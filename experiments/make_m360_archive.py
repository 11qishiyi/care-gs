"""Write an archive-contract entry for a self-trained Mip-NeRF 360 3DGS model.

Same contract as `make_selftrain_archive.py`, with one difference that matters here: the images
on disk are already the published protocol resolution (`images_4`), so the cameras are loaded at
that factor and the ground-truth views are written at exactly the resolution the model renders.

    <archive>/output/<name>/cameras.json                 cameras at 1/factor, sorted by name
    <archive>/output/<name>/test/ours_40000/gt/%05d.png  every `holdout`-th view
    <archive>/output/<name>/point_cloud/iteration_40000/point_cloud.ply   link to the trained PLY

Leakage discipline: the trainer runs with `--split interleaved`, so views with `i % holdout == 0`
are never optimised; they are exactly the ones written here as ground truth.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))
from calib.colmap_io import load_colmap_scene  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene-dir", required=True, help="COLMAP root holding sparse/0 and images_4")
    ap.add_argument("--ply", required=True)
    ap.add_argument("--archive", default="/workspace/data/m360std")
    ap.add_argument("--name", required=True)
    ap.add_argument("--factor", type=int, default=4, help="images on disk are 1/factor of full res")
    ap.add_argument("--holdout", type=int, default=8)
    args = ap.parse_args()

    sc = load_colmap_scene(args.scene_dir, factor=args.factor, split="interleaved",
                           test_every=args.holdout, filter_views=False)
    c2w = np.asarray(sc["camtoworlds"])
    Ks = np.asarray(sc["Ks"])
    paths = list(sc["image_paths"])
    W, H = int(sc["width"]), int(sc["height"])
    n = len(paths)
    print(f"{n} views, {W}x{H} at 1/{args.factor}, train={len(sc['train_idx'])}, "
          f"held out={len(sc['cal_idx'])}", flush=True)

    base = os.path.join(args.archive, "output", args.name)
    gt_dir = os.path.join(base, "test", "ours_40000", "gt")
    ply_dir = os.path.join(base, "point_cloud", "iteration_40000")
    os.makedirs(gt_dir, exist_ok=True)
    os.makedirs(ply_dir, exist_ok=True)

    cams = []
    for i, p in enumerate(paths):
        cams.append(dict(img_name=os.path.basename(p), width=W, height=H,
                         position=np.asarray(c2w[i][:3, 3]).tolist(),
                         rotation=np.asarray(c2w[i][:3, :3]).tolist(),
                         fx=float(Ks[i][0, 0]), fy=float(Ks[i][1, 1])))
    order = sorted(range(n), key=lambda i: cams[i]["img_name"])
    cams = [cams[i] for i in order]
    paths = [paths[i] for i in order]
    json.dump(cams, open(os.path.join(base, "cameras.json"), "w", encoding="utf-8"), indent=1)

    kept = 0
    for i in range(n):
        if i % args.holdout:
            continue
        im = Image.open(paths[i]).convert("RGB")
        if im.size != (W, H):
            im = im.resize((W, H), Image.BILINEAR)
        im.save(os.path.join(gt_dir, f"{kept:05d}.png"))
        kept += 1
    dst_ply = os.path.join(ply_dir, "point_cloud.ply")
    if os.path.exists(dst_ply):
        os.remove(dst_ply)
    try:
        os.link(args.ply, dst_ply)
    except OSError:
        shutil.copyfile(args.ply, dst_ply)
    print(f"wrote cameras.json ({n}), {kept} ground-truth views at {W}x{H}, "
          f"ply {os.path.getsize(dst_ply) / 1e6:.0f} MB", flush=True)
    print("M360_ARCHIVE_OK", flush=True)


if __name__ == "__main__":
    main()
