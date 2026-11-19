"""Causal deletion effect on the certified quantity, by sampling.

``Delta_i = P(r > q | alpha_i = 0) - P(r > q)`` is the only honest answer to "what does
deleting this primitive cost the certificate".  Every cheap proxy we tried (three times)
was correlational and fooled us; this measures the thing itself for a random sample so a
cheap estimator can be scored against it.

Everything comes from the dump plus the PLY, so the resolution, the cameras and the ground
truth are the ones the rest of the paper uses:

    python3 experiments/causal_delta.py --npz dump/bicycle.npz \
        --ply /workspace/data/out3dgs/output/bicycle/point_cloud/iteration_40000/point_cloud.ply \
        --n 50 --out causal_bicycle.json

The first run is deliberately tiny (``--n 50``): it exists to prove the render path and
the fixed-denominator argument, not to produce a number.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def load_npz(path):
    sc = C.load_npz_scene(path)
    return sc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--ply", required=True)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="causal.json")
    a = ap.parse_args(argv)

    import torch
    from calib.gsrender import load_splats, render

    sc = load_npz(a.npz)
    meta = sc["meta"]
    H, W = int(meta["height"]), int(meta["width"])
    c2w = torch.as_tensor(np.asarray(sc["c2w"]), dtype=torch.float32, device="cuda")
    K = torch.as_tensor(np.asarray(sc["K"]), dtype=torch.float32, device="cuda")
    gt = np.asarray(sc["gray_gt"], np.float32)                 # (m,H,W)
    m = c2w.shape[0]
    C.log(f"{meta['scene']}: {m} views, {H}x{W}")

    sp = load_splats(a.ply, device="cuda")
    C.log(f"loaded {sp.n:,d} primitives")

    # calibration half, as everywhere else in the paper
    cal, _ = C.split_perms(m, 1, C.RNG_SEED)[0]
    cal = np.asarray(cal)

    def resid_of(splats):
        out = render(splats, c2w[cal], K[cal], W, H, sh_degree=splats.sh_degree)
        col = out["colors"].float().cpu().numpy()              # (m_cal,H,W,3)
        g = col.mean(-1)
        return np.abs(g - gt[cal]).astype(np.float32)

    r0 = resid_of(sp)
    q = C.cq(r0.reshape(-1), a.alpha)
    p0 = float((r0 > q).mean())
    C.log(f"q={q:.4f}  P0={p0:.4f} over {r0.size:,d} pixels")

    rng = np.random.default_rng(a.seed)
    idx = rng.choice(int(sp.n), size=min(a.n, int(sp.n)), replace=False)
    rows = []
    for j, i in enumerate(idx):
        op = sp.opacities.clone()
        op[i] = 0.0
        sp2 = type(sp)(sp.means, sp.scales, sp.quats, op, sp.sh0, sp.shN)
        r1 = resid_of(sp2)
        p1 = float((r1 > q).mean())
        rows.append(dict(i=int(i), p1=p1, delta=p1 - p0,
                         opacity=float(sp.opacities[i]),
                         volume=float(torch.exp(sp.scales[i]).prod()),
                         r_local=float(r0[:, (r0 > q).any(axis=0)].mean())
                         if (r0 > q).any() else 0.0))
        if (j + 1) % 10 == 0:
            C.log(f"  {j+1}/{len(idx)} delta so far "
                  f"{np.mean([r['delta'] for r in rows]):+.5f}")
        del sp2
        torch.cuda.empty_cache()

    d = np.array([r["delta"] for r in rows])
    o = np.array([r["opacity"] for r in rows])
    v = np.array([r["volume"] for r in rows])
    C.log(f"delta: mean {d.mean():+.5f}  std {d.std():.5f}  "
          f"nonzero {int((np.abs(d) > 1e-9).sum())}/{d.size}")
    if d.std() > 0:
        from scipy.stats import spearmanr
        C.log(f"spearman(delta, opacity) = {spearmanr(d, o).statistic:+.3f}")
        C.log(f"spearman(delta, volume)  = {spearmanr(d, v).statistic:+.3f}")
    C.json_dump(a.out, dict(scene=meta["scene"], q=q, p0=p0, n=len(rows), rows=rows))
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
