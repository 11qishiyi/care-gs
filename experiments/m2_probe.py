#!/usr/bin/env python3
"""M2 probe: is a *relative* grid for the means the missing piece?

M1 charged geometry ``11*b/8`` bytes with one scene-level min--max grid per
component, and the iso family showed that this is catastrophic for positions:
10-bit means cost -8 dB while 8-bit scales/quats/opacities cost nothing.  A
relative grid costs one 5-bit exponent per primitive and makes the mantissa
relative to that primitive's own magnitude.

Run on the node (needs CUDA, ~1 min/scene):

    python experiments/m2_probe.py --archive /workspace/data/out3dgs \
        --scenes bicycle,flowers --out /workspace/res/m2/probe.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def _common():
    import common as C
    C.add_code_root()
    return C


def rel_grid(means, bits, exp_bits=5, half_octave=True):
    """Quantise ``means`` (N,3) with one shared magnitude exponent per primitive.

    Returns a dict with the reconstructed tensor and the byte cost per primitive,
    so the caller cannot forget that the exponent is not free.
    """
    import torch
    s = means.abs().amax(dim=1, keepdim=True).clamp_min(1e-12)      # (N,1)
    lo = torch.log2(s) * (2.0 if half_octave else 1.0)
    n_lev = (1 << int(exp_bits)) - 1
    e_lo = lo.amin()
    step = (lo.amax() - e_lo).clamp_min(1e-9) / float(n_lev)
    e_q = e_lo + torch.round((lo - e_lo) / step).clamp_(0.0, float(n_lev)) * step
    s_q = torch.pow(2.0, -e_q / (2.0 if half_octave else 1.0))
    n_m = (1 << int(bits)) - 1
    # u in [-1, 1] because s_q is at least the largest component of that primitive
    u = (means / s_q).clamp(-1.0, 1.0)
    u_q = torch.round(u * n_m) / float(n_m)
    out = u_q * s_q
    bytes_per_prim = 3.0 * bits / 8.0 + exp_bits / 8.0
    return dict(means=out, bytes_per_prim=bytes_per_prim,
                err=float((out - means).abs().mean()))


def glob_grid(t, bits):
    import torch
    n_lev = (1 << int(bits)) - 1
    mn = t.amin(dim=0, keepdim=True)
    mx = t.amax(dim=0, keepdim=True)
    step = (mx - mn).clamp_min(1e-12) / float(n_lev)
    return mn + torch.round((t - mn) / step).clamp_(0.0, float(n_lev)) * step


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers")
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--out", default="/workspace/res/m2/probe.json")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--n-views", type=int, default=4)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args(argv)

    C = _common()
    import numpy as np
    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.gsrender import load_splats, render

    rows = []
    for scene in [s for s in args.scenes.split(",") if s]:
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor,
                                     cal_frac=args.cal_frac)
        W, H = sc["width"], sc["height"]
        idx = list(sc["dep_idx"])[:args.n_views]
        c2w = torch.as_tensor(sc["camtoworlds"][idx], dtype=torch.float32, device=args.device)
        K = torch.as_tensor(sc["Ks"][idx], dtype=torch.float32, device=args.device)
        from calib.colmap_io import load_images
        gt = load_images([sc["image_paths"][i] for i in idx], args.factor, (W, H))
        gt = gt.astype(np.float32) / 255.0
        gt_t = torch.as_tensor(gt, device=args.device)

        ply = args.ply_pattern.format(archive=args.archive, scene=scene)
        sp = load_splats(ply, device=args.device)
        C.log(f"{scene}: {sp.n:,d} primitives, {W}x{H}, {len(idx)} views")

        def score(splats, tag, bpp):
            out = render(splats, c2w, K, W, H, chunk=4)
            cols = out["colors"].clamp(0, 1)
            p = float(np.mean([C.psnr_np(cols[i].detach().cpu().numpy(),
                                         gt[i]) for i in range(len(idx))]))
            rows.append(dict(scene=scene, variant=tag, psnr=p, bytes_per_prim=bpp))
            C.log(f"  {tag:22s} PSNR={p:6.2f} B/pr={bpp:6.2f}")
            del out
            if str(args.device).startswith("cuda"):
                torch.cuda.empty_cache()
            return p

        base = score(sp, "clean", 236.0)
        for bits in (10, 12):
            q = sp.clone()
            q.means = glob_grid(sp.means, bits)
            score(q, f"glob_means{bits}", 236.0 - 3 * (32 - bits) / 8)
            del q
        for bits in (8, 10, 12, 14):
            for eb in (5,):
                q = sp.clone()
                r = rel_grid(sp.means, bits, exp_bits=eb)
                q.means = r["means"]
                geo_only = 3 * bits / 8 + eb / 8 + (3 * 8 + 4 * 8 + 8) / 8
                score(q, f"rel_means{bits}_e{eb}", geo_only)
                del q, r
        del sp
        if str(args.device).startswith("cuda"):
            torch.cuda.empty_cache()
        C.log(f"{scene}: base {base:.2f} dB")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(dict(rows=rows), fh, indent=1)
    C.log(f"WROTE {args.out}")
    for r in rows:
        C.log(f"  {r['scene']:10s} {r['variant']:22s} {r['psnr']:6.2f} dB  {r['bytes_per_prim']:6.2f} B/pr")
    return 0


if __name__ == "__main__":
    sys.exit(main())
