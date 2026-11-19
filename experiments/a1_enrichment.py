"""A1 verdict v2: rank by the score, sum the tail mass.

The first version of this script ranked by ``hit`` and then summed ``hit``, which makes
the enrichment equal to 1/frac by construction for every score, including random.  The
correct quantity ranks primitives by the **score** and sums their **tail mass**:

    E = [tail mass in the top 30% ranked by score] / [0.30 * total tail mass]

E = 1.0 means the score is uninformative about where tail mass sits, whatever the score's
distribution looks like, so the null is fixed by construction and can be checked by
shuffling the score.
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from tail_occupancy import tail_occupancy  # noqa: E402


def enrichment(score, hit, vis, frac=0.3):
    idx = np.nonzero(vis)[0]
    if idx.size < 10:
        return None
    s, h = score[idx], hit[idx]
    total = h.sum()
    if total <= 0:
        return None
    k = max(1, int(frac * idx.size))
    order = np.argsort(-s)
    top = h[order[:k]].sum()
    return float(top / total / frac), int(idx.size), float(total)


def run(npz_dir, out_path, alpha):
    out = {}
    for path in C.discover_npz(npz_dir):
        name = os.path.basename(path)[:-4]
        try:
            sc = C.load_npz_scene(path)
        except (zipfile.BadZipFile, OSError) as exc:
            C.log(f"  skip {name}: {type(exc).__name__}")
            continue
        vnames = [str(v) for v in sc["variant_names"]]
        resid = np.asarray(sc["resid"][vnames.index("clean")], np.float32)
        m = resid.shape[0]
        cal = C.split_perms(m, 1, C.RNG_SEED)[0][0]
        q = C.cq(resid.reshape(m, -1)[cal].reshape(-1), alpha)
        score, hit, seen = tail_occupancy(resid, np.asarray(sc["prim_means"]),
                                          np.asarray(sc["c2w"]), np.asarray(sc["K"]), q, cal)
        vis = seen > 0
        a = enrichment(score, hit, vis)
        rng = np.random.default_rng(0)
        b = enrichment(rng.random(score.size), hit, vis)   # null: random ranking
        if a is None:
            C.log(f"  {name}: no tail mass / too few visible")
            continue
        out[name] = dict(q=float(q), n=int(score.size), visible=a[1],
                         visible_frac=a[1] / score.size, tail_mass=a[2],
                         E=a[0], E_random=(b[0] if b else None))
        C.log(f"  {name:14s} vis {100*a[1]/score.size:4.0f}%  "
              f"E={a[0]:.3f}  (random {b[0] if b else float('nan'):.3f})")
    C.json_dump(out_path, out)
    vals = np.array([v["E"] for v in out.values()])
    if vals.size:
        print(f"n={vals.size}  E median {np.median(vals):.3f}  "
              f"min {vals.min():.3f}  max {vals.max():.3f}  "
              f">=1.30 in {int((vals >= 1.30).sum())}/{vals.size}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", default="a1_enrichment.json")
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    a = ap.parse_args(argv)
    run(a.npz, a.out, a.alpha)
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
