"""Graphical abstract for the JVCIR submission (uploaded separately, not part of the manuscript).

One panel, read left to right: the asset, the container that makes quantisation worth spending, the certificate and the
audit that re-measures it on the views the asset already carries, and the planner that turns a tolerance into an
operating point. The two numbers on the banner are the ones that decide the paper's positioning: the action family, not
its strength, sets the admissible rate, and a decibel budget does not imply a coverage budget.

Elsevier asks for >= 1328 px width and legibility at 13 cm; the PNG is rendered at 300 dpi (about 4000 px wide).

    python tools/jvcir_fig_graphical.py
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = "figures_j"
C_QFP = "#1f4e79"
C_GEO = "#c0392b"
C_GREY = "#5a6570"
C_BG = "#eef2f6"


def box(ax, x, y, w, h, title, lines, edge, fill="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                linewidth=1.1, edgecolor=edge, facecolor=fill, zorder=2))
    ax.text(x + 0.012, y + h - 0.030, title, fontsize=9.5, fontweight="bold", color=edge,
            va="top", ha="left", zorder=3)
    for i, ln in enumerate(lines):
        ax.text(x + 0.012, y + h - 0.088 - i * 0.046, ln, fontsize=8.0, color="#1b1b1b",
                va="top", ha="left", zorder=3)


def arrow(ax, x0, y0, x1, y1, colour=C_GREY):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14,
                                 linewidth=1.2, color=colour, zorder=1,
                                 shrinkA=0, shrinkB=0))


def main() -> None:
    fig, ax = plt.subplots(figsize=(13.2, 4.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="none", zorder=0))

    ax.text(0.012, 0.995, "CARE-GS: rate reduction you can certify for a shipped 3D Gaussian Splatting asset",
            fontsize=11.5, fontweight="bold", color="#111111", va="top")

    box(ax, 0.012, 0.40, 0.175, 0.46, "asset", [
        "1447 MB, fp32 PLY",
        "6 M Gaussians",
        "ships with its",
        "calibration views",
        "and a quantile q",
    ], C_GREY, C_BG)

    box(ax, 0.215, 0.40, 0.255, 0.46, "1 · shared-basis container", [
        "one rank-16 SH basis",
        "  per asset (45 coeffs)",
        "smallest-three quats",
        "per-stream alphabets",
        "Morton order + zstd",
        "",
        "83.41 MB at −0.04 dB",
        "17.35× smaller",
    ], C_QFP)

    box(ax, 0.498, 0.40, 0.235, 0.46, "2 · audit, not assumption", [
        "recipient re-renders the",
        "  shipped calibration views",
        "counts residuals under the",
        "  unchanged q",
        "",
        "2.0 pp mean error",
        "56/56 cells decided",
        "0 false accepts",
    ], C_QFP)

    box(ax, 0.761, 0.40, 0.227, 0.46, "3 · coverage-aware planner", [
        "tolerance ε → operating point",
        "choose the ACTION FAMILY:",
        "  quantise  8.97–15.78×",
        "  prune     no admissible point",
        "",
        "the prior alone violates ε",
        "  on 2–3 of 6 assets;",
        "the audit is the acceptance test",
    ], C_QFP)

    for x0, x1 in ((0.187, 0.213), (0.470, 0.496), (0.733, 0.759)):
        arrow(ax, x0, 0.63, x1, 0.63)

    banner = ["Across 6 scene-checkpoints, at a one-point coverage tolerance, the action family decides the rate:",
              "quantisation reaches 8.97–15.78×, pruning nothing. At a matched rate pruning costs 12.7–23.2 points,",
              "quantisation 0.7–0.95 — and 0.10 dB of PSNR can hide 6.2 coverage points."]
    ax.add_patch(FancyBboxPatch((0.012, 0.045), 0.976, 0.31, boxstyle="round,pad=0.010,rounding_size=0.02",
                                linewidth=0, facecolor=C_BG, zorder=2))
    for i, ln in enumerate(banner):
        ax.text(0.028, 0.255 - i * 0.058, ln, fontsize=8.6, color="#16202a", va="center", zorder=3)

    fig.savefig(f"{OUT}/graphical_abstract.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(f"{OUT}/graphical_abstract.png", dpi=300, bbox_inches="tight", pad_inches=0.03)
    print(f"wrote {OUT}/graphical_abstract.pdf and .png")


if __name__ == "__main__":
    main()
