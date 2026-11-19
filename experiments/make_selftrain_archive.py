"""Turn a self-trained 3DGS checkpoint on a BungeeNeRF scene into an archive-contract entry.

Why this exists: to test the certificate on assets outside the four released checkpoints we
train 3DGS ourselves, but the audit protocol (`calib.archive_only.load_archive_only_scene`)
expects the released-archive layout.  This script writes that layout from a COLMAP scene plus
the trained PLY:

    <archive>/output/<name>/cameras.json                 full-resolution cameras, sorted by name
    <archive>/output/<name>/test/ours_40000/gt/%05d.png  every 8th view, at 1/factor resolution
    <archive>/output/<name>/point_cloud/iteration_40000/point_cloud.ply   (link to the trained PLY)

Leakage discipline: the trainer is run with `--split interleaved`, i.e. it optimises only the
views with `i % 8 != 0`.  The views written here as ground truth are exactly the `i % 8 == 0`
ones, so the certificate's calibration/deployment split never sees an optimised view
(Appendix D of the paper).

Usage:
    python experiments/make_selftrain_archive.py --scene-dir /data/bungeenerf/bungeenerf/bilbao \
        --ply /workspace/data/selftrain/bilbao/point_cloud.ply \
        --archive /workspace/data/selftrain_archive --name bilbao_selftrain --factor 4
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
    ap.add_argument("--scene-dir", required=True, help="COLMAP scene root (has sparse/ and images/)")
    ap.add_argument("--ply", required=True, help="trained point_cloud.ply")
    ap.add_argument("--archive", default="/workspace/data/selftrain_archive")
    ap.add_argument("--name", required=True)
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--holdout", type=int, default=8)
    args = ap.parse_args()

    sc = load_colmap_scene(args.scene_dir, factor=1, split="interleaved",
                           test_every=args.holdout)
    c2w = np.asarray(sc["camtoworlds"])
    Ks = np.asarray(sc["Ks"])
    paths = list(sc["image_paths"])
    W, H = int(sc["width"]), int(sc["height"])
    n = len(paths)
    print(f"{n} views, {W}x{H} (full res), train={len(sc['train_idx'])}, "
          f"test={len(sc['cal_idx'])}")

    base = os.path.join(args.archive, "output", args.name)
    gt_dir = os.path.join(base, "test", "ours_40000", "gt")
    ply_dir = os.path.join(base, "point_cloud", "iteration_40000")
    os.makedirs(gt_dir, exist_ok=True)
    os.makedirs(ply_dir, exist_ok=True)

    cams = []
    kept = 0
    for i, p in enumerate(paths):
        name = os.path.basename(p)
        cams.append(dict(img_name=name, width=W, height=H,
                         position=np.asarray(c2w[i][:3, 3]).tolist(),
                         rotation=np.asarray(c2w[i][:3, :3]).tolist(),
                         fx=float(Ks[i][0, 0]), fy=float(Ks[i][1, 1])))
    # cameras.json is what the loader sorts; write it in name order and use the same order for GT
    order = sorted(range(n), key=lambda i: cams[i]["img_name"])
    cams = [cams[i] for i in order]
    paths = [paths[i] for i in order]
    json.dump(cams, open(os.path.join(base, "cameras.json"), "w", encoding="utf-8"), indent=1)

    tw, th = max(1, round(W / args.factor)), max(1, round(H / args.factor))
    for j, i in enumerate(range(n)):
        if i % args.holdout:
            continue
        im = Image.open(paths[i]).convert("RGB").resize((tw, th), Image.BILINEAR)
        im.save(os.path.join(gt_dir, f"{kept:05d}.png"))
        kept += 1
    print(f"wrote cameras.json ({n}) and {kept} ground-truth views at {tw}x{th}")

    dst_ply = os.path.join(ply_dir, "point_cloud.ply")
    try:
        os.link(args.ply, dst_ply)
    except OSError:
        shutil.copyfile(args.ply, dst_ply)
    print(f"ply {os.path.getsize(dst_ply)/1e6:.0f} MB -> {dst_ply}")
    print("SELFTRAIN_ARCHIVE_OK")


if __name__ == "__main__":
    main()
