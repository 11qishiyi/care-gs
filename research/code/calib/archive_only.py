"""Scene loader for scenes available ONLY inside the 3DGS output archive.

Verified on flowers: ``test/ours_40000/gt/{j:05d}.png`` is the j-th camera among
``{i : i % 8 == 0}`` when cameras are sorted by image name (correlation 1.000 for
all 22 test images against the original dataset images).  This lets us build a
complete scene -- cameras, intrinsics, ground-truth images -- from the archive
alone, for any scene it ships (bicycle, stump, treehill, flowers).
"""
from __future__ import annotations

import json
import os

import numpy as np


def load_archive_only_scene(archive_root: str, scene: str, factor: int = 4,
                            llffhold: int = 8, cal_frac: float = 0.5):
    base = os.path.join(archive_root, "output", scene)
    cams = json.load(open(os.path.join(base, "cameras.json"), encoding="utf-8"))
    cams.sort(key=lambda c: c["img_name"])

    sel = [i for i in range(len(cams)) if i % llffhold == 0]
    gt_dir = os.path.join(base, "test", "ours_40000", "gt")
    gt_files = sorted(os.listdir(gt_dir))
    if len(gt_files) != len(sel):
        print(f"[warn] {len(gt_files)} gt files vs {len(sel)} test cameras")
    n = min(len(sel), len(gt_files))
    picked = [cams[i] for i in sel[:n]]
    paths = [os.path.join(gt_dir, gt_files[j]) for j in range(n)]

    c2w = np.stack([np.array([[  # build 4x4 from rotation + position
        0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 1]], dtype=np.float64)
        for _ in picked])
    for k, c in enumerate(picked):
        R = np.asarray(c["rotation"], dtype=np.float64)
        c2w[k, :3, :3] = R
        c2w[k, :3, 3] = np.asarray(c["position"], dtype=np.float64)

    W = int(round(picked[0]["width"] / factor))
    H = int(round(picked[0]["height"] / factor))
    Ks = np.zeros((n, 3, 3), dtype=np.float64)
    for k, c in enumerate(picked):
        Ks[k] = np.array([[c["fx"] / factor, 0, W / 2.0],
                          [0, c["fy"] / factor, H / 2.0],
                          [0, 0, 1]], dtype=np.float64)

    idx = np.arange(n)
    n_cal = max(2, int(round(cal_frac * n)))
    return dict(camtoworlds=c2w.astype(np.float32), Ks=Ks.astype(np.float32),
                image_paths=paths, width=W, height=H,
                train_idx=idx[:0], cal_idx=idx[:n_cal], dep_idx=idx[n_cal:],
                names=[c["img_name"] for c in picked])
