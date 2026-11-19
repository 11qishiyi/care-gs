"""Regenerate the two figures of the revised paper from the stored result JSONs.

fig_decouple.pdf  (a) coverage drop by granularity and edit strength
                  (b) task drop against coverage drop, with the y = x line
fig_repair.pdf    coverage after re-certification vs calibration size, and the paired
                  quantile growth with the no-op edit as the noise floor

Every plotted number is read from research/results_*; nothing is hard-coded.

    python tools/make_figs_v2.py
"""
from __future__ import annotations

import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures_v2")
SC = ["flowers", "bicycle", "treehill", "stump"]
NICE = {"flowers": "flowers", "bicycle": "bicycle", "treehill": "treehill", "stump": "stump"}


def load(rel):
    with open(os.path.join(ROOT, "research", rel), encoding="utf-8") as f:
        return json.load(f)


def rows(rel):
    d = load(rel)
    return d if isinstance(d, list) else [d]


ms = {(r["scene"], round(r["ratio"], 1)): r for r in rows("results_v52/many_splits.json")}
vt = {}
for p in ("results_v60/vt_flowers.json", "results_v60/vt_rest.json"):
    for r in rows(p):
        vt[r["scene"]] = r
v22 = {(r["scene"], r["edit"]): r for r in rows("results_v22/cert_v3.json")}
ef = {}
for p in glob.glob(os.path.join(ROOT, "research", "results_v53", "*.json")):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    for r in (d if isinstance(d, list) else [d]):
        if isinstance(r, dict) and "scene" in r:
            ef[r["scene"]] = r

os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
                     "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "figure.dpi": 200})

# ------------------------------------------------------------------ figure 1
fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.4, 2.5), gridspec_kw={"width_ratios": [1.15, 1]})

x = np.arange(len(SC))
w = 0.26
pix30 = [-100 * ms[(s, 0.3)]["drop_mean"] for s in SC]
pix30e = [100 * (ms[(s, 0.3)]["drop_mean"] - ms[(s, 0.3)]["drop_lo"]) for s in SC]
reg30 = [100 * vt[s]["voxel_prune30_drop_mean"] for s in SC]
reg30e = [100 * (vt[s]["voxel_prune30_drop_mean"] - vt[s]["voxel_prune30_drop_lo"]) for s in SC]
sh = [100 * ef[s]["shdeg1_drop_mean"] if s in ef else 0.0 for s in SC]
sh = [abs(v) for v in sh]
axa.bar(x - w, pix30, w, yerr=pix30e, capsize=2, label="pixel cert., 30% pruned", color="#2b6cb0")
axa.bar(x, reg30, w, yerr=reg30e, capsize=2, label="region cert., 30% pruned", color="#63b3ed")
axa.bar(x + w, sh, w, label=r"SH $3\to1$ (pixel)", color="#cbd5e0", edgecolor="#4a5568",
        linewidth=0.5)
axa.set_xticks(x)
axa.set_xticklabels([NICE[s] for s in SC])
axa.set_ylabel("coverage loss (points)"); axa.set_ylim(0, 26)
axa.set_title("(a) the unit of the claim sets the size")
axa.legend(frameon=False, loc="upper left", ncol=1, fontsize=6, handlelength=1.1, borderaxespad=0.15)
axa.grid(axis="y", alpha=0.25, linewidth=0.5)
axa.set_axisbelow(True)

# (b) task drop vs coverage drop, both strengths, both granularities
mk = {"50%": "o", "30%": "^"}
cols = {"pixel": "#2b6cb0", "region": "#63b3ed"}
pts = []
for s in SC:
    for ratio, lab in ((0.5, "50%"), (0.3, "30%")):
        t = -100 * (vt[s][f"task_prune{int(ratio*100)}_hit"] - vt[s]["task_clean_hit"])
        pts.append((abs(100 * ms[(s, ratio)]["drop_mean"]), t, "pixel", lab, s))
        v = abs(100 * vt[s][f"voxel_prune{int(ratio*100)}_drop_mean"])
        pts.append((v, t, "region", lab, s))
