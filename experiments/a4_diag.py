"""Throwaway diagnostic: is the A4 render actually reacting to the edits?

Two questions, in order:

  1. does the stored residual of each variant differ from ``clean`` at all?
  2. when a view is rendered live, is the image mostly empty (alpha ~ 0) or is
     the render simply insensitive to removing half the primitives?

Run on the node:

    PYTHONPATH=/workspace/code/research/code:/workspace/code python experiments/a4_diag.py \
        --npz /workspace/res/a4/smoke/bicycle.npz --scene bicycle
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

C.add_code_root()

from calib.archive_only import load_archive_only_scene  # noqa: E402
from calib.colmap_io import load_images, normalize_exposure  # noqa: E402
from calib.gsrender import load_splats, render  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", default="/workspace/res/a4/smoke/bicycle.npz")
    ap.add_argument("--scene", default="bicycle")
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    sc = C.load_npz_scene(args.npz)
    names = [str(v) for v in sc["variant_names"]]
    resid = np.asarray(sc["resid"])
    gray = np.asarray(sc["gray_render"])
    print(f"resid {resid.shape} gray {gray.shape} names {names}")
    ci = names.index("clean")
    for i, n in enumerate(names):
        d = resid[i].astype(np.float32) - resid[ci].astype(np.float32)
        g = gray[i].astype(np.float32)
        print(f"  {n:>8s} resid_mean={resid[i].astype(np.float32).mean():.5f} "
              f"gray_mean={g.mean():.4f} gray_std={g.std():.4f} "
              f"maxabs_vs_clean={np.abs(d).max():.3e} "
              f"frac>1e-4={float((np.abs(d) > 1e-4).mean()):.4f}")

    # --- live render of one calibration view, clean vs prune50 -------------
    import torch
    from calib.gsrender import Splats
    scene = load_archive_only_scene(args.archive, args.scene, factor=args.factor)
    W, H = int(scene["width"]), int(scene["height"])
    _gt = load_images(scene["image_paths"], args.factor, (W, H))
    gt = (_gt.astype(np.float32) / 255.0)
    c2w = torch.from_numpy(scene["camtoworlds"]).float().to(args.device)
    K = torch.from_numpy(scene["Ks"]).float().to(args.device)
    ply = args.ply_pattern.format(archive=args.archive, scene=args.scene)
    base = load_splats(ply, device=args.device)
    print(f"live: {base.n} prims, ply {os.path.getsize(ply)/2**30:.2f} GiB, "
          f"{W}x{H}, gt in [{gt.min():.3f},{gt.max():.3f}]")

    vi = int(scene["cal_idx"][0])
    for label, sp in (("clean", base), ("half", base.subset(torch.arange(0, base.n, 2)))):
        out = render(sp, c2w[vi:vi + 1], K[vi:vi + 1], W, H)
        cols = out["colors"][0].cpu().numpy()
        alps = out["alphas"][0].cpu().numpy()
        p = C.psnr_np(cols, gt[vi])
        print(f"  {label:5s} n={sp.n:>9,d} rgb mean={cols.mean():.4f} "
              f"min={cols.min():.3f} max={cols.max():.3f} "
              f"alpha mean={alps.mean():.4f} max={alps.max():.3f} PSNR={p:.2f}")

    # --- what does an identity-ish sanity check say about the sizing ------
    print(f"gt[vi] mean={gt[vi].mean():.4f} std={gt[vi].std():.4f}")
    print(f"psnr(gt, gt) = {C.psnr_np(gt[vi], gt[vi]):.2f}")
    print(f"psnr(zeros, gt) = {C.psnr_np(np.zeros_like(gt[vi]), gt[vi]):.2f}")
    print(f"psnr(mean, gt) = {C.psnr_np(np.full_like(gt[vi], gt[vi].mean()), gt[vi]):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
