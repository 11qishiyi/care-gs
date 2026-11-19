# -*- coding: utf-8 -*-
"""Verify the all-views mapping before using it in the audit."""
import io
io.open(r"D:\3dsg_1\research\code\scripts\verify_allviews.py", "w", encoding="utf-8").write('''"""Verify the all-views (train+test) camera mapping by rendering a few views."""
import sys
sys.path.insert(0, "/workspace/code")
import numpy as np, torch
from calib.archive_all import load_archive_all_scene
from calib.gsrender import load_splats, render
from calib.colmap_io import load_images, normalize_exposure

ARCH = "/workspace/data/out3dgs"
for scene in ["flowers", "bicycle", "stump"]:
    sc = load_archive_all_scene(ARCH, scene, factor=4)
    W, H = sc["width"], sc["height"]
    gt = torch.from_numpy(normalize_exposure(load_images(sc["image_paths"], 4, (W, H)))).float().cuda()
    c2w = torch.from_numpy(sc["camtoworlds"]).cuda(); K = torch.from_numpy(sc["Ks"]).cuda()
    ply = f"{ARCH}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply"
    sp = load_splats(ply)
    n = len(sc["image_paths"])
    probe = [0, 1, n//3, n//2, n-1]
    it = torch.as_tensor(probe, device="cuda")
    out = render(sp, c2w[it], K[it], W, H)
    ps = []
    for j, vi in enumerate(probe):
        rgb = out["colors"][j]
        g = gt[vi].cuda()
        mse = float(((rgb - g) ** 2).mean())
        ps.append(10 * np.log10(1.0 / max(mse, 1e-12)))
    print(f"{scene:9s} views={n:4d} probe PSNR = " + " ".join(f"{v:.1f}" for v in ps)
          + f"  mean={np.mean(ps):.2f}")
''')
print("wrote verify_allviews.py")
