"""Build archive entries for the BungeeNeRF/amsterdam scene (a second dataset).

The 3DGS output archive (`Jackie137/3dgs-Output`) ships `output/bungeenerf/amsterdam`
with 161 cameras and two checkpoints (iteration_20000 and iteration_50000) but **no
ground-truth images**; the capture comes from the separate `Jackie137/BungeeNeRF`
ModelScope dataset (bungeenerf.tar.gz).  This script stitches the two into the layout
`calib.archive_only` expects, for two "scene" names so that the depth comparison can
also be run on the second dataset:

    <ARCH>/output/amsterdam_20k/{cameras.json,point_cloud/iteration_40000/point_cloud.ply,
                                 test/ours_40000/gt/%05d.png}
    <ARCH>/output/amsterdam_50k/...   (same cameras and GT, the 50k checkpoint)

Ground truth is copied in *sorted camera order, every 8th camera* (llffhold=8), the same
convention as the Mip-NeRF 360 entries, so `load_archive_only_scene` matches the two.

Usage (on the node, after extracting bungeenerf.tar.gz somewhere):
    python experiments/prep_bungee.py --archive /workspace/data/out3dgs \
        --bungee-root /data/bungeenerf --out-scenes amsterdam_20k,amsterdam_50k
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

LLFFHOLD = 8
IMAGE_EXT = (".jpeg", ".jpg", ".png", ".JPG", ".JPEG", ".PNG")


def find_scene_dir(root: str, scene: str) -> str:
    """Locate the directory that holds the capture, tolerating layout differences."""
    cands = []
    for dp, dn, fn in os.walk(root):
        if any(f.lower().endswith(IMAGE_EXT) for f in fn):
            cands.append(dp)
    # prefer a path that mentions the scene name, else the largest directory
    named = [c for c in cands if scene in c.lower()]
    pool = named or cands
    if not pool:
        raise SystemExit(f"no images under {root}")
    return max(pool, key=lambda d: len(os.listdir(d)))


def index_images(d: str) -> dict:
    out = {}
    for f in os.listdir(d):
        stem, ext = os.path.splitext(f)
        if ext in IMAGE_EXT:
            out.setdefault(stem.lower(), os.path.join(d, f))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--bungee-root", default="/data/bungeenerf")
    ap.add_argument("--src-scene", default="bungeenerf/amsterdam")
    ap.add_argument("--out-scenes", default="amsterdam_20k,amsterdam_50k")
    ap.add_argument("--iters", default="iteration_20000,iteration_50000")
    args = ap.parse_args()

    src = os.path.join(args.archive, "output", args.src_scene)
    cams = json.load(open(os.path.join(src, "cameras.json"), encoding="utf-8"))
    cams.sort(key=lambda c: c["img_name"])
    sel = [cams[i] for i in range(len(cams)) if i % LLFFHOLD == 0]
    print(f"cameras={len(cams)} held-out={len(sel)} first={sel[0]['img_name']} "
          f"{sel[0]['width']}x{sel[0]['height']}")

    img_dir = find_scene_dir(args.bungee_root, "amsterdam")
    imgs = index_images(img_dir)
    print(f"images: {len(imgs)} under {img_dir}")

    matched, missing = [], []
    for c in sel:
        stem = os.path.splitext(os.path.basename(c["img_name"]))[0].lower()
        p = imgs.get(stem)
        (matched if p else missing).append((c, p))
    print(f"matched={len(matched)} missing={len(missing)}")
    if missing[:3]:
        print("  missing e.g.", [c["img_name"] for c, _ in missing[:3]])
    if not matched:
        raise SystemExit("no matched ground truth")

    names = [s.strip() for s in args.out_scenes.split(",") if s.strip()]
    iters = [s.strip() for s in args.iters.split(",") if s.strip()]
    for scene, it in zip(names, iters):
        base = os.path.join(args.archive, "output", scene)
        gt_dir = os.path.join(base, "test", "ours_40000", "gt")
        ply_dir = os.path.join(base, "point_cloud", "iteration_40000")
        os.makedirs(gt_dir, exist_ok=True)
        os.makedirs(ply_dir, exist_ok=True)
        for j, (_c, p) in enumerate(matched):
            shutil.copyfile(p, os.path.join(gt_dir, f"{j:05d}.png"))
        shutil.copyfile(os.path.join(src, "cameras.json"), os.path.join(base, "cameras.json"))
        src_ply = os.path.join(src, "point_cloud", it, "point_cloud.ply")
        dst_ply = os.path.join(ply_dir, "point_cloud.ply")
        try:
            os.link(src_ply, dst_ply)
        except OSError:
            shutil.copyfile(src_ply, dst_ply)
        print(f"[{scene}] gt={len(matched)} ply={it} {os.path.getsize(dst_ply)/1e6:.0f} MB")
    print("BUNGEE_DONE")


if __name__ == "__main__":
    main()
