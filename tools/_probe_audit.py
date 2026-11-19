"""Quick probe: is the 'label-free self-coverage audit' a working detector?

Reads the two archived self-coverage results (flowers, treehill) and prints, per
edit, the audit estimate (coverage of the EDITED model on the SHIPPED calibration
views at the SHIPPED q) against the true post-edit deployment coverage.
"""
import json

for s in ["flowers", "treehill"]:
    d = json.load(open(f"research/results_v3/sc_{s}.json", encoding="utf-8"))
    print(f"\n{s}: n_cal={d['n_cal']} n_dep={d['n_dep']} alpha={d['alpha']} block={d['block']}")
    noop = d["states"].get("opa_quant", {}).get("stale", {})
    base = None
    if noop:
        base = noop["cal_self_cov"] - noop["cov"]
    for e, st in d["states"].items():
        if e == "clean":
            continue
        a = st["stale"]["cal_self_cov"]
        t = st["stale"]["cov"]
        err = 100 * (a - t)
        err_c = 100 * (a - t - base) if base is not None else float("nan")
        print(f"  {e:14s} audit={a:.3f} true={t:.3f} err={err:+5.1f}pp"
              f" (noop-corrected {err_c:+5.1f}pp)  shift={st['stale']['cal_resid_shift']:+.4f}")
