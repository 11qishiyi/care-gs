"""Appendix-H figure: optimisation depth (39k vs 7k) and storage bit depth.

Left panel  : coverage loss at 30 % pruning for the four released 40k checkpoints and their
              7k twins (Appendix H table "Optimisation depth on the same scenes").
Right panel : coverage loss under SH quantisation at 8, 6 and 4 bits (four checkpoints),
              showing that the precision family is inert over a sixteen-fold storage range.

Reads results_v110/region/*.json (the 400-split campaign) and writes submission/final/fig_ext.pdf.
Usage: python tools/make_fig_ext.py
"""
from __future__ import annotations

import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SCENES = ["bicycle", "flowers", "stump", "treehill"]
LABEL = {"bicycle": "bicycle", "flowers": "flowers", "stump": "stump", "treehill": "treehill"}
BITS = [("quant8", "8 bit"), ("quant6", "6 bit"), ("quant4", "4 bit")]


def load_rows() -> dict:
    out = {}
    for f in glob.glob("results_v110/region/region_*.json"):
        scene = os.path.basename(f)[len("region_"):-len(".json")]
        blob = json.load(open(f, encoding="utf-8"))
        rows = blob["rows"] if isinstance(blob, dict) and "rows" in blob else blob
        for r in rows:
            if (r.get("gran") or r.get("granularity")) != "pixel":
                continue
            out[(scene, r["variant"])] = (-r["degradation_pp"],
                                          100 * abs(r["drop_lo"]),
                                          100 * abs(r["drop_hi"]))
    return out


def main() -> None:
    rows = load_rows()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 2.7), constrained_layout=True)

    # ---- left: 40k vs 7k at 30 % pruning
    x = np.arange(len(SCENES))
    l40, l7, e40, e7 = [], [], [], []
    for s in SCENES:
        d, lo, hi = rows[(s, "prune30")]
        d7, lo7, hi7 = rows[(s + "_i7k", "prune30")]
        l40.append(max(d, 0.0)); e40.append([max(0.0, d - min(lo, hi)), max(0.0, max(lo, hi) - d)])
        l7.append(max(d7, 0.0)); e7.append([max(0.0, d7 - min(lo7, hi7)), max(0.0, max(lo7, hi7) - d7)])
    w = 0.36
    ax1.bar(x - w / 2, l40, w, yerr=np.array(e40).T, capsize=2, label="40k checkpoint",
            color="#4c72b0", edgecolor="none")
    ax1.bar(x + w / 2, l7, w, yerr=np.array(e7).T, capsize=2, label="7k checkpoint",
            color="#dd8452", edgecolor="none")
    ax1.set_xticks(x, [LABEL[s] for s in SCENES], fontsize=8)
    ax1.set_ylabel("coverage loss at 30 % prune (pp)", fontsize=8)
    ax1.set_title("(a) optimisation depth, same scene", fontsize=9)
    ax1.tick_params(labelsize=8)
    ax1.legend(fontsize=7, frameon=False)
    ax1.set_ylim(bottom=0)

    # ---- right: bit depth
    xs = np.arange(len(BITS))
    for i, s in enumerate(SCENES):
        ys, es = [], []
        for var, _lab in BITS:
            d, lo, hi = rows[(s, var)]
            ys.append(d)
            es.append([max(0.0, d - min(lo, hi)), max(0.0, max(lo, hi) - d)])
        ax2.errorbar(xs + (i - 1.5) * 0.06, ys, yerr=np.array(es).T, marker="o", ms=3,
                     lw=0.9, capsize=2, label=LABEL[s], alpha=0.9)
    ax2.axhline(0.0, color="0.6", lw=0.7, ls=":")
    ax2.set_xticks(xs, [lab for _v, lab in BITS], fontsize=8)
    ax2.set_ylabel("coverage loss (pp)", fontsize=8)
    ax2.set_title("(b) storage precision", fontsize=9)
    ax2.tick_params(labelsize=8)
    ax2.set_ylim(-1.2, 1.2)
    ax2.legend(fontsize=6, frameon=False, ncol=2, loc="lower left")

    out = "submission/final/fig_ext.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()
