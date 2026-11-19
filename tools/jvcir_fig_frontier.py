"""Fig. 2 — rate--reliability: what each action family buys, and the pruning dose--response.

Panel A plots measured rate against measured coverage loss for both action families, over the six
usable scene-checkpoints of `m5_rd_v2`; the shaded band is the one-point tolerance the planner is
held to. Panel B is the same pruning family against retained fraction, i.e. the dose--response the
paper's admissibility claim rests on.

Everything is read from `experiments/artifacts/a4/m5_rd_v2.json` (rate, drop_pp, family) and the
usable set from `j1_reliability.json`, so the figure and Table 3 cannot disagree.

    python tools/jvcir_fig_frontier.py
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
EPS = 1.0
C_PRUNE = "#c0392b"
C_QFP = "#1f4e79"


def main() -> None:
    grid = json.loads((A4 / "m5_rd_v2.json").read_text(encoding="utf-8"))
    usable = json.loads((A4 / "j1_reliability.json").read_text(encoding="utf-8"))["keep"]
    scenes = {s["scene"]: s for s in grid["scenes"] if s["scene"] in usable}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.85), gridspec_kw={"width_ratios": [1.25, 1]})

    # ---------------- panel A: loss vs rate, both families
    bins = np.logspace(np.log10(1.0), np.log10(30.0), 13)
    centres = np.sqrt(bins[:-1] * bins[1:])
    for fam, colour, label in (("prune", C_PRUNE, "pruning (deleting primitives)"),
                               ("qfp", C_QFP, "quantisation (this container)")):
        xs, ys = [], []
        for sc in scenes.values():
            pts = [(r["rate"], -r["drop_pp"]) for r in sc["rows"] if r.get("family") == fam]
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
            ax1.scatter([p[0] for p in pts], [p[1] for p in pts], s=7, color=colour, alpha=0.30,
                        linewidths=0, zorder=3)
        xs, ys = np.asarray(xs), np.asarray(ys)
        med = []
        for lo_b, hi_b in zip(bins[:-1], bins[1:]):
            sel = (xs >= lo_b) & (xs < hi_b)
            med.append(float(np.median(ys[sel])) if sel.any() else np.nan)
        ax1.plot(centres, med, color=colour, lw=1.1, marker="o", ms=2.6, label=label, zorder=4)

    ax1.axhspan(0, EPS, color="#888888", alpha=0.16, zorder=0)
    ax1.axhline(EPS, color="#555555", lw=0.6, ls="--", zorder=1)
    ax1.text(13.2, 4.2, r"tolerance $\varepsilon = 1$ pp", fontsize=5.4, color="#444444")
    ax1.set_xscale("log")
    ax1.set_xlabel("measured rate ($\\times$ vs fp32 PLY)", fontsize=6.2)
    ax1.set_ylabel("coverage loss (pp)", fontsize=6.2)
    ax1.set_ylim(-0.6, 26)
    ax1.set_xlim(1.0, 26)
    ax1.tick_params(labelsize=5.4, length=2)
    ax1.legend(fontsize=5.2, frameon=False, loc="upper left")
    ax1.set_title("A  the admissible set is set by the action family", fontsize=6.4, loc="left")

    # ---------------- panel B: pruning dose--response
    variants = sorted({r["variant"] for sc in scenes.values() for r in sc["rows"]
                       if r.get("family") == "prune"}, key=lambda v: int(v[1:]))
    med, lo, hi, fr = [], [], [], []
    for v in variants:
        vals = [-(r["drop_pp"]) for sc in scenes.values() for r in sc["rows"]
                if r.get("family") == "prune" and r["variant"] == v]
        fr.append(int(v[1:]))
        med.append(float(np.median(vals)))
        lo.append(float(np.percentile(vals, 25)))
        hi.append(float(np.percentile(vals, 75)))
    ax2.fill_between(fr, lo, hi, color=C_PRUNE, alpha=0.16, linewidth=0)
    ax2.plot(fr, med, color=C_PRUNE, lw=1.1, marker="o", ms=3)
    ax2.axhline(EPS, color="#555555", lw=0.6, ls="--")
    ax2.set_xscale("log")
    ax2.set_xticks(fr)
    ax2.set_xticklabels([f"{k}%" for k in fr], fontsize=5.2)
    ax2.set_xlabel("primitives retained", fontsize=6.2)
    ax2.set_ylabel("coverage loss (pp)", fontsize=6.2)
    ax2.set_ylim(-0.6, 28)
    ax2.set_xlim(fr[0] * 0.85, fr[-1] * 1.15)
    ax2.tick_params(labelsize=5.4, length=2)
    ax2.set_title("B  deleting primitives: median and IQR, six assets", fontsize=6.4, loc="left")
    ax2.text(fr[0], 0.55, "no pruning setting is inside the tolerance",
             fontsize=5.0, color="#444444")

    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.3)

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig2_frontier.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / "fig2_frontier.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(f"wrote {OUT/'fig2_frontier.pdf'} and .png")


if __name__ == "__main__":
    main()
