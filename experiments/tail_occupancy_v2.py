"""Tail-occupancy v2: score only the primitives that are actually in the picture.

v1 returned rest_mean = 0.000 on every scene, which looked like a huge signal and was an
artefact: primitives that never project into any calibration view have seen = 0 and were
scored 0, so the "top 30% vs the rest" contrast measured visibility, not tail mass.

v2 fixes four things:
  * the ranking is restricted to the visible set (seen > 0), which is also the set a
    pruner can actually choose from;
  * a random baseline is scored in the same restricted set, so any residual contrast is
    measured against the right null;
  * unreadable npz (a file still being written) is skipped instead of aborting the run;
  * the visibility fraction is reported, because a score that is undefined for most
    primitives cannot drive a full budget.
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

from tail_occupancy import tail_occupancy  # noqa: E402  (projection + scoring live there)


def contrast(score, vis, mask=None, frac=0.3):
    """Mean of the top ``frac`` minus the mean of the rest, over the visible set."""
    idx = np.nonzero(vis)[0] if mask is None else np.nonzero(vis & mask)[0]
    if idx.size < 10:
        return None
    s = score[idx]
    k = max(1, int(frac * idx.size))
    order = np.argsort(-s)
    return float(s[order[:k]].mean() - s[order[k:]].mean()), int(idx.size), k


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
        means = np.asarray(sc["prim_means"])
        score, hit, seen = tail_occupancy(resid, means, np.asarray(sc["c2w"]),
                                          np.asarray(sc["K"]), q, cal)
        vis = seen > 0
        got = contrast(score, vis)
        rng = np.random.default_rng(0)
        null = contrast(rng.random(score.size), vis)      # random score, same set
        if got is None:
            C.log(f"  {name}: too few visible primitives")
            continue
        d, nvis, k = got
        out[name] = dict(q=float(q), n=int(score.size), visible=nvis,
                         visible_frac=nvis / score.size, top_k=k,
                         d=float(d), mean_top=float(np.sort(score[vis])[-k:].mean()),
                         mean_rest=float(np.sort(score[vis])[:-k].mean()),
                         d_random=float(null[0]) if null else None)
        C.log(f"  {name:14s} vis {nvis:>8,d} ({100*nvis/score.size:4.0f}%) "
              f"q={q:.4f} d={d:+.3f} (random {null[0]:+.3f})")
    C.json_dump(out_path, out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", default="tail_v2.json")
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    a = ap.parse_args(argv)
    run(a.npz, a.out, a.alpha)
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
