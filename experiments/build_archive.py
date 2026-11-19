"""Build an INRIA-format 'out3dgs' archive from the official pretrained models + Mip-NeRF360 images.

Why: every script in this repo (and in experiments/) reads scenes through
``calib.archive_only.load_archive_only_scene``, which expects

    <archive>/output/<scene>/cameras.json
    <archive>/output/<scene>/point_cloud/iteration_40000/point_cloud.ply
    <archive>/output/<scene>/test/ours_40000/gt/{j:05d}.png

The official release (repo-sam.inria.fr .../pretrained/models.zip) ships the PLY and
cameras.json but no ground-truth test images.  Mip-NeRF 360 images come from the
ModelScope mirror (``<data>/<scene>/images_4``).  This script stitches the two into the
layout the loaders expect.  It does NOT modify the images: ground truth stays exactly as
the dataset ships it, so any photometric mismatch is measured, not introduced.

    python experiments/build_archive.py --models /workspace/data/models \
        --images /workspace/data/mip360 --archive /workspace/data/official \
        --scenes flowers,bicycle,treehill,stump
"""
from __future__ import annotations

import argparse
import json
import os
import shutil


def find_ply(models_root: str, scene: str) -> str:
    base = os.path.join(models_root, "output", scene)
    cands = []
    pc = os.path.join(base, "point_cloud")
    if os.path.isdir(pc):
        for d in sorted(os.listdir(pc)):
            p = os.path.join(pc, d, "point_cloud.ply")
            if os.path.isfile(p):
                cands.append(p)
    if not cands:
        for root, _dirs, files in os.walk(base):
            for f in files:
                if f.endswith(".ply"):
                    cands.append(os.path.join(root, f))
    if not cands:
        raise SystemExit(f"[{scene}] no point_cloud.ply under {base}")
    # prefer the largest iteration number
    cands.sort(key=lambda p: str(p))
    return cands[-1]


def index_images(images_root: str, scene: str) -> dict:
    """stem(lower) -> path for every image of the scene."""
    out = {}
    for sub in ("images_4", "images_2", "images"):
        d = os.path.join(images_root, scene, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            stem, ext = os.path.splitext(f)
            if ext.lower() in (".jpg", ".jpeg", ".png"):
                out.setdefault(stem.lower(), os.path.join(d, f))
        if out:
            out["__subdir__"] = sub
            return out
    raise SystemExit(f"[{scene}] no images under {images_root}/{scene}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="/workspace/data/models")
    ap.add_argument("--images", default="/workspace/data/mip360")
    ap.add_argument("--archive", default="/workspace/data/official")
    ap.add_argument("--scenes", default="flowers,bicycle,treehill,stump")
    ap.add_argument("--llffhold", type=int, default=8)
    ap.add_argument("--iter-name", default="iteration_40000")
    ap.add_argument("--report", default="/workspace/res/archive_build.json")
    args = ap.parse_args()

    report = []
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        src_cams = os.path.join(args.models, "output", scene, "cameras.json")
        if not os.path.isfile(src_cams):
            print(f"[{scene}] SKIP: no cameras.json at {src_cams}")
            continue
        cams = json.load(open(src_cams, encoding="utf-8"))
        cams.sort(key=lambda c: c["img_name"])
        sel = [i for i in range(len(cams)) if i % args.llffhold == 0]
        imgs = index_images(args.images, scene)
        subdir = imgs.pop("__subdir__")
        picked, missing = [], []
        for i in sel:
            stem = os.path.splitext(os.path.basename(cams[i]["img_name"]))[0].lower()
            p = imgs.get(stem)
            if p is None:
                missing.append(cams[i]["img_name"])
            else:
                picked.append((i, p))
        print(f"[{scene}] cameras={len(cams)} test={len(sel)} matched={len(picked)} "
              f"missing={len(missing)} images={subdir}")
        if missing[:3]:
            print("   missing e.g.", missing[:3])
        if not picked:
            print(f"[{scene}] SKIP: no matched ground truth")
            continue

        base = os.path.join(args.archive, "output", scene)
        gt_dir = os.path.join(base, "test", "ours_40000", "gt")
        ply_dir = os.path.join(base, "point_cloud", args.iter_name)
        os.makedirs(gt_dir, exist_ok=True)
        os.makedirs(ply_dir, exist_ok=True)
        for j, (_i, p) in enumerate(picked):
            shutil.copyfile(p, os.path.join(gt_dir, f"{j:05d}.png"))
        if not os.path.isfile(os.path.join(base, "cameras.json")):
            shutil.copyfile(src_cams, os.path.join(base, "cameras.json"))
        ply_src = find_ply(args.models, scene)
        ply_dst = os.path.join(ply_dir, "point_cloud.ply")
        if not os.path.isfile(ply_dst):
            try:
                os.link(ply_src, ply_dst)
            except OSError:
                shutil.copyfile(ply_src, ply_dst)

        gt_w, gt_h = None, None
        try:
            from PIL import Image
            with Image.open(os.path.join(gt_dir, "00000.png")) as im:
                gt_w, gt_h = im.size
        except Exception:
            pass
        report.append(dict(scene=scene, cams=len(cams), test=len(sel), matched=len(picked),
                           image_subdir=subdir, ply=ply_src, ply_mb=round(os.path.getsize(ply_src) / 1e6, 1),
                           cam_width=cams[0]["width"], cam_height=cams[0]["height"],
                           gt_width=gt_w, gt_height=gt_h,
                           ratio_w=(cams[0]["width"] / gt_w) if gt_w else None))

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    json.dump(report, open(args.report, "w", encoding="utf-8"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
