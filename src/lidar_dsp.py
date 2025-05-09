import cv2
import numpy as np

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

    # refine with all inliers
    pts = points_3d[best_inliers]
    C = pts.mean(axis=0)
    _, _, V = np.linalg.svd(pts - C)
    n = V[-1] / np.linalg.norm(V[-1])
    d = -n.dot(C)
    return n, d

def detect_planes_and_box(cv2_image, depth_map, meta):
    fx, fy, cx, cy = meta['intrinsics'][0][0], meta['intrinsics'][1][1], meta['intrinsics'][2][0], meta['intrinsics'][2][1]
    Hc, Wc = cv2_image.shape[:2]
    Hd, Wd = depth_map.shape

    # Resize depth to match image resolution
    depth_full = cv2.resize(depth_map, (Wc, Hc), interpolation=cv2.INTER_NEAREST)

    ys, xs = np.indices((Hc, Wc))
    Z = depth_full.flatten()
    valid = Z > 0
    X = (xs.flatten()[valid] - cx) * Z[valid] / fx
    Y = (ys.flatten()[valid] - cy) * Z[valid] / fy
    pts3d = np.stack([X, Y, Z[valid]], axis=1)
    idx_flat = np.where(valid)[0]

    # Subsample for RANSAC
    M = pts3d.shape[0]
    sample = pts3d[np.random.choice(M, min(M, 20000), replace=False)]

    n1, d1 = fit_plane_ransac(sample, threshold=0.02, iters=200)
    dist1 = abs(d1)
    df = np.abs(pts3d.dot(n1) + d1)
    mask1 = np.zeros(Hc * Wc, bool)
    mask1[idx_flat[df < 0.02]] = True
    mask1 = mask1.reshape(Hc, Wc)

    nf = pts3d[df >= 0.02]
    idx_nf = idx_flat[df >= 0.02]
    sample2 = nf[np.random.choice(nf.shape[0], min(nf.shape[0], 20000), replace=False)]
    n2, d2 = fit_plane_ransac(sample2, threshold=0.02, iters=200)
    dist2 = abs(d2)
    dt = np.abs(pts3d.dot(n2) + d2)
    mask2 = np.zeros(Hc * Wc, bool)
    mask2[idx_flat[dt < 0.02]] = True
    mask2 = mask2.reshape(Hc, Wc)

    if dist1 < dist2:
        n1, n2 = n2, n1
        d1, d2 = d2, d1
        dist1, dist2 = dist2, dist1
        mask1, mask2 = mask2, mask1

    floor_mask, table_mask = mask1, mask2
    floor_dist, table_dist = dist1, dist2

    valid2d = valid.reshape(Hc, Wc)
    remain = valid2d & ~floor_mask & ~table_mask
    ys_r, xs_r = np.where(remain)
    Zr = depth_full[ys_r, xs_r]
    if Zr.size == 0:
        box_dist = float('nan')
    else:
        i_min = np.argmin(Zr)
        vb, ub = int(ys_r[i_min]), int(xs_r[i_min])
        Zb = float(Zr[i_min])
        Xb = (ub - cx) * Zb / fx
        Yb = (vb - cy) * Zb / fy
        box_dist = np.sqrt(Xb ** 2 + Yb ** 2 + Zb ** 2)

    return floor_dist, box_dist, table_dist
