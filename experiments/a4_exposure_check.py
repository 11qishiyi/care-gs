#!/usr/bin/env python3
"""Is the clean splice's low PSNR on some scenes an exposure mismatch?

The A4 artifacts store ``gray_render`` (clean splice) and ``gray_gt``.  If a
scene's render and GT differ mostly by a global per-view gain (Mip-NeRF 360 is
auto-exposed and the archive convention ``gt/255`` does not undo it), then
``--gt-convention archive`` hands the coverage statistic a residual field whose
bulk is nuisance brightness, not geometry.  The coverage statistic is
self-calibrated (``q`` comes from the same pair) so the drop stays defined, but
the response to an edit is diluted.

This script quantifies that without re-rendering: for each view it reports the
mean brightness of render and GT, the raw gray PSNR, and the PSNR after fitting
a per-view affine ``a*r + b`` to the render.  A scene whose affine gain is far
from 1 has an exposure problem, not a geometry problem.

Usage::

    python experiments/a4_exposure_check.py --dump /workspace/res/a4/dump
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiments import common as C  # noqa: E402


def affine_fit(r, g):
    """Least-squares ``a*r + b`` approximating ``g``; returns (a, b, psnr)."""
    r = r.reshape(-1).astype(np.float64)
    g = g.reshape(-1).astype(np.float64)
    A = np.stack([r, np.ones_like(r)], 1)
    sol, *_ = np.linalg.lstsq(A, g, rcond=None)
    a, b = float(sol[0]), float(sol[1])
    fit = a * r + b
    mse = float(np.mean((fit - g) ** 2))
    psnr = 10.0 * np.log10(1.0 / max(mse, 1e-12))
    return a, b, psnr


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default="/workspace/res/a4/dump")
    ap.add_argument("--clean", default="clean")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    paths = C.discover_npz(args.dump)
    if not paths:
        raise SystemExit(f"no npz under {args.dump}")
    report = []
    for p in paths:
        sc = C.load_npz_scene(p)
        k = C.variant_index(sc, args.clean)
        gr = sc["gray_render"][k].astype(np.float32)   # (m,H,W)
        gg = sc["gray_gt"].astype(np.float32)          # (m,H,W)
        views = np.asarray(sc["views"]).tolist()
        rows = []
        for i in range(gr.shape[0]):
            r, g = gr[i], gg[i]
            a, b, pa = affine_fit(r, g)
            rows.append({
                "view": views[i],
                "mean_render": float(r.mean()),
                "mean_gt": float(g.mean()),
                "gain_needed": float(g.mean() / max(r.mean(), 1e-6)),
                "psnr_raw": float(C.psnr_np(r, g)),
                "psnr_affine": float(pa),
                "affine_a": a,
                "affine_b": b,
            })
        sel = rows
        scene = {
            "scene": sc["meta"].get("scene", os.path.basename(p)),
            "n_views": len(rows),
            "psnr_raw_mean": float(np.mean([r["psnr_raw"] for r in sel])),
            "psnr_affine_mean": float(np.mean([r["psnr_affine"] for r in sel])),
            "gain_needed_median": float(np.median([r["gain_needed"] for r in sel])),
            "gain_needed_min": float(np.min([r["gain_needed"] for r in sel])),
            "gain_needed_max": float(np.max([r["gain_needed"] for r in sel])),
            "views": rows,
        }
        report.append(scene)
        print(f"{scene['scene']:<12} views={scene['n_views']:>3}  "
              f"psnr raw {scene['psnr_raw_mean']:6.2f} dB  "
              f"affine {scene['psnr_affine_mean']:6.2f} dB  "
              f"gain needed {scene['gain_needed_median']:.3f} "
              f"[{scene['gain_needed_min']:.3f},{scene['gain_needed_max']:.3f}]",
              flush=True)
    if args.out:
        C.json_dump(args.out, {"scenes": report})
        print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
