"""Is the clean-render gap an activation bug in the loader?

`gsplat.load_ply_to_splats` returns INRIA PLY attributes in their stored form: scales in log
space, opacities as logits.  If it already activates them, applying the activation a second time
is silent -- sigmoid(sigmoid(x)) keeps every opacity in (0.5, 0.76), which makes the scene
half-transparent and costs 3-5 dB while SSIM stays high.  This probe measures the mean rendered
alpha and PSNR under both readings of the opacity column, and the same for the scale column.

    python experiments/probe_opacity.py --archive <arch> --scene bonsai_smoke --n-views 3
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))
from calib.archive_only import load_archive_only_scene  # noqa: E402
from calib.gsrender import Splats, load_splats, render  # noqa: E402


def find_ply(archive: str, scene: str) -> str:
    base = os.path.join(archive, "output", scene, "point_cloud")
    best = None
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d, "point_cloud.ply")
        if os.path.isfile(p):
            best = p
    if best is None:
        raise SystemExit(f"no PLY under {base}")
    return best


def psnr01(a, b):
    return 10.0 * np.log10(1.0 / max(float(np.mean((a - b) ** 2)), 1e-12))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--n-views", type=int, default=3)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    sc = load_archive_only_scene(args.archive, args.scene, factor=args.factor)
    base = load_splats(find_ply(args.archive, args.scene), device=args.device)
    idx = list(np.asarray(sc["cal_idx"]))[: args.n_views]
    c2w = torch.as_tensor(np.asarray(sc["camtoworlds"])[idx])
    Ks = torch.as_tensor(np.asarray(sc["Ks"])[idx])
    H, W = int(sc["height"]), int(sc["width"])
    paths = np.asarray(sc["image_paths"])
    gts = np.stack([np.asarray(Image.open(paths[i]).convert("RGB").resize((W, H), Image.BILINEAR),
                               np.float32) / 255.0 for i in idx])

    def run(tag, splats):
        out = render(splats, c2w, Ks, W, H)
        pred = out["colors"].detach().cpu().clamp(0, 1).numpy()
        alpha = out["alphas"].detach().cpu().numpy()
        ps = np.mean([psnr01(pred[i], gts[i]) for i in range(len(idx))])
        print(f"  {tag:34s} PSNR {ps:6.2f} dB  alpha {alpha.mean():.4f} "
              f"(p05 {np.percentile(alpha, 5):.3f})  opacity {float(splats.opacities.mean()):.3f}")
        del out, pred, alpha

    print(f"scene {args.scene}  prims {base.n}  {W}x{H}  views {len(idx)}")
    run("as loaded (sigmoid applied by us)", base)

    # undo one sigmoid: treat the loaded opacities as if they were already in (0,1)
    o = base.opacities.clamp(1e-6, 1 - 1e-6)
    sp = Splats(means=base.means, scales=base.scales, quats=base.quats,
                opacities=torch.log(o / (1 - o)), sh0=base.sh0, shN=base.shN)
    run("opacity read as logit again", sp)
    del sp

    # undo one exp: treat the loaded scales as if they were already positive
    s = base.scales.clamp_min(1e-8)
    sp = Splats(means=base.means, scales=torch.log(s), quats=base.quats,
                opacities=base.opacities, sh0=base.sh0, shN=base.shN)
    run("scale read as log again", sp)
    del sp


if __name__ == "__main__":
    main()
