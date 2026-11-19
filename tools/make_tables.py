# -*- coding: utf-8 -*-
"""Build clean tables from the real-data calibration results."""
import json

FILES = [
    ("research/results_real/flowers_full.json", 0.10),
    ("research/results_real/treehill.json", 0.10),
    ("research/results_real/flowers_a20.json", 0.20),
    ("research/results_real/treehill_a20.json", 0.20),
]

print("=== CLEAN STATE (no edit) ===")
hdr = ("scene", "alpha", "naive", "scale-adapt", "region(pixel)", "region(cert)", "w_naive", "w_sadapt")
print("%-10s %5s %8s %12s %14s %13s %9s %10s" % hdr)
rows = []
for f, a in FILES:
    d = json.load(open(f, encoding="utf-8"))
    c = d["states"]["clean"]
    rows.append((d["scene"], d["alpha"], c["naive"]["cov"], c["scale_adaptive"]["cov"],
                 c["region_from_pixel"]["cov"], c["region_control"]["cert_rate"],
                 c["naive"]["width"], c["scale_adaptive"]["width"]))
for r in sorted(rows):
    print("%-10s %5.2f %8.3f %12.3f %14.3f %13.3f %9.4f %10.4f" % r)

print()
print("=== EDITS (alpha=0.10) ===")
for f in ("research/results_real/flowers_full.json", "research/results_real/treehill.json"):
    d = json.load(open(f, encoding="utf-8"))
    clean = d["states"]["clean"]["naive"]["cov"]
    print("-- %s (clean naive=%.3f, n_cal=%d, n_dep=%d) --"
          % (d["scene"], clean, d["n_cal"], d["n_dep"]))
    for k, v in d["states"].items():
        if k == "clean":
            continue
        st = v["stale"]["cov"]
        rc = v["recal"]["naive"]["cov"]
        rr = v.get("recal_clean")
        rc_cov = rr["naive"]["cov"] if rr else None
        print("   %-14s stale=%.3f (%+.1fpp)  recal=%.3f  recal_clean=%s  clean_frac=%.2f"
              % (k, st, 100 * (st - clean), rc,
                 ("%.3f" % rc_cov) if rc_cov is not None else "-",
                 v["curation"]["frac_clean"]))
    print()

print("=== EDITS (alpha=0.20) ===")
for f in ("research/results_real/flowers_a20.json", "research/results_real/treehill_a20.json"):
    d = json.load(open(f, encoding="utf-8"))
    clean = d["states"]["clean"]["naive"]["cov"]
    print("-- %s (clean naive=%.3f, target 0.80) --" % (d["scene"], clean))
    for k, v in d["states"].items():
        if k == "clean":
            continue
        st = v["stale"]["cov"]
        rc = v["recal"]["naive"]["cov"]
        print("   %-14s stale=%.3f (%+.1fpp)  recal=%.3f" % (k, st, 100 * (st - clean), rc))
