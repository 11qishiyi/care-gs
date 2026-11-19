"""Analyse the label-free self-coverage diagnostic against true post-edit coverage."""
import json
import numpy as np

FILES = ["research/results_v3/sc_flowers.json", "research/results_v3/sc_treehill.json"]

rows = []
for f in FILES:
    d = json.load(open(f, encoding="utf-8"))
    clean_cov = d["states"]["clean"]["naive"]["cov"]
    # baseline cal->deploy offset estimated from a near-no-op edit (opa_quant)
    noop = d["states"].get("opa_quant")
    base = (noop["stale"]["cal_self_cov"] - noop["stale"]["cov"]) if noop else 0.0
    for e, st in d["states"].items():
        if e == "clean":
            continue
        rows.append(dict(scene=d["scene"], edit=e, clean=clean_cov,
                         cal_self=st["stale"]["cal_self_cov"],
                         stale=st["stale"]["cov"],
                         recal=st["recal"]["naive"]["cov"],
                         base=base))

print("=== label-free self-coverage vs true post-edit coverage ===")
print(f"{'scene':10s}{'edit':12s}{'cal_self':>10s}{'stale':>8s}{'raw err':>9s}{'base':>7s}{'corr err':>10s}")
errs_raw, errs_corr = [], []
for r in sorted(rows, key=lambda x: (x["scene"], x["edit"])):
    e_raw = 100 * (r["cal_self"] - r["stale"])
    e_cor = 100 * (r["cal_self"] - r["stale"] - r["base"])
    errs_raw.append(e_raw); errs_corr.append(e_cor)
    print(f"{r['scene']:10s}{r['edit']:12s}{r['cal_self']:10.3f}{r['stale']:8.3f}"
          f"{e_raw:+9.1f}{100*r['base']:+7.1f}{e_cor:+10.1f}")

errs_raw = np.array(errs_raw); errs_corr = np.array(errs_corr)
print(f"\nraw error   : mean |err| {np.abs(errs_raw).mean():.1f}pp  max {np.abs(errs_raw).max():.1f}pp")
print(f"baseline-corrected: mean |err| {np.abs(errs_corr).mean():.1f}pp  "
      f"max {np.abs(errs_corr).max():.1f}pp")

print("\n=== does recalibration recover? (recal vs clean) ===")
for r in sorted(rows, key=lambda x: (x["scene"], x["edit"])):
    print(f"{r['scene']:10s}{r['edit']:12s} clean={r['clean']:.3f} recal={r['recal']:.3f} "
          f"delta={100*(r['recal']-r['clean']):+.1f}pp")
