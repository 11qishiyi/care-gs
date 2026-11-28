"""Fig. 6 --- the qualitative grid: ground truth, the clean model, two container points, one prune.

Everything here is mechanical, because a qualitative figure is where cherry-picking usually enters:

  * the view is the one `experiments/j5_render.py` picked by the pre-registered rule (median clean PSNR over the
    held-out views), and the manifest records its rank;
  * the magnification window is chosen on the **ground truth** by maximum gradient energy over a fixed-size window
    with a fixed stride (`experiments/j5_pack.py`, same rule as `J5_PLAN.md`), so the codec's output never
    influences which patch is shown;
  * every label (rate, PSNR, SSIM, LPIPS) is read from `_pull_j5/j5_pack.json`, which the node wrote from the
    render, and the caption quotes the same file.

    python tools/jvcir_fig_qual.py            # needs _pull_j5/ (j5_pack.json + patches; see tools/pull_j5.ps1)
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
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image

PULL = Path("_pull_j5")
OUT = Path("figures_j")
A4 = Path("experiments/artifacts/a4")
ARM_NAMES = {"clean": "clean", "p50": "prune 50% (Fisher)"}
ERR_GAIN = 8


MIN_PX = 330          # 330 px at the ~1.1 in panel width is 300 dpi on the printed page


def load(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    if img.width < MIN_PX:
        img = img.resize((MIN_PX, MIN_PX), Image.LANCZOS)
    return np.asarray(img, dtype=np.float32) / 255.0


def pretty(name: str, arm: dict) -> str:
    label = ARM_NAMES.get(name, "ours" if arm.get("family") == "qfp" else name)
    return f"{label}\n{arm['rate']:.2f}x · {arm['psnr']:.2f} dB"


def main() -> None:
    man = json.loads((PULL / "j5_pack.json").read_text(encoding="utf-8"))
    arms = list(man["scenes"][0]["arms"].keys())
    ncol = 2 + len(arms)
    nrow = 2 * len(man["scenes"])
    fig, axes = plt.subplots(nrow, ncol, figsize=(7.3, 1.06 * nrow + 1.15),
                             gridspec_kw={"width_ratios": [0.9] + [0.62] * (ncol - 1)})
    if nrow == 1:
        axes = np.asarray([axes])

    for si, sc in enumerate(man["scenes"]):
        r = 2 * si
        full = load(PULL / sc["full"])
        sx = full.shape[1] / float(sc["width"])
        sy = full.shape[0] / float(sc["height"])
        ax = axes[r, 0]
        ax.imshow(full)
        ax.add_patch(Rectangle((sc["crop"]["x"] * sx, sc["crop"]["y"] * sy),
                               sc["crop"]["size"] * sx, sc["crop"]["size"] * sy,
                               fill=False, edgecolor="#c0392b", lw=0.9))
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_linewidth(0.4); s.set_color("#888888")


        cells = [("GT", load(PULL / f"{sc['scene']}_gt_patch.png"))]
        for name in arms:
            arm = sc["arms"][name]
            cells.append((pretty(name, arm), load(PULL / arm["png"])))
        clean_patch = cells[1 + arms.index("clean")][1]
        for c, (lab, img) in enumerate(cells):
            a = axes[r, c + 1]
            a.imshow(img)
            a.set_xticks([]); a.set_yticks([])
            for s in a.spines.values():
                s.set_linewidth(0.4); s.set_color("#888888")
            a.set_title(lab, fontsize=7.8 if c == 0 else 7.4, pad=2.0)
            e = axes[r + 1, c + 1]
            if c == 0:                      # GT has no error against itself
                e.axis("off")
                continue
            err = np.abs(img - clean_patch).mean(-1) * ERR_GAIN
            e.imshow(np.clip(err, 0, 1), cmap="inferno", vmin=0, vmax=1)
            e.set_xticks([]); e.set_yticks([])
            for s in e.spines.values():
                s.set_linewidth(0.4); s.set_color("#888888")
        axes[r + 1, 0].axis("off")
        axes[r + 1, 0].text(0.98, 0.62, "error against", fontsize=7.2, ha="right", va="center",
                            color="#333333")
        axes[r + 1, 0].text(0.98, 0.40, "the clean render", fontsize=7.2, ha="right", va="center",
                            color="#333333")
        axes[r + 1, 0].text(0.98, 0.18, f"×{ERR_GAIN}", fontsize=7.8, ha="right", va="center",
                            color="#333333")

    fig.subplots_adjust(left=0.004, right=0.996, top=0.915, bottom=0.012, wspace=0.03, hspace=-0.06)
    for r, sc in enumerate(man["scenes"]):
        axes[r, 0].set_ylabel(f"{sc['scene']}\nview {sc['view_index']}\nrank {sc['view_rank']}/{sc['n_held_out']}",
                              fontsize=7.4, rotation=90, labelpad=3.0)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig6_qualitative.pdf", dpi=300, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / "fig6_qualitative.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    A4.mkdir(parents=True, exist_ok=True)
    (A4 / "j5_fig_qual.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(f"wrote {OUT/'fig6_qualitative.pdf'} and .png; "
          + ", ".join(f"{s['scene']} crop ({s['crop']['x']},{s['crop']['y']}) σ{s['crop']['gt_std']}"
                      for s in man["scenes"]))


if __name__ == "__main__":
    main()
