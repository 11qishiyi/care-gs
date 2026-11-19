"""Load a scene from an INRIA-3DGS training output directory (cameras.json + PLY).

The released 3DGS outputs provide ``cameras.json`` with the *camera-to-world*
rotation and centre plus focal lengths, so no COLMAP parsing is needed and the
convention is guaranteed to match the checkpoint (which is exactly what we want:
the calibration study must not be polluted by a pose-convention bug).
"""
from __future__ import annotations

import json
import os

import numpy as np


def load_3dgs_cameras(cameras_json: str) -> list:
    cams = json.load(open(cameras_json, encoding="utf-8"))
    out = []
    for c in cams:
        R = np.asarray(c["rotation"], dtype=np.float64)          # camera-to-world rotation
        C = np.asarray(c["position"], dtype=np.float64)          # camera centre in world
        c2w = np.eye(4)
        c2w[:3, :3] = R
        c2w[:3, 3] = C
        K = np.array([[c["fx"], 0.0, c["width"] / 2.0],
                      [0.0, c["fy"], c["height"] / 2.0],
                      [0.0, 0.0, 1.0]], dtype=np.float64)
        out.append(dict(img_name=c["img_name"], width=int(c["width"]), height=int(c["height"]),
                        c2w=c2w, K=K))
    out.sort(key=lambda d: d["img_name"])
    return out


def build_image_index(image_dir: str) -> dict:
    idx = {}
    if not os.path.isdir(image_dir):
        return idx
    for f in os.listdir(image_dir):
        stem, _ = os.path.splitext(f)
        idx.setdefault(stem, os.path.join(image_dir, f))
    return idx


def load_scene_from_3dgs(cameras_json: str, dataset_dir: str, factor: int = 2,
                         split: str = "chrono", cal_frac: float = 0.15,
                         train_frac: float = 0.65):
    """Return cameras, Ks, image paths and the train/cal/deploy split."""
    cams = load_3dgs_cameras(cameras_json)
    sub = "images" if factor == 1 else f"images_{factor}"
    img_dir = os.path.join(dataset_dir, sub)
    if not os.path.isdir(img_dir):
        img_dir = os.path.join(dataset_dir, "images")
    index = build_image_index(img_dir)

    for c in cams:
        c["stem"] = os.path.splitext(c["img_name"])[0]
    kept = [c for c in cams if c["stem"] in index]
    if len(kept) < len(cams):
        print(f"[scene] {len(cams) - len(kept)} cameras have no image in {img_dir}")
    c2w = np.stack([c["c2w"] for c in kept]).astype(np.float32)
    K = np.stack([c["K"] for c in kept]).astype(np.float32) * np.array(
        [[1, 1, 1], [1, 1, 1], [1, 1, 1]], dtype=np.float32)
    K[:, 0, :] /= factor
    K[:, 1, :] /= factor
    W = int(round(kept[0]["width"] / factor))
    H = int(round(kept[0]["height"] / factor))
    paths = [index[c["stem"]] for c in kept]

    n = len(paths)
    idx = np.arange(n)
    if split == "chrono":
        n_tr = int(round(train_frac * n))
        n_cal = int(round(cal_frac * n))
        train = idx[:n_tr]
        cal = idx[n_tr:n_tr + n_cal]
        dep = idx[n_tr + n_cal:]
    else:
        test = idx[idx % 8 == 0]
        train = idx[idx % 8 != 0]
        half = len(test) // 2
        cal, dep = test[:half], test[half:]
    return dict(camtoworlds=c2w, Ks=K, image_paths=paths, width=W, height=H,
                train_idx=train, cal_idx=cal, dep_idx=dep,
                names=[c["img_name"] for c in kept])


def load_exposure(exposure_json: str) -> dict:
    if not os.path.isfile(exposure_json):
        return {}
    d = json.load(open(exposure_json, encoding="utf-8"))
    return d
