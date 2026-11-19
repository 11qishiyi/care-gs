"""Load a scene from the released 3DGS output archive itself.

The archive ships ``test/ours_40000/gt/*.png`` — the ground-truth images of the
held-out views, in the order 3DGS used when rendering them.  Together with
``cameras.json`` this gives a complete, self-consistent scene without needing the
original dataset download, which lets us scale to the four scenes present in the
archive (bicycle, flowers, stump, treehill).

The 3DGS convention is ``idx % llffhold == 0 -> test`` over the *scene camera
order*, so ``test/....../gt/{j:05d}.png`` corresponds to the j-th camera whose
index is a multiple of ``llffhold``.  That mapping is verified empirically by
:func:`verify_mapping` before any experiment uses it.
"""
from __future__ import annotations

import json
import os

import numpy as np


def _load_cams(cameras_json: str) -> list:
    cams = json.load(open(cameras_json, encoding="utf-8"))
    out = []
    for c in cams:
        R = np.asarray(c["rotation"], dtype=np.float64)
        c2w = np.eye(4)
        c2w[:3, :3] = R
        c2w[:3, 3] = np.asarray(c["position"], dtype=np.float64)
        K = np.array([[c["fx"], 0.0, c["width"] / 2.0],
                      [0.0, c["fy"], c["height"] / 2.0],
                      [0.0, 0.0, 1.0]], dtype=np.float64)
        out.append(dict(id=int(c.get("id", len(out))), img_name=c["img_name"],
                        width=int(c["width"]), height=int(c["height"]), c2w=c2w, K=K))
    return out


def load_archive_scene(archive_root: str, scene: str, factor: int = 4,
                       llffhold: int = 8, which: str = "test",
                       cam_root: str | None = None):
    """Return cameras/Ks/image paths for the held-out (test) views of a scene.

    ``archive_root`` contains ``output/<scene>/cameras.json`` and
    ``output/<scene>/test/ours_40000/gt/``.
    """
    base = os.path.join(archive_root, "output", scene)
    cam_base = os.path.join(cam_root or archive_root, "output", scene)
    cams = _load_cams(os.path.join(cam_base, "cameras.json"))
    # NOTE: cameras.json is written in the *training order* (id order), which is a
    # COLMAP insertion order and NOT sorted by image name.  Sorting by name breaks
    # the ``test j -> camera 8j`` mapping (verified: PSNR drops 20.4 -> 12.2 dB).
    cams.sort(key=lambda c: c["id"])

    if which == "test":
        sel = [i for i in range(len(cams)) if i % llffhold == 0]
        img_dir = os.path.join(base, "test", "ours_40000", "gt")
    else:
        sel = [i for i in range(len(cams)) if i % llffhold != 0]
        img_dir = os.path.join(base, "train", "ours_40000", "gt")
    paths = []
    for j, _ in enumerate(sel):
        p = os.path.join(img_dir, f"{j:05d}.png")
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        paths.append(p)

    picked = [cams[i] for i in sel]
    c2w = np.stack([c["c2w"] for c in picked]).astype(np.float32)
    K = np.stack([c["K"] for c in picked]).astype(np.float32)
    K[:, 0, :] /= factor
    K[:, 1, :] /= factor
    W = int(round(picked[0]["width"] / factor))
    H = int(round(picked[0]["height"] / factor))
    return dict(camtoworlds=c2w, Ks=K, image_paths=paths, width=W, height=H,
                names=[c["img_name"] for c in picked],
                cam_index=np.asarray(sel), factor=factor)


def split_chrono(n: int, cal_frac: float = 0.35, train_frac: float = 0.0):
    """Chronological split over the held-out views (they are in capture order)."""
    idx = np.arange(n)
    n_cal = int(round(cal_frac * n))
    cal = idx[:n_cal]
    dep = idx[n_cal:]
    return dict(train_idx=np.array([], dtype=int), cal_idx=cal, dep_idx=dep)


def load_images_streaming(paths, size, verbose: bool = False):
    """Decode + downscale one image at a time (GT PNGs are ~50 MB each)."""
    from PIL import Image
    out = []
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        if (im.width, im.height) != tuple(size):
            im = im.resize(size, Image.LANCZOS)
        out.append(np.asarray(im))
        if verbose and i % 10 == 0:
            print(f"  img {i+1}/{len(paths)}", flush=True)
    return np.stack(out, 0)
