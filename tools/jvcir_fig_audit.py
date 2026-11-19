"""Fig. 4 --- does the audit decide the tolerance? Predicted loss against measured loss, 56 cells.

Panel A is the audit (re-render the shipped calibration views under the unchanged quantile); panel B is the
cross-asset prior the planner would use without it. Both are plotted against the measured loss on all held-out
views, so the two panels are directly comparable. The shaded corner is the region a decision rule must not enter:
the rule accepts (predicted loss <= eps) while the asset actually violates the tolerance.

Panel A carries the audit's own error as a vertical bar: the per-cell mean absolute error of the audit estimate
over the 400 random calibration/deployment splits of `results_v120/audit_bound_nobonsai.json`. Panel B has no
such bar, because the prior is not a measurement.

Reads `experiments/artifacts/a4/j2_audit_decision.json` (`per_cell`) joined to that source for the error bars,
so the figure and the decision table cannot disagree.

    python tools/jvcir_fig_audit.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

A4 = Path("experiments/artifacts/a4")
OUT = Path("figures_j")
SRC = Path("results_v120/audit_bound_nobonsai.json")
EPS = 1.0
C_GEO = "#c0392b"   # geometric edits: deleting primitives
C_ATT = "#1f4e79"   # attribute edits: quantising colour / geometry

GEOMETRIC = {"prune30", "prune50", "pup30"}


def main() -> None:
    d = json.loads((A4 / "j2_audit_decision.json").read_text(encoding="utf-8"))
    cells = d["per_cell"]
    err = {}
    if SRC.exists():
        for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"]:
            err[(r["scene"], r["variant"])] = (r["audit_mae_pp"], r["audit_abs_p95_pp"])

    truth = np.array([c["truth"] for c in cells])
    audit = np.array([c["audit"] for c in cells])
    prior = np.array([c["prior"] for c in cells])
    fam = np.array(["geo" if c["variant"] in GEOMETRIC else "att" for c in cells])
    bar = np.array([err.get((c["scene"], c["variant"]), (0.0, 0.0))[0] for c in cells])

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharex=True, sharey=True)
    lo, hi = -3.0, 30.0

    for ax, pred, label in ((axes[0], audit, "A  audit on the shipped calibration views"),
                            (axes[1], prior, "B  cross-asset prior (no measurement)")):
        # the region a decision rule must not enter: accepted by the rule, outside the tolerance
        ax.add_patch(plt.Rectangle((EPS, lo), hi - EPS, EPS - lo, facecolor="#c0392b", alpha=0.08,
                                   edgecolor="none", zorder=0))
        for f, colour, name in (("geo", C_GEO, "deleting primitives"), ("att", C_ATT, "quantising attributes")):
            m = fam == f
            ax.scatter(truth[m], pred[m], s=16, color=colour, alpha=0.85, linewidths=0.4,
                       edgecolors="white", zorder=3, label=name)
        ax.plot([lo, hi], [lo, hi], color="#444444", lw=0.7, ls="-", zorder=2)
        ax.fill_between([lo, hi], [lo - EPS, hi - EPS], [lo + EPS, hi + EPS], color="#444444", alpha=0.08,
                        linewidth=0, zorder=1)
        ax.axhline(EPS, color="#555555", lw=0.6, ls="--", zorder=1)
        ax.axvline(EPS, color="#555555", lw=0.6, ls="--", zorder=1)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, 22)
        ax.set_xlabel("measured loss, all held-out views (pp)", fontsize=6.2)
        ax.tick_params(labelsize=5.4, length=2)
        ax.set_title(label, fontsize=6.4, loc="left")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    axes[0].errorbar(truth, audit, yerr=bar, fmt="none", ecolor="#1f4e79", elinewidth=0.5, capsize=0.8,
                     alpha=0.5, zorder=2)
    axes[0].set_ylabel("loss predicted by the rule (pp)", fontsize=6.2)
    axes[0].legend(fontsize=5.2, frameon=False, loc="upper left", handletextpad=0.3, borderpad=0.1)
    axes[0].text(8.6, EPS + 1.15, "empty: the audit\nnever lands here",
                 fontsize=5.0, color="#7b241c", va="bottom")
    axes[1].text(EPS + 9.0, EPS + 0.45, "accepted by the rule,\nbut the asset misses\nthe tolerance",
                 fontsize=5.0, color="#7b241c", va="bottom")
    for ax in axes:
        ax.text(hi - 2.6, EPS + 0.30, r"$\varepsilon = 1$ pp", fontsize=5.2, color="#444444", ha="right")

    fig.tight_layout(pad=0.3)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig3_audit.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / "fig3_audit.png", dpi=300, bbox_inches="tight", pad_inches=0.02)

    # provenance for anything the caption quotes
    mae = float(np.mean(bar))
    (A4 / "j5_fig_audit.json").write_text(json.dumps({
        "source": "experiments/artifacts/a4/j2_audit_decision.json + results_v120/audit_bound_nobonsai.json",
        "n_cells": len(cells), "eps": EPS,
        "audit_mae_pp_mean": round(mae, 2), "audit_mae_pp_max": round(float(np.max(bar)), 2),
        "false_accept_audit": int(((audit <= EPS) & (truth > EPS)).sum()),
        "false_accept_prior": int(((prior <= EPS) & (truth > EPS)).sum()),
        "false_reject_audit": int(((audit > EPS) & (truth <= EPS)).sum()),
        "false_reject_prior": int(((prior > EPS) & (truth <= EPS)).sum()),
    }, indent=1), encoding="utf-8")
    print(f"wrote {OUT/'fig3_audit.pdf'} and .png  |  audit MAE {mae:.2f} pp (max {np.max(bar):.2f}); "
          f"false accepts audit {int(((audit <= EPS) & (truth > EPS)).sum())}, "
          f"prior {int(((prior <= EPS) & (truth > EPS)).sum())} of {len(cells)}")


if __name__ == "__main__":
    main()
