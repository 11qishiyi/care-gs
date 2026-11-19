# -*- coding: utf-8 -*-
"""Exposure normalisation: remove per-image auto-exposure so the model fits scene content."""
import io

# 1) colmap_io: add normalised loader
p = r"D:\3dsg_1\research\code\calib\colmap_io.py"
s = io.open(p, encoding="utf-8").read()
if "def normalize_exposure" not in s:
    s += '''

def normalize_exposure(imgs: np.ndarray, target: float = 0.40) -> np.ndarray:
    """Scale each image so its mean intensity equals ``target``.

    Mip-NeRF 360 captures are auto-exposed: per-image brightness varies by up to
    ~2.3x, which a shared radiance field cannot represent.  Normalising removes
    that nuisance *deterministically*, so training, calibration and deployment
    all see the same transform (no per-view parameters to leak information).
    """
    out = imgs.astype(np.float32) / 255.0
    m = out.reshape(out.shape[0], -1).mean(axis=1).clip(1e-3, None)
    out = out * (target / m)[:, None, None, None]
    return np.clip(out, 0.0, 1.0)
'''
io.open(p, "w", encoding="utf-8").write(s)
print("patched colmap_io")

# 2) train_gs: use normalised images, report PSNR in normalised space
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
    "from calib.colmap_io import load_colmap_scene, load_images, read_points3D_bin",
    "from calib.colmap_io import load_colmap_scene, load_images, read_points3D_bin, normalize_exposure")
s = s.replace(
    "    gt = torch.from_numpy(imgs).float() / 255.0                     # (N,H,W,3) stays on CPU",
    "    gt_np = normalize_exposure(imgs)\n"
    "    gt = torch.from_numpy(gt_np).float()                            # (N,H,W,3) on CPU")
io.open(p, "w", encoding="utf-8").write(s)
print("patched train_gs")

# 3) run_scene: same normalisation
p = r"D:\3dsg_1\research\code\scripts\run_scene.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
    "from calib.colmap_io import load_colmap_scene, load_images",
    "from calib.colmap_io import load_colmap_scene, load_images, normalize_exposure")
s = s.replace(
    '    gt = torch.from_numpy(load_images(scene["image_paths"], args.factor, (W, H))).float() / 255.0',
    '    gt = torch.from_numpy(normalize_exposure(\n'
    '        load_images(scene["image_paths"], args.factor, (W, H)))).float()')
io.open(p, "w", encoding="utf-8").write(s)
print("patched run_scene")
