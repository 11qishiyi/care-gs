# -*- coding: utf-8 -*-
"""Fit and print the composition scaling law from the two scenes."""
import json
import math

for s in ["flowers", "treehill"]:
    d = json.load(open(f"research/results_v4/compose_{s}.json", encoding="utf-8"))
    rows = [r for r in d["rows"] if "block" in r]
    k = [r["K"] for r in rows]
    inf = [r["block"]["inflation"] for r in rows]
    cov = [r["block"]["coverage"] for r in rows]
    slope = math.log(inf[-1] / inf[0]) / math.log(k[-1] / k[0])
    print(f"{s}: q_atom={d['q_atom']:.3f} atom_cov={d['atom_coverage']:.3f} "
          f"corr_len={d['corr_len_px']:.1f}px")
    print(f"   block coverage: " + "  ".join(f"K={a}:{b:.3f}" for a, b in zip(k, cov)))
    print(f"   inflation     : " + "  ".join(f"K={a}:{b:.1f}x" for a, b in zip(k, inf)))
    print(f"   log-log slope : {slope:.3f}   (Bonferroni would be slope 1 -> Kx)")
    paths = [r for r in d["rows"] if "path" in r]
    print("   path coverage : " + "  ".join(
        f"K={r['K']}:{r['path']['coverage']:.3f}" for r in paths))
    print()