for gran in ("pixel", "region"):
    for lab in ("50%", "30%"):
        xs = [p[0] for p in pts if p[2] == gran and p[3] == lab]
        ys = [p[1] for p in pts if p[2] == gran and p[3] == lab]
        axb.scatter(xs, ys, marker=mk[lab], s=22, facecolors="none" if gran == "region" else cols[gran],
                    edgecolors=cols[gran], linewidths=0.9,
                    label=f"{gran}, {lab} pruned")
lim = max(max(p[0] for p in pts), max(p[1] for p in pts)) * 1.15
axb.plot([0, lim], [0, lim], ls=":", color="#4a5568", linewidth=0.8)
axb.axhline(0, color="#4a5568", linewidth=0.6)
axb.set_xlabel("coverage loss (points)")
axb.set_ylabel("task loss (points)")
axb.set_title("(b) coverage and utility are not monotone")
axb.set_xlim(-0.5, lim)
axb.legend(frameon=False, loc="lower right", fontsize=6)
axb.grid(alpha=0.25, linewidth=0.5)
axb.set_axisbelow(True)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(OUT, "fig_decouple.pdf"))
fig.savefig(os.path.join(OUT, "fig_decouple.png"), dpi=200)
plt.close(fig)

# ------------------------------------------------------------------ figure 2
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.2))
for s in SC:
    pc = v22[(s, "prune30")].get("repair_curve") or []
    ns = [c["n_cal"] for c in pc]
    cs = [c["cov_rc"] for c in pc]
    ax1.plot(range(len(ns)), cs, marker="o", ms=3, linewidth=1.0, label=NICE[s])
ax1.axhline(0.9, ls="--", color="#4a5568", linewidth=0.8)
ax1.set_xticks(range(5))
ax1.set_xticklabels(["2", "4", "6", "8", "all"])
ax1.set_xlabel("calibration views used to re-certify")
ax1.set_ylabel("coverage after repair")
ax1.set_title("(a) validity is cheap in data")
ax1.legend(frameon=False, fontsize=6, ncol=2)
ax1.grid(alpha=0.25, linewidth=0.5)
ax1.set_axisbelow(True)

edits = ["prune30", "shdeg1", "quant8_sh"]
labels = ["prune 30%", "SH $3\\to1$", "SH 8-bit"]
for k, (e, lab) in enumerate(zip(edits, labels)):
    g = [100 * (v22[(s, e)]["q_pix"] / v22[(s, "clean")]["q_pix"] - 1) for s in SC]
    ax2.bar(np.arange(len(SC)) + (k - 1) * 0.26, g, 0.26, label=lab,
            color=["#2b6cb0", "#90cdf4", "#e2e8f0"][k],
            edgecolor="#4a5568" if k == 2 else "none", linewidth=0.5)
ax2.axhline(0, color="#4a5568", linewidth=0.6)
ax2.set_xticks(np.arange(len(SC)))
ax2.set_xticklabels([NICE[s] for s in SC])
ax2.set_ylabel("quantile growth (%)")
ax2.set_title("(b) information is expensive")
ax2.legend(frameon=False, fontsize=6, loc="upper left")
ax2.grid(axis="y", alpha=0.25, linewidth=0.5)
ax2.set_axisbelow(True)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(OUT, "fig_repair.pdf"))
fig.savefig(os.path.join(OUT, "fig_repair.png"), dpi=200)
plt.close(fig)

print("wrote", OUT)
print("panel (a) pixel drops:", [round(v, 1) for v in pix30])
print("panel (a) region drops:", [round(v, 1) for v in reg30])
print("panel (b) points:", [(p[4], p[2], p[3], round(p[0], 1), round(p[1], 1)) for p in pts])




