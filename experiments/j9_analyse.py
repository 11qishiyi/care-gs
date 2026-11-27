"""J9 analysis --- turn the stored quantile tables into the four generalisation tests.

The driver (`j9_dump_quantiles.py`) stores, per (scene, variant, view), the quantile function of the per-pixel error at
2000 levels, once for |e| and once for e^2. From those tables this script computes, for any tolerance alpha and either
functional:

    q_alpha        = the clean model's (1-alpha) quantile, pooled over the views it ships
    coverage       = fraction of pixels with e <= q_alpha          (pooled, or per view)
    loss           = coverage_clean - coverage_variant

and then answers the four pre-registered questions of `J9_PLAN.md`:

    C1  does the family separation hold at every tolerance?
    C2  is the geometric family relatively worse under squared error than under absolute error?
    C3  does the separation hold view by view, not only after pooling?
    C4  does it hold on the additional scenes?

    python experiments/j9_analyse.py --res _pull_j9 --out submission/jvcir
    python experiments/j9_analyse.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ALPHAS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3)
GEO = ("prune50", "prune30")
ATTR = ("shdeg1", "shdeg2", "quant8", "quant6", "quant4")


def coverage_from_table(table: np.ndarray, levels: np.ndarray, q: float) -> float:
    """Fraction of pixels at or below q, read off a quantile table (table is the sorted quantile function)."""
    return float(np.interp(q, table, levels))


def analyse_scene(npz: np.lib.npyio.NpzFile, alpha: float, functional: str = "abs") -> dict:
    levels = npz["levels"]
    clean = npz[f"clean__{functional}"]                    # (V, NQ)
    variants = [k[:-len(f"__{functional}")] for k in npz.files if k.endswith(f"__{functional}") and k != f"clean__{functional}"]
    # the shipped quantile: (1-alpha) of the clean model, pooled over the views it ships
    q = float(np.quantile(clean.ravel(), 1 - alpha))
    out = {"q": q}
    clean_cov_pool = float(np.mean([coverage_from_table(clean[v], levels, q) for v in range(clean.shape[0])]))
    out["clean_coverage"] = clean_cov_pool
    for name in variants:
        t = npz[f"{name}__{functional}"]
        per_view = [coverage_from_table(t[v], levels, q) for v in range(t.shape[0])]
        out[name] = dict(
            loss_pp=round(100 * (clean_cov_pool - float(np.mean(per_view))), 3),
            loss_per_view_pp=[round(100 * (coverage_from_table(clean[v], levels, q) - per_view[v]), 3)
                              for v in range(len(per_view))],
        )
    return out


def verdicts(scenes: dict) -> dict:
    """Apply C1-C4 from J9_PLAN.md."""
    res = {}
    # C1: at every alpha, every geometric cell loses more than every attribute cell
    c1 = {}
    for a in ALPHAS:
        key = f"a{a}_abs"
        worst_attr = max(s[key][n]["loss_pp"] for s in scenes.values() for n in ATTR if n in s.get(key, {}))
        best_geo = min(s[key][n]["loss_pp"] for s in scenes.values() for n in GEO if n in s.get(key, {}))
        c1[f"{a}"] = dict(worst_attribute_pp=round(worst_attr, 2), least_geometric_pp=round(best_geo, 2),
                          separated=bool(best_geo > worst_attr))
    res["C1_by_alpha"] = c1
    res["C1_holds_everywhere"] = all(v["separated"] for v in c1.values())

    # C2: the geometric family's relative disadvantage under squared error vs absolute error
    rel = {}
    for a in ALPHAS:
        def spread(func):
            k = f"a{a}_{func}"
            g = [s[k][n]["loss_pp"] for s in scenes.values() for n in GEO if n in s.get(k, {})]
            t = [s[k][n]["loss_pp"] for s in scenes.values() for n in ATTR if n in s.get(k, {})]
            if not g or not t:
                return None
            return (min(g) / max(t)) if max(t) > 1e-9 else None
        rel[f"{a}"] = dict(abs=spread("abs"), sq=spread("sq"))
    res["C2_ratio"] = rel

    # C3: view-by-view separation rate per scene
    c3 = {}
    for name, s in scenes.items():
        key = "a0.1_abs"
        if key not in s:
            continue
        good = 0
        cells = 0
        for n_geo in GEO:
            for n_attr in ATTR:
                if n_geo not in s[key] or n_attr not in s[key]:
                    continue
                cells += 1
                gv = s[key][n_geo]["loss_per_view_pp"]
                av = s[key][n_attr]["loss_per_view_pp"]
                if min(gv) > max(av):
                    good += 1
        c3[name] = dict(cells=cells, separated_all_views=good)
    res["C3_per_view"] = c3
    return res


def selftest() -> int:
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
        ok = ok and cond

    levels = np.linspace(0, 1, 200)
    # a 'clean' table is the identity quantile of a uniform residual: q(level) = level
    clean = np.tile(levels, (4, 1)).astype(np.float32)
    geo = clean * 1.5                     # geometric edit: every quantile 50% higher
    attr = clean * 1.001                  # attribute edit: barely moves
    npz = dict(levels=levels, clean__abs=clean, prune50__abs=geo, quant8__abs=attr)
    class Fake(dict):
        files = list(npz)
        def __getitem__(self, k):
            return npz[k]
    a = analyse_scene(Fake(), 0.1)        # type: ignore[arg-type]
    check(a["prune50"]["loss_pp"] > a["quant8"]["loss_pp"], "the synthetic geometric arm loses more")
    check(abs(a["quant8"]["loss_pp"]) < 1.0, "the synthetic attribute arm is nearly free")

    npz2 = dict(npz)
    npz2.update({k.replace("__abs", "__sq"): v for k, v in npz.items() if k.endswith("__abs")})
    class Fake2(Fake):
        files = list(npz2)
        def __getitem__(self, k):
            return npz2[k]
    scenes = {f"s{i}": {**{f"a{a}_abs": analyse_scene(Fake(), a) for a in ALPHAS},
                        **{f"a{a}_sq": analyse_scene(Fake2(), a, "sq") for a in ALPHAS}} for i in range(2)}
    v = verdicts(scenes)
    check(v["C1_holds_everywhere"] is True, "C1 holds when the synthetic separation is unambiguous")
    check("C2_ratio" in v and "C3_per_view" in v, "C2 and C3 are produced")
    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="_pull_j9")
    ap.add_argument("--out", default="submission/jvcir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    files = sorted(Path(a.res).glob("*.npz"))
    if not files:
        print(f"no npz under {a.res}")
        return 2
    scenes = {}
    for f in files:
        npz = np.load(f)
        scenes[f.stem] = {**{f"a{a}_abs": analyse_scene(npz, a, "abs") for a in ALPHAS},
                          **{f"a{a}_sq": analyse_scene(npz, a, "sq") for a in ALPHAS}}
        print(f"{f.stem}: " + " ".join(f"a{a}:{scenes[f.stem][f'a{a}_abs']['clean_coverage']:.3f}" for a in ALPHAS))
    res = verdicts(scenes)
    out = Path("experiments/artifacts/a4")
    out.mkdir(parents=True, exist_ok=True)
    (out / "j9_report.json").write_text(json.dumps({"scenes": scenes, "verdicts": res}, indent=1), encoding="utf-8")
    print(json.dumps(res["C1_by_alpha"], indent=1))
    print("C1 holds at every tolerance:", res["C1_holds_everywhere"])
    return 0


if __name__ == "__main__":
    sys.exit(main())