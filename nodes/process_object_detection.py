import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os


# RANSAC plane fitting
def fit_plane_ransac(points_3d, threshold=0.02, iters=1000):
    best_inliers, best_n, best_d = [], None, None
    N = points_3d.shape[0]
    for _ in range(iters):
        i1, i2, i3 = np.random.choice(N, 3, replace=False)
        P1, P2, P3 = points_3d[[i1, i2, i3]]
        n = np.cross(P2 - P1, P3 - P1)
        if np.linalg.norm(n) < 1e-6:
            continue
        n /= np.linalg.norm(n)
        d = -n.dot(P1)
        dist = np.abs(points_3d.dot(n) + d)
        inliers = np.where(dist < threshold)[0]
        if inliers.size > len(best_inliers):
            best_inliers, best_n, best_d = inliers, n, d

    if best_n is None:
        raise RuntimeError("RANSAC failed")

    # refine on all inliers
    pts = points_3d[best_inliers]
    C = pts.mean(axis=0)
    _, _, V = np.linalg.svd(pts - C)
    n = V[-1] / np.linalg.norm(V[-1])
    d = -n.dot(C)
    return n, d

def load_intrinsics(path):
    K = json.load(open(path))['intrinsics']
    return K[0][0], K[1][1], K[2][0], K[2][1]

def load_depth_bin(path, shape):
    d = np.fromfile(path, np.float32)
    if d.size != shape[0] * shape[1]:
        raise ValueError("depth size mismatch")
    return d.reshape(shape)

if __name__ == "__main__":
    IMG, DEP, META = "captures/2025-05-09_15-59-08.112/frame.jpg", "captures/2025-05-09_15-59-08.112/depth.bin", "captures/2025-05-09_15-59-08.112/meta.json"
    Hd, Wd = 192, 256

    img = cv2.imread(IMG)
    Hc, Wc = img.shape[:2]
    fx, fy, cx, cy = load_intrinsics(META)
    depth = load_depth_bin(DEP, (Hd, Wd))
    depth_full = cv2.resize(depth, (Wc, Hc), interpolation=cv2.INTER_NEAREST)

    # Build 3D cloud
    ys, xs = np.indices((Hc, Wc))
    Z = depth_full.flatten()
    valid = Z > 0
    X = (xs.flatten()[valid] - cx) * Z[valid] / fx
    Y = (ys.flatten()[valid] - cy) * Z[valid] / fy
    pts3d = np.stack([X, Y, Z[valid]], axis=1)
    idx_flat = np.where(valid)[0]

    # Subsample for speed
    M = pts3d.shape[0]
    sample = pts3d[np.random.choice(M, min(M, 20000), replace=False)]

    # Fit first plane (candidate)
    n1, d1 = fit_plane_ransac(sample, threshold=0.02, iters=200)
    dist1 = abs(d1)
    df = np.abs(pts3d.dot(n1) + d1)
    mask1 = np.zeros(Hc*Wc, bool)
    mask1[idx_flat[df < 0.02]] = True
    mask1 = mask1.reshape(Hc, Wc)

    # Fit second plane on the remaining points
    nf = pts3d[df >= 0.02]
    idx_nf = idx_flat[df >= 0.02]
    sample2 = nf[np.random.choice(nf.shape[0], min(nf.shape[0], 20000), replace=False)]
    n2, d2 = fit_plane_ransac(sample2, threshold=0.02, iters=200)
    dist2 = abs(d2)
    dt = np.abs(pts3d.dot(n2) + d2)
    mask2 = np.zeros(Hc*Wc, bool)
    mask2[idx_flat[dt < 0.02]] = True
    mask2 = mask2.reshape(Hc, Wc)

    # Ensure plane “1” is the floor (farther from camera) and plane “2” is the table
    if dist1 < dist2:
        # swap everything
        n1, n2 = n2, n1
        d1, d2 = d2, d1
        dist1, dist2 = dist2, dist1
        mask1, mask2 = mask2, mask1

    # Now mask1 → floor, mask2 → table
    floor_mask, table_mask = mask1, mask2
    floor_dist, table_dist = dist1, dist2

    # Find box as the closest remaining point
    valid2d = valid.reshape(Hc, Wc)
    remain = valid2d & ~floor_mask & ~table_mask
    ys_r, xs_r = np.where(remain)
    Zr = depth_full[ys_r, xs_r]
    i_min = np.argmin(Zr)
    vb, ub = int(ys_r[i_min]), int(xs_r[i_min])
    Zb = float(Zr[i_min])
    Xb = (ub - cx) * Zb / fx
    Yb = (vb - cy) * Zb / fy
    box_dist = np.sqrt(Xb**2 + Yb**2 + Zb**2)

    # Annotate
    out = img.copy()
    ov = np.zeros_like(out, np.uint8)

    # Floor → blue overlay
    ov[..., 0] = 255
    bg = cv2.addWeighted(out, 0.7, ov, 0.3, 0)
    out[floor_mask] = bg[floor_mask]

    # Table → red overlay
    ov[:] = 0; ov[..., 2] = 255
    bg = cv2.addWeighted(out, 0.7, ov, 0.3, 0)
    out[table_mask] = bg[table_mask]

    # Box → green dot
    cv2.circle(out, (ub, vb), 10, (0, 255, 0), -1)

    # Text labels (now correct)
    cv2.putText(out, f"Floor: {floor_dist:.2f} m", (20, Hc - 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
    cv2.putText(out, f"Table: {table_dist:.2f} m", (20, Hc - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
    cv2.putText(out, f"Box: {box_dist:.2f} m", (ub + 15, vb - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    # Save to plane_detection folder 
    out_dir = "pbject_detection_results"
    os.makedirs(out_dir, exist_ok=True)
    save_path = os.path.join(out_dir, "detection_result.png")
    cv2.imwrite(save_path, out)
    print(f"Saved annotated image to {save_path}")
    
    # # Show
    # plt.figure(figsize=(10, 6))
    # plt.imshow(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
    # plt.axis('off')
    # plt.show()

    #print out the measured distances
    print(f"Floor distance: {floor_dist:.2f} m")
    print(f"Table distance: {table_dist:.2f} m")
    print(f"Box distance: {box_dist:.2f} m")

    

