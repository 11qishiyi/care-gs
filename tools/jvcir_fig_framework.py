"""Fig. 1 — the CARE-GS framework diagram (JVCIR wants Fig. 1 to be the pipeline, not a result).

Three rows: what the issuer does, what the recipient does, and the comparison that lets the two be
reconciled. The planner sits at the end of the issuer row and is closed by the decision at the end of
the comparison row, which is the paper's claim: the planner is valid only because the audit can be run
by whoever holds the asset.

Outputs `figures_j/fig1_framework.pdf` (vector) and a 300 dpi PNG preview.

    python tools/jvcir_fig_framework.py
"""
from __future__ import annotations

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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("figures_j")
W, H = 7.2, 4.15
FS = 6.6

C_ISSUER = "#dbe8f7"
C_FILE = "#f6e3c5"
C_RECIP = "#dff0dd"
C_CERT = "#efe0ef"
C_PLAN = "#f7d9d9"
EDGE = "#333333"

BW, GAP, X0 = 0.158, 0.033, 0.012
ROWS = {"issuer": 0.735, "recipient": 0.415, "comparison": 0.095}
BH = 0.175


def box(ax, i, row, text, fc, bold=False):
    x = X0 + i * (BW + GAP)
    y = ROWS[row]
    ax.add_patch(FancyBboxPatch((x, y), BW, BH, boxstyle="round,pad=0.010,rounding_size=0.018",
                                linewidth=0.7, edgecolor=EDGE, facecolor=fc, zorder=2))
    ax.text(x + BW / 2, y + BH / 2, text, ha="center", va="center", fontsize=FS, zorder=3,
            fontweight=("bold" if bold else "normal"), linespacing=1.3)
    return (x, y)


def harrow(ax, i, row, ls="-"):
    x0 = X0 + i * (BW + GAP) + BW
    y = ROWS[row] + BH / 2
    ax.add_patch(FancyArrowPatch((x0, y), (x0 + GAP, y), arrowstyle="-|>", mutation_scale=6,
                                 linewidth=0.8, linestyle=ls, color=EDGE, shrinkA=0.5, shrinkB=0.5, zorder=1))


def arrow(ax, p0, p1, ls="--", rad=0.0, lw=0.8):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=6, linewidth=lw,
                                 linestyle=ls, color=EDGE, shrinkA=2.0, shrinkB=2.0,
                                 connectionstyle=f"arc3,rad={rad}", zorder=1))


def lane_label(ax, row, text, color):
    y = ROWS[row] + BH + 0.022
    ax.text(X0, y, text, fontsize=FS + 0.4, ha="left", va="bottom", color=color, fontweight="bold")


def main() -> None:
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # ---------------- issuer row
    box(ax, 0, "issuer", "trained 3DGS\nasset (PLY)", C_ISSUER)
    box(ax, 1, "issuer", "shared-basis\ncontainer", C_ISSUER, bold=True)
    box(ax, 2, "issuer", "coded asset\n83.41 MB", C_FILE, bold=True)
    box(ax, 3, "issuer", "certificate\n$\\alpha$, $q$, views", C_CERT, bold=True)
    box(ax, 4, "issuer", "planner\n$f$, colour, geoms", C_PLAN, bold=True)
    for i in range(4):
        harrow(ax, i, "issuer")
    lane_label(ax, "issuer", "issuer  (has the labels, runs once)", "#1f4e79")

    # ---------------- recipient row
    box(ax, 2, "recipient", "decoder\n(tensors)", C_FILE)
    box(ax, 3, "recipient", "rendered\nviews", C_RECIP)
    box(ax, 4, "recipient", "edit / recompress\n(prune, requantise)", C_RECIP, bold=True)
    for i in (2, 3):
        harrow(ax, i, "recipient")
    lane_label(ax, "recipient", "recipient  (no labels, one render pass)", "#1e5c2e")

    # ---------------- comparison row
    box(ax, 0, "comparison", "audit: re-render\nshipped views", C_PLAN, bold=True)
    box(ax, 1, "comparison", "measured loss\n$\\Delta$ coverage (pp)", C_CERT)
    box(ax, 2, "comparison", "decision\nship iff $\\Delta \\leq \\varepsilon$", C_PLAN, bold=True)
    box(ax, 3, "comparison", "envelope\nloss $\\leq$ KS $+$ slack", C_CERT)
    box(ax, 4, "comparison", "re-certify\nrecalibrate $q$, 2 views", C_CERT)
    for i in range(4):
        harrow(ax, i, "comparison")
    lane_label(ax, "comparison", "reconciliation  (no new labels, no issuer pipeline)", "#6b2f6b")

    # ---------------- vertical hops
    x2 = X0 + 2 * (BW + GAP) + BW / 2
    arrow(ax, (x2, ROWS["issuer"]), (x2, ROWS["recipient"] + BH))
    x4 = X0 + 4 * (BW + GAP) + BW / 2
    arrow(ax, (x4, ROWS["recipient"]), (x4, ROWS["comparison"] + BH))

    # the decision closes the loop back into the planner, routed under the comparison row
    xdec = x2
    xpr = X0 + 4 * (BW + GAP) + BW
    ybot = ROWS["comparison"]
    ymid = 0.062
    ypr = ROWS["issuer"] + BH / 2
    path = [(xdec, ybot), (xdec, ymid), (0.992, ymid), (0.992, ypr), (xpr, ypr)]
    for (x0, y0), (x1, y1) in zip(path[:-2], path[1:-1]):
        ax.plot([x0, x1], [y0, y1], ls="--", lw=0.7, color=EDGE, zorder=1)
    ax.add_patch(FancyArrowPatch(path[-2], path[-1], arrowstyle="-|>", mutation_scale=6, linewidth=0.7,
                                 linestyle="--", color=EDGE, shrinkA=0.0, shrinkB=1.0, zorder=1))

    ax.text(0.5, 0.012,
            "the planner is admissible only because the audit needs nothing the recipient does not already hold",
            fontsize=FS - 0.4, ha="center", style="italic", color="#333333")

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig1_framework.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / "fig1_framework.png", dpi=360, bbox_inches="tight", pad_inches=0.02)
    print(f"wrote {OUT/'fig1_framework.pdf'} and .png")


if __name__ == "__main__":
    main()
