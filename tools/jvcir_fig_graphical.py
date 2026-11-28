"""Graphical abstract for the JVCIR submission (uploaded separately, not part of the manuscript).

Read left to right: the asset, the container that makes quantisation worth spending, the audit that re-measures the
shipped certificate on the views the asset already carries, and the planner that turns a tolerance into an operating
point. The banner carries the positioning: the action family, not its strength, sets the admissible rate, and a decibel
budget does not imply a coverage budget.

Elsevier asks for >= 1328 px width and legibility at 13 cm. The canvas is 7.0 in wide at 300 dpi (2043 px), so 10 pt body
text prints at 10 * 13 cm / 7 in = 7.3 pt at the size the abstract is actually read at. Every string is measured against
its box here and the script fails rather than emit overlapping text.

    python tools/jvcir_fig_graphical.py
"""
from __future__ import annotations

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

OUT = "figures_j"
C_QFP = "#1f4e79"
C_GREY = "#5a6570"
C_BG = "#eef2f6"

W, H = 7.0, 3.45
X0, GAP, BW = 0.012, 0.014, 0.2295
BH = 0.520
Y_BOX = 0.345
Y_BANNER, H_BANNER = 0.040, 0.262
FS_TITLE, FS_BODY, FS_HEAD, FS_BANNER = 11.0, 10.0, 13.5, 10.0
PAD_IN = 0.012 * W

BOXES = [
    ("asset", C_GREY, C_BG, [
        "1447 MB fp32 PLY",
        "6 M Gaussians",
        "ships with its",
        "calibration views",
        "and one quantile $q$",
    ]),
    (("1 $\\cdot$ shared-basis", "container"), C_QFP, "white", [
        "rank-16 SH basis",
        "smallest-three quats",
        "per-stream alphabets",
        "83.41 MB at 0.44 dB",
        "17.35$\\times$ smaller",
    ]),
    (("2 $\\cdot$ audit, not", "assumption"), C_QFP, "white", [
        "re-render the shipped",
        "calibration views",
        "",
        "2.0 pp mean error",
        "56/56 decided",
        "0 false accepts",
    ]),
    (("3 $\\cdot$ coverage-aware", "planner"), C_QFP, "white", [
        "tolerance $\\varepsilon$ + audit",
        "$\\rightarrow$ operating point",
        "",
        "quantise 8.97–15.78$\\times$",
        "prune: none admissible",
        "prior misses 2–3/6",
    ]),
]

BANNER = [
    "Across 6 scene-checkpoints at a one-point coverage tolerance the action family decides the rate:",
    "quantisation reaches 8.97–15.78$\\times$, pruning has no admissible point. At a matched rate pruning costs",
    "12.7–23.2 coverage points, quantisation 0.72–0.95 — and 0.10 dB of PSNR can hide 6.2 coverage points.",
]


def main() -> None:
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])   # the axes must fill the canvas, or every coordinate is scaled
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="none", zorder=0))
    renderer = fig.canvas.get_renderer()

    def check(s: str, pt: float, max_in: float, weight: str = "normal") -> None:
        t = ax.text(0.5, 0.5, s, fontsize=pt, fontweight=weight)
        w_in = t.get_window_extent(renderer=renderer).width / fig.dpi
        t.remove()
        if w_in > max_in:
            raise SystemExit(f"string too wide ({w_in:.2f} in > {max_in:.2f} in): {s!r}")

    box_text_in = BW * W - 2 * PAD_IN
    banner_text_in = (1 - 2 * X0) * W - 2 * PAD_IN

    ax.text(X0, 0.975,
            "CARE-GS: rate reduction you can certify for a shipped 3D Gaussian Splatting asset",
            fontsize=FS_HEAD, fontweight="bold", color="#111111", va="top")
    check("CARE-GS: rate reduction you can certify for a shipped 3D Gaussian Splatting asset",
          FS_HEAD, W - 2 * X0 * W, "bold")

    for i, (title, edge, fill, lines) in enumerate(BOXES):
        x = X0 + i * (BW + GAP)
        ax.add_patch(FancyBboxPatch((x, Y_BOX), BW, BH, boxstyle="round,pad=0.006,rounding_size=0.012",
                                    linewidth=1.0, edgecolor=edge, facecolor=fill, zorder=2))
        titles = (title,) if isinstance(title, str) else title
        for k, tt in enumerate(titles):
            check(tt, FS_TITLE, box_text_in, "bold")
            ax.text(x + PAD_IN / W, Y_BOX + BH - 0.030 - k * 0.050, tt, fontsize=FS_TITLE,
                    fontweight="bold", color=edge, va="top", ha="left", zorder=3)
        y_first = Y_BOX + BH - 0.030 - 0.050 * len(titles) - 0.030
        for k, ln in enumerate(lines):
            if ln:
                check(ln, FS_BODY, box_text_in)
            ax.text(x + PAD_IN / W, y_first - k * 0.058, ln, fontsize=FS_BODY, color="#1b1b1b",
                    va="top", ha="left", zorder=3)

    y_mid = Y_BOX + BH / 2
    for i in range(3):
        x0 = X0 + i * (BW + GAP) + BW
        ax.add_patch(FancyArrowPatch((x0 + 0.001, y_mid), (x0 + GAP - 0.001, y_mid),
                                     arrowstyle="-|>", mutation_scale=9, linewidth=1.0,
                                     color=C_GREY, zorder=1))

    ax.add_patch(FancyBboxPatch((X0, Y_BANNER), 1 - 2 * X0, H_BANNER,
                                boxstyle="round,pad=0.006,rounding_size=0.012",
                                linewidth=0, facecolor=C_BG, zorder=2))
    for k, ln in enumerate(BANNER):
        check(ln, FS_BANNER, banner_text_in)
        ax.text(X0 + PAD_IN / W, Y_BANNER + H_BANNER - 0.055 - k * 0.066, ln,
                fontsize=FS_BANNER, color="#16202a", va="top", zorder=3)

    fig.savefig(f"{OUT}/graphical_abstract.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(f"{OUT}/graphical_abstract.png", dpi=300, bbox_inches="tight", pad_inches=0.03)
    print(f"wrote {OUT}/graphical_abstract.pdf and .png "
          f"({FS_BODY} pt body = {FS_BODY * 13.0 / 2.54 / W:.1f} pt at 13 cm)")


if __name__ == "__main__":
    main()