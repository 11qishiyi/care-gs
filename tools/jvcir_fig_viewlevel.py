"""Fig. 5 — the shipped quantile against rate: pixel coverage, view coverage, and the gap.

Two panels, both read from `experiments/artifacts/a4/j4_report.json`:
  A  coverage of the *unchanged* shipped quantile as the container spends fewer bytes: the solid line is
     the fraction of held-out pixels covered, the dashed line the fraction of held-out views whose pixels
     are at least 90 % covered.
  B  the distance between those two numbers, which is what a pixel-level certificate does not say.

    python tools/jvcir_fig_viewlevel.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Elsevier asks for Times/Arial in artwork; STIX keeps the mathtext in the same serif family.
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,
})

A4 = Path("experiments/artifacts/a4")
OUT = Path("figures_j")
COLOURS = {"bicycle": "#1f4e79", "stump": "#c0392b"}


def main() -> None:
    d = json.loads((A4 / "j4_report.json").read_text(encoding="utf-8"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw={"width_ratios": [1.15, 1]})

    for sc in d["scenes"]:
        rows = [r for r in sc["rows"] if r["rate"]]
        rows.sort(key=lambda r: r["rate"])
        x = [r["rate"] for r in rows]
        pix = [r["cov_pixel"] for r in rows]
        view = [r["cov_view"] for r in rows]
        c = COLOURS.get(sc["scene"], "#444444")
        ax1.plot(x, pix, color=c, lw=1.2, marker="o", ms=3, label=f"{sc['scene']}, pixels")
        ax1.plot(x, view, color=c, lw=1.2, marker="s", ms=3, ls="--", label=f"{sc['scene']}, views")
        ax2.plot(x, [r["gap_pp"] for r in rows], color=c, lw=1.2, marker="o", ms=3, label=sc["scene"])

    ax1.axhline(0.90, color="#555555", lw=0.6, ls=":")
    ax1.text(1.05, 0.952, "nominal coverage", fontsize=7.5, color="#444444", va="bottom")
    ax1.set_xlabel("rate ($\\times$ vs fp32 PLY)", fontsize=8.8)
    ax1.set_ylabel("coverage of the shipped $q$", fontsize=8.8)
    ax1.set_ylim(0.0, 1.0)
    ax1.set_xscale("log")
    ax1.set_xticks([1, 2, 5, 10])
    ax1.set_xticklabels(["1", "2", "5", "10"])
    ax1.tick_params(labelsize=7.7, length=2.6)
    ax1.legend(fontsize=7.2, frameon=False, loc="lower left", ncol=1)
    ax1.set_title("A  the same $q$, per pixel and per view", fontsize=9.1, loc="left")

    ax2.set_xlabel("rate ($\\times$ vs fp32 PLY)", fontsize=8.8)
    ax2.set_ylabel("pixel coverage $-$ view coverage (pp)", fontsize=8.8)
    ax2.set_xscale("log")
    ax2.set_xticks([1, 2, 5, 10])
    ax2.set_xticklabels(["1", "2", "5", "10"])
    ax2.tick_params(labelsize=7.7, length=2.6)
    ax2.legend(fontsize=7.5, frameon=False)
    ax2.set_title("B  what a pixel-level certificate does not say", fontsize=9.1, loc="left")

    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.3)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig5_viewlevel.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / "fig5_viewlevel.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(f"wrote {OUT/'fig5_viewlevel.pdf'} and .png")


if __name__ == "__main__":
    main()
