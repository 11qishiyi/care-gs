"""Fig. 5 --- a decibel budget is not a coverage budget.

Panel A plots the six usable assets' configurations in the plane a practitioner would use (PSNR loss against the
clean model) and the plane the paper argues for (coverage loss): configurations that are indistinguishable in
decibels sit up to several coverage points apart. The annotated pair is the widest such gap at a matched decibel
loss and is found from the data, not picked by hand.

Panel B turns the same rows into an exchange rate --- coverage points per decibel --- per asset, which is the
quantity that makes a fidelity budget unenforceable: the rate differs by a factor of four between assets of the
same kind.

Reads `experiments/artifacts/a4/m5_rd_v2.json` and the usable set from `j1_reliability.json`; writes
`experiments/artifacts/a4/j5_fig_decibel.json` with the numbers the caption quotes.

    python tools/jvcir_fig_decibel.py
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
TOL_DB = 0.1
C_PRUNE = "#c0392b"
C_QFP = "#1f4e79"


def main() -> None:
    grid = json.loads((A4 / "m5_rd_v2.json").read_text(encoding="utf-8"))
    j1 = json.loads((A4 / "j1_reliability.json").read_text(encoding="utf-8"))
    keep = j1["keep"]
    scenes = {s["scene"]: s for s in grid["scenes"] if s["scene"] in keep}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.95), gridspec_kw={"width_ratios": [1.15, 1]})

    # ---------------- panel A: decibel loss vs coverage loss
    for fam, colour, label in (("prune", C_PRUNE, "deleting primitives"),
                               ("qfp", C_QFP, "quantising attributes")):
        xs, ys = [], []
        for sc in scenes.values():
            for r in sc["rows"]:
                if r.get("family") == fam:
                    xs.append(-r["d_psnr"])
                    ys.append(-r["drop_pp"])
        ax1.scatter(xs, ys, s=11, color=colour, alpha=0.55, linewidths=0, label=label, zorder=3)

    # the widest coverage gap at a matched decibel loss, within one asset
    best = None
    for name, sc in scenes.items():
        rows = sc["rows"]
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                if abs(a["d_psnr"] - b["d_psnr"]) <= TOL_DB:
                    gap = abs(a["drop_pp"] - b["drop_pp"])
                    if best is None or gap > best["d_pp"]:
                        best = {"scene": name, "a": a["variant"], "b": b["variant"],
                                "d_db": abs(a["d_psnr"] - b["d_psnr"]), "d_pp": gap,
                                "xa": -a["d_psnr"], "ya": -a["drop_pp"],
                                "xb": -b["d_psnr"], "yb": -b["drop_pp"]}
    if best:
        ax1.annotate("", xy=(best["xb"], best["yb"]), xytext=(best["xa"], best["ya"]),
                     arrowprops=dict(arrowstyle="<->", lw=0.8, color="#333333"), zorder=5)
        ax1.scatter([best["xa"], best["xb"]], [best["ya"], best["yb"]], s=26, facecolors="none",
                    edgecolors="#333333", linewidths=0.8, zorder=6)
        mx = (best["xa"] + best["xb"]) / 2
        my = (best["ya"] + best["yb"]) / 2
        ax1.annotate(f"{best['d_db']:.2f} dB apart,\n{best['d_pp']:.1f} pp apart\n({best['scene']})",
                     xy=(mx, my), xytext=(0.42, 15.0), fontsize=5.0, color="#333333",
                     va="center", arrowprops=dict(arrowstyle="-", lw=0.5, color="#777777",
                                               shrinkA=0, shrinkB=2), zorder=7)

    ax1.axhline(EPS, color="#555555", lw=0.6, ls="--", zorder=1)
    ax1.text(1.57, EPS + 0.45, r"tolerance $\varepsilon = 1$ pp", fontsize=5.2, color="#444444", ha="right", va="bottom")
    ax1.set_xlabel("PSNR loss against the clean model (dB)", fontsize=6.2)
    ax1.set_ylabel("coverage loss (pp)", fontsize=6.2)
    ax1.set_xlim(-0.45, 1.6)
    ax1.set_ylim(-1.2, 24)
    ax1.tick_params(labelsize=5.4, length=2)
    ax1.legend(fontsize=5.2, frameon=False, loc="upper left", handletextpad=0.3, borderpad=0.1)
    ax1.set_title("A  the same decibel loss, different coverage", fontsize=6.4, loc="left")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # ---------------- panel B: coverage points per decibel, per asset
    per = j1["e3"]["per_asset"]
    names = [p["scene"] for p in per]
    med = [p["pp_per_dB_median"] for p in per]
    lo = [p["pp_per_dB_min"] for p in per]
    hi = [p["pp_per_dB_max"] for p in per]
    x = np.arange(len(names))
    ax2.vlines(x, lo, hi, color="#9aa7b4", lw=1.0, zorder=2)
    ax2.scatter(x, med, s=22, color=C_QFP, zorder=3)
    for xi, m in zip(x, med):
        ax2.text(xi, m * 1.16, f"{m:.2f}", fontsize=4.8, ha="center", color="#1f4e79")
    ax2.set_yscale("log")
    ax2.set_xticks(x)
    ax2.set_xticklabels([n.replace("_i7k", "\\i7k") for n in names], fontsize=5.0, rotation=18)
    ax2.set_ylabel("coverage points per dB", fontsize=6.2)
    ax2.tick_params(labelsize=5.4, length=2)
    ax2.set_title("B  the exchange rate is asset-dependent", fontsize=6.4, loc="left")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=0.3)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig4_decibel.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / "fig4_decibel.png", dpi=300, bbox_inches="tight", pad_inches=0.02)

    payload = {
        "source": "experiments/artifacts/a4/m5_rd_v2.json + j1_reliability.json",
        "tol_db": TOL_DB,
        "widest_matched_db_pair": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in (best or {}).items()},
        "pp_per_db_median_range": j1["e3"]["median_range"],
        "pp_per_db_spread_x": j1["e3"]["spread_x"],
    }
    (A4 / "j5_fig_decibel.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"wrote {OUT/'fig4_decibel.pdf'} and .png  |  widest matched-dB pair: "
          f"{best['d_db']:.2f} dB / {best['d_pp']:.1f} pp on {best['scene']}" if best else "no pair found")


if __name__ == "__main__":
    main()
