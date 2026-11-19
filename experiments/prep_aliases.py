"""Build alias scene entries so that geometric edits can be tested at a *second
optimisation depth* (iteration_7000) without touching the loader.

For every base scene S with ``output/S/point_cloud/iteration_7000/point_cloud.ply``
this creates ``output/S_i7k`` with:
  cameras.json                      (copy of S)
  point_cloud/iteration_40000/point_cloud.ply   (hardlink -> the 7k PLY)
  test/ours_40000/gt/*.png          (copy of S's held-out GT)

The loader (calib.archive_only) and dump_artifacts' default --ply-pattern both read
``iteration_40000`` and ``test/ours_40000/gt``, so the alias is a drop-in scene
whose *checkpoint* is the 7k one.  Pure file plumbing, no science.
"""
from __future__ import annotations

import argparse
import os
import shutil


def link_or_copy(src: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill,bonsai")
    ap.add_argument("--src-iter", default="iteration_7000")
    ap.add_argument("--alias-suffix", default="_i7k")
    args = ap.parse_args()

    made = []
    for s in [x.strip() for x in args.scenes.split(",") if x.strip()]:
        base = os.path.join(args.archive, "output", s)
        src_ply = os.path.join(base, "point_cloud", args.src_iter, "point_cloud.ply")
        src_cam = os.path.join(base, "cameras.json")
        src_gt = os.path.join(base, "test", "ours_40000", "gt")
        if not (os.path.isfile(src_ply) and os.path.isfile(src_cam) and os.path.isdir(src_gt)):
            print(f"[{s}] SKIP: missing ply/cameras/gt "
                  f"({os.path.isfile(src_ply)}, {os.path.isfile(src_cam)}, {os.path.isdir(src_gt)})")
            continue
        alias = s + args.alias_suffix
        dst = os.path.join(args.archive, "output", alias)
        link_or_copy(src_cam, os.path.join(dst, "cameras.json"))
        link_or_copy(src_ply, os.path.join(dst, "point_cloud", "iteration_40000", "point_cloud.ply"))
        n = 0
        for f in sorted(os.listdir(src_gt)):
            link_or_copy(os.path.join(src_gt, f), os.path.join(dst, "test", "ours_40000", "gt", f))
            n += 1
        made.append((alias, n, os.path.getsize(src_ply) / 1e6))
        print(f"[{alias}] ok: {n} gt views, ply {made[-1][2]:.0f} MB (from {args.src_iter})")
    print("ALIAS_DONE", len(made))


if __name__ == "__main__":
    main()
