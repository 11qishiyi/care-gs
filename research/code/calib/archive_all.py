"""Scene loader that uses ALL views available in the 3DGS output archive.

The archive ships ground-truth renders for both splits:

    train/ours_40000/gt/{j:05d}.png   j = index among *training* cameras (name order)
    test /ours_40000/gt/{j:05d}.png   j = index among *test*    cameras (name order)

With ``llffhold = 8`` the test cameras are those with ``i % 8 == 0`` in name order, so
every camera maps to exactly one GT image.  Verified on flowers: 173 cameras =
151 train + 22 test, which matches the file counts exactly.

Using all views roughly multiplies the number of evaluation views by an order of
magnitude, which is what the coverage confidence intervals need: the effective
sample size for a coverage claim is the number of *views*, not pixels.
"""
from __future__ import annotations

import json
import os

import numpy as np


def load_archive_all_scene(archive_root: str, scene: str, factor: int = 4,
                           llffhold: int = 8, cal_frac: float = 0.5):
    base = os.path.join(archive_root, "output", scene)
    cams = json.load(open(os.path.join(base, "cameras.json"), encoding="utf-8"))
    cams.sort(key=lambda c: c["img_name"])

    test_dir = os.path.join(base, "test", "ours_40000", "gt")
    train_dir = os.path.join(base, "train", "ours_40000", "gt")
    test_files = sorted(os.listdir(test_dir)) if os.path.isdir(test_dir) else []
    train_files = sorted(os.listdir(train_dir)) if os.path.isdir(train_dir) else []

    paths, picked = [], []
    tid = 0
    for i, c in enumerate(cams):
        is_test = (i % llffhold == 0)
        if is_test:
            if tid >= len(test_files):
                continue
            paths.append(os.path.join(test_dir, test_files[tid]))
            tid += 1
        else:
            k = i - (i // llffhold + 1)          # index among training cameras
            if k < 0 or k >= len(train_files):
                continue
            paths.append(os.path.join(train_dir, train_files[k]))
        picked.append(c)

    n = len(picked)
    c2w = np.zeros((n, 4, 4), dtype=np.float64)
    for k, c in enumerate(picked):
        c2w[k, :3, :3] = np.asarray(c["rotation"], dtype=np.float64)
        c2w[k, :3, 3] = np.asarray(c["position"], dtype=np.float64)
        c2w[k, 3, 3] = 1.0

    W = int(round(picked[0]["width"] / factor))
    H = int(round(picked[0]["height"] / factor))
    Ks = np.zeros((n, 3, 3), dtype=np.float64)
    for k, c in enumerate(picked):
        Ks[k] = [[c["fx"] / factor, 0, W / 2.0],
                 [0, c["fy"] / factor, H / 2.0],
                 [0, 0, 1]]

    idx = np.arange(n)
    n_cal = max(2, int(round(cal_frac * n)))
    # interleaved calibration/deployment split (see report section 3.4: a block
    # split breaks exchangeability and makes the certificate falsely conservative)
    cal = idx[0::2][: n_cal]
    dep = idx[1::2]
    return dict(camtoworlds=c2w.astype(np.float32), Ks=Ks.astype(np.float32),
                image_paths=paths, width=W, height=H,
                train_idx=idx[:0], cal_idx=cal, dep_idx=dep,
                names=[c["img_name"] for c in picked])
