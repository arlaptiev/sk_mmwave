import os
import numpy as np
import matplotlib.pyplot as plt

# ARKit LiDAR depthMap is 256×192 (width×height)
W, H = 256, 192  

bin_path = "captures/2025-05-08_14-52-20.647/depth.bin" #path to depth file

depth = np.fromfile(bin_path, dtype=np.float32) #Load float32 array
depth = depth.reshape((H, W)) #reshape to (H, W)

output_dir = "depth_maps"
os.makedirs(output_dir, exist_ok=True)

#Plot and save the figure
plt.figure(figsize=(6, 5))
plt.title("LiDAR Depth (meters)")
plt.imshow(depth, cmap="viridis", origin="upper")
plt.colorbar(label="Distance (m)")

# Derive output filename
stem = os.path.splitext(os.path.basename(bin_path))[0]
output_path = os.path.join(output_dir, f"{stem}.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Saved depth map image to: {output_path}")

