"""End-to-end: does any cheap criterion preserve the certificate better than Fisher?

Every attempt to estimate a per-primitive causal effect failed, for a reason that is now
clear: one primitive in five million moves the global tail probability by ~1e-8, below
resolution. So we stop estimating the effect and measure the endpoint instead --- keep the
top 30% by each criterion, re-render the calibration views, and read the coverage drop
directly. No additivity assumption is needed for this comparison.

    python3 experiments/criterion_eval.py --npz dump/bicycle.npz \
        --ply .../point_cloud.ply --budget 0.3 --out crit_bicycle.json

Criteria: opacity (what a viewer does), volume (classic importance), random (the floor),
tail (the proxy we just killed --- kept in as a control), and optionally ``--pup-ply`` for
the Fisher ranking written by make_pup_variant.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from tail_occupancy import project  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--ply", required=True)
    ap.add_argument("--pup-ply", default="", help="top-30% PLY written by make_pup_variant")
    ap.add_argument("--budget", type=float, default=0.3)
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="criterion.json")
    a = ap.parse_args(argv)

    import torch
    from calib.gsrender import load_splats, render

    sc = C.load_npz_scene(a.npz)
    meta = sc["meta"]
    H, W = int(meta["height"]), int(meta["width"])
    c2w = torch.as_tensor(np.asarray(sc["c2w"]), dtype=torch.float32, device="cuda")
    K = torch.as_tensor(np.asarray(sc["K"]), dtype=torch.float32, device="cuda")
    gt = np.asarray(sc["gray_gt"], np.float32)
    m = c2w.shape[0]
    cal = np.asarray(C.split_perms(m, 1, C.RNG_SEED)[0][0])

    sp = load_splats(a.ply, device="cuda")
    n = int(sp.n)

    def coverage(splats):
        out = render(splats, c2w[cal], K[cal], W, H, sh_degree=splats.sh_degree)
        g = out["colors"].float().cpu().numpy().mean(-1)
        return np.abs(g - gt[cal]).astype(np.float32)

    r0 = coverage(sp)
    q = C.cq(r0.reshape(-1), a.alpha)
    p0 = float((r0 > q).mean())
    C.log(f"{meta['scene']}: n={n:,d}  q={q:.4f}  P0={p0*100:.2f}%")

    k = max(1, int(round(a.budget * n)))
    op = sp.opacities.detach().cpu().numpy()
    vol = torch.exp(sp.scales).prod(1).detach().cpu().numpy()
    rng = np.random.default_rng(a.seed)

    # tail occupancy over the calibration views, the criterion we killed as a proxy
    resid_all = np.abs(np.asarray(sc["resid"][[str(v) for v in sc["variant_names"]].index("clean")],
                                  np.float32).mean(0) if False else
                       np.asarray(sc["resid"][[str(v) for v in sc["variant_names"]].index("clean")],
                                  np.float32))
    means = np.asarray(sc["prim_means"])
    hit = np.zeros(means.shape[0], np.float64)
    seen = np.zeros(means.shape[0], np.float64)
    above = (resid_all > q).astype(np.float64)
    for i in cal:
        yy, xx, keep = project(means, np.asarray(sc["c2w"])[i], np.asarray(sc["K"])[i], H, W)
        idx = np.nonzero(keep)[0]
        if idx.size:
            hit[idx] += above[i][yy[idx], xx[idx]]
            seen[idx] += 1
    tail = hit / np.maximum(seen, 1)

    criteria = dict(opacity=op, volume=vol, random=rng.random(n), tail=tail, tail_inv=-tail)
    rows = {}
    for name, score in criteria.items():
        keep = np.argsort(-score)[:k]
        sub = sp.subset(torch.as_tensor(keep, device="cuda"))
        r1 = coverage(sub)
        p1 = float((r1 > q).mean())
        rows[name] = dict(p1=p1, drop_pp=100 * (p0 - p1))
        C.log(f"  {name:9s} keep {k:,d}  cov {p1*100:6.2f}%  drop {100*(p0-p1):+6.2f} pp")
        del sub
        torch.cuda.empty_cache()

    if a.pup_ply:
        sp2 = load_splats(a.pup_ply, device="cuda")
        r1 = coverage(sp2)
        p1 = float((r1 > q).mean())
        rows["fisher_pup"] = dict(p1=p1, drop_pp=100 * (p0 - p1), kept=int(sp2.n))
        C.log(f"  fisher    keep {int(sp2.n):,d}  cov {p1*100:6.2f}%  "
              f"drop {100*(p0-p1):+6.2f} pp")

    C.json_dump(a.out, dict(scene=meta["scene"], q=q, p0=p0, budget=a.budget, rows=rows))
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
