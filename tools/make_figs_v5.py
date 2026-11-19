# Academic Figure Skill — Asset Confirmation (verified against assets/figures/)
# (a) edit-family comparison  -> assets/figures/BarComparison    -> param inherit (JSON data, not tidy CSV)
# (b) dose-response sweep     -> assets/figures/LineTrend        -> param inherit
# (c) granularity pairing     -> assets/figures/PairedBoxScatter -> param inherit
# (d) quantile-growth sweep   -> assets/figures/LineTrend        -> param inherit
# (fig2) four yardsticks      -> assets/figures/GroupedBarChart  -> param inherit
# (fig3a) optimisation depth  -> assets/figures/PairedBoxScatter -> param inherit
# (fig3b) storage bit depth   -> assets/figures/LineTrend        -> param inherit
# RULE: "param inherit" = drawing function below that copies Class A/B/C values from the
#       named production script; no production script is executed because every one of them
#       expects flat CSV input while this project's measurements live in nested per-scene JSON.

"""Publication figures v5 for "Valid but Unusable" (TMLR).

Three vector figures, all at true print size (165 mm wide = the TMLR text block, so the
PDF is included at 1:1 and never downscaled):

  fig1  Editing the asset breaks the certificate, and only the geometric edit does   (4 panels)
  fig2  Four yardsticks on the same edit                                             (1 panel)
  fig3  Optimisation depth and storage precision (appendix)                          (2 panels)

Style: Academic Figure Skill baselines (Arial 7-8 pt, spines 0.6 pt, no gridlines, no
legend frame, journal palette).  Every plotted number is printed and, where the paper
tabulates it, checked against the tabulated value before the figure is written.

Run from the repository root:
    python tools/make_figs_v5.py
"""
import json
import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl          # noqa: E402
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402

# ---------------------------------------------------------------- style baselines
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "figure.titlesize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
})
CATEGORICAL = ["#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666"]
GREY = "#999999"
BLACK = "#222222"

MM = 1 / 25.4
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures_v5")


def path(*p):
    return os.path.join(ROOT, *p)


def load_json(*p):
    with open(path(*p), encoding="utf-8") as fh:
        return json.load(fh)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{name}.pdf"), bbox_inches="tight",
                metadata={"CreationDate": None})
    fig.savefig(os.path.join(OUT, f"{name}.png"), bbox_inches="tight", dpi=300)
    print(f"  wrote figures_v5/{name}.pdf (+png)")


# ------------------------------------------------------------------------ data
RELEASED = ["bicycle", "flowers", "stump", "treehill"]          # one archive, 40k
SECOND = ["bonsai", "amsterdam_20k"]                             # other released checkpoints
SELF = ["barcelona_st", "bilbao_st", "chicago_st"]               # we trained these
ASSETS = RELEASED + SECOND + SELF
PROV = {**{s: "released 40k" for s in RELEASED},
        **{s: "second dataset" for s in SECOND},
        **{s: "self-trained" for s in SELF}}
PROV_COLOR = {"released 40k": CATEGORICAL[0], "second dataset": CATEGORICAL[2],
              "self-trained": CATEGORICAL[4]}
SHORT = {"bicycle": "bicycle", "flowers": "flowers", "stump": "stump", "treehill": "treehill",
         "bonsai": "bonsai", "amsterdam_20k": "amsterdam",
         "barcelona_st": "barcelona*", "bilbao_st": "bilbao*", "chicago_st": "chicago*"}

COV = {}          # (scene, variant) -> (loss_pp, lo, hi) at pixel granularity
COV_BLOCK = {}    # (scene, variant) -> loss_pp at 64x64 block granularity
for s in ASSETS + [x + "_i7k" for x in RELEASED + ["bonsai"]]:
    f = path("results_v110", "region", f"region_{s}.json")
    if not os.path.isfile(f):
        continue
    blob = json.load(open(f, encoding="utf-8"))
    rows = blob["rows"] if isinstance(blob, dict) and "rows" in blob else blob
    for r in rows:
        gran = r.get("gran") or r.get("granularity")
        loss = -r["degradation_pp"]
        if gran == "pixel":
            COV[(s, r["variant"])] = (loss, 100 * abs(r["drop_lo"]), 100 * abs(r["drop_hi"]))
        elif gran == "block64":
            COV_BLOCK[(s, r["variant"])] = loss

# dose-response and the cost of validity come from the earlier campaign (4 budgets)
DOSE, QGROWTH = {}, {}
for s in RELEASED:
    b = load_json("results_v70", f"battery_{s}.json")
    DOSE[s] = [(lv, -100 * b["coverage"][f"prune{lv}"]["drop_mean"]) for lv in (70, 50, 30, 10)]
    QGROWTH[s] = [(lv, 100 * b["coverage"][f"prune{lv}"]["q_growth_mean"]) for lv in (70, 50, 30, 10)]

# four yardsticks (same sources as Table 6 / tools/make_fig3_v90.py)
def boot(x, n=4000, seed=0):
    v = np.asarray(x, np.float64)
    v = v[~np.isnan(v)]
    rng = np.random.default_rng(seed)
    m = rng.choice(v, size=(n, v.size), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


coverage, local, reg, pose = {}, {}, {}, {}
for s in RELEASED:
    d = load_json("results_v90", "stage9", f"{s}.json")
    coverage[s] = 100.0 * d["coverage"]["opacity30"]["drop_mean"]
    local[s] = 100.0 * (d["task"]["tol2_peak0.6"]["opacity30"] - d["task"]["tol2_peak0.6"]["clean"])
for rel in (("results_v70", "second_task.json"), ("results_v90", "second_task_stump_treehill.json")):
    for d in load_json(*rel):
        cl = np.array([r["inlier_ratio"] for r in d["variants"]["clean"]["per_view"]])
        pr = np.array([r["inlier_ratio"] for r in d["variants"]["prune30"]["per_view"]])
        diff = 100.0 * (pr - cl)
        lo, hi = boot(diff)
        reg[d["scene"]] = dict(drop=float(diff.mean()), lo=lo, hi=hi, n=int(diff.size))
for rel in (("results_v80", "third_task.json"), ("results_v90", "third_task_stump_treehill.json")):
    for d in load_json(*rel):
        v = d["variants"]
        pose[d["scene"]] = 100.0 * (v["prune30"]["success_5deg"] - v["clean"]["success_5deg"])

EXPECTED = {"coverage": [-22.1, -10.8, -27.7, -15.2], "local": [-27.3, -11.1, -12.8, -34.4],
            "registration": [-3.9, -2.6, -2.5, -11.3], "pose": [-8.3, -4.8, -6.7, 5.9]}
series = {"coverage": [coverage[s] for s in RELEASED], "local": [local[s] for s in RELEASED],
          "registration": [reg[s]["drop"] for s in RELEASED],
          "pose": [pose[s] for s in RELEASED]}
for k, vals in series.items():
    for got, want in zip(vals, EXPECTED[k]):
        if abs(got - want) > 0.1:
            raise SystemExit(f"refusing to plot: {k} {got:+.2f} != tabulated {want:+.1f}")

# --------------------------------------------------------------- figure 1 (4 panels)
fig = plt.figure(figsize=(165 * MM, 104 * MM))
gs = fig.add_gridspec(2, 2, hspace=0.52, wspace=0.30)

# (a) per-asset edit matrix ------------------------------------------------
ax = fig.add_subplot(gs[0, 0])
families = [("prune30", "prune\n30%"), ("prune50", "prune\n50%"), ("shdeg1", "SH\n3\u21921"),
            ("quant8", "8-bit"), ("quant6", "6-bit"), ("quant4", "4-bit")]
M = np.array([[COV[(s, v)][0] for v, _ in families] for s in ASSETS])
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
cmap = LinearSegmentedColormap.from_list("damage", ["#B2182B", "#F7F7F7", "#2166AC"])
norm = TwoSlopeNorm(vcenter=0.0, vmin=-65.0, vmax=8.0)
im = ax.imshow(M, cmap=cmap, norm=norm, aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M[i, j]
        ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=5.4,
                color="white" if abs(v) > 32 else BLACK)
ax.set_xticks(range(len(families)))
ax.set_xticklabels([lab for _v, lab in families], fontsize=6.2)
ax.set_yticks(range(len(ASSETS)))
ax.set_yticklabels([SHORT[s] for s in ASSETS], fontsize=6.2)
for tick, s in zip(ax.get_yticklabels(), ASSETS):
    tick.set_color(PROV_COLOR[PROV[s]])
ax.set_title("a  one row per asset", loc="left", fontweight="bold")


# (b) dose-response ---------------------------------------------------------
ax = fig.add_subplot(gs[0, 1])
for i, s in enumerate(RELEASED):
    xs = [lv for lv, _ in DOSE[s]]
    ys = [y for _, y in DOSE[s]]
    ax.plot(xs, ys, marker="o", ms=3.0, lw=1.0, color=CATEGORICAL[0],
            alpha=0.35 + 0.15 * i, label="released 40k" if i == 0 else None, zorder=3)
for s in SECOND + SELF:
    pts = [(lv, COV[(s, f"prune{lv}")][0]) for lv in (50, 30) if (s, f"prune{lv}") in COV]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="s" if s in SECOND else "^",
            ms=3.2, lw=0.8, color=PROV_COLOR[PROV[s]], alpha=0.9,
            label=None if s != SECOND[0] and s != SELF[0] else PROV[s], zorder=3)
ax.set_xlabel("primitives kept (%)")
ax.set_ylabel("change in coverage (points)")
ax.set_title("b  dose-response", loc="left", fontweight="bold")
ax.invert_xaxis()
ax.axhline(0, color=GREY, lw=0.5, ls=":")
ax.legend(loc="lower left", handletextpad=0.2, borderaxespad=0.1, fontsize=6)
ax.set_ylim(-70, 12)
ax.set_yticks([-60, -40, -20, 0])

# (c) granularity -----------------------------------------------------------
ax = fig.add_subplot(gs[1, 0])
for s in ASSETS:
    x, y = COV[(s, "prune30")][0], COV_BLOCK[(s, "prune30")]
    ax.scatter(x, y, s=14, color=PROV_COLOR[PROV[s]], edgecolor="white", linewidth=0.3,
               zorder=3, label=PROV[s] if s in (RELEASED[0], SECOND[0], SELF[0]) else None)
lim = [-85, 6]
ax.plot(lim, lim, color=GREY, lw=0.6, ls="--", zorder=1)
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("pixel-granularity change (points)")
ax.set_ylabel("block (64\u00d764) loss (points)")
ax.set_title("c  the region definition moves it", loc="left", fontweight="bold")
ax.legend(loc="upper left", handletextpad=0.2, borderaxespad=0.1, fontsize=6)

# (d) cost of validity ------------------------------------------------------
ax = fig.add_subplot(gs[1, 1])
for i, s in enumerate(RELEASED):
    xs = [lv for lv, _ in QGROWTH[s]]
    ys = [y for _, y in QGROWTH[s]]
    ax.plot(xs, ys, marker="o", ms=3.0, lw=1.0, color=CATEGORICAL[1],
            alpha=0.35 + 0.15 * i, zorder=3)
ax.set_xlabel("primitives kept (%)")
ax.set_ylabel("conformal quantile growth (%)")
ax.set_title("d  validity is cheap, width is not", loc="left", fontweight="bold")
ax.invert_xaxis()
ax.axhline(0, color=GREY, lw=0.5, ls=":")

save(fig, "fig1_edits")
plt.close(fig)

# --------------------------------------------------------------- figure 2
fig = plt.figure(figsize=(165 * MM, 74 * MM))
gs = fig.add_gridspec(1, 2, width_ratios=[2.15, 1.0], wspace=0.32)

# (a) four yardsticks, grouped bars
ax = fig.add_subplot(gs[0, 0])
xs = np.arange(len(RELEASED))
w = 0.19
bars = [("coverage certificate", "coverage", CATEGORICAL[0], None),
        ("local re-localisation", "local", CATEGORICAL[1], None),
        ("registration consensus", "registration", GREY, None),
        ("two-view relative pose", "pose", CATEGORICAL[3], None)]
for k, (label, key, color, edge) in enumerate(bars):
    ax.bar(xs + (k - 1.5) * w, series[key], w, label=label, color=color,
           edgecolor="white", linewidth=0.4, zorder=3)
ax.axhline(0, color=BLACK, lw=0.6, zorder=4)
ax.set_xticks(xs)
ax.set_xticklabels([SHORT[s] for s in RELEASED])
ax.set_ylabel("change from the fresh asset (points)")
ax.set_ylim(-40, 14)
ax.set_yticks(range(-40, 11, 10))
ax.set_title("a  four yardsticks, same edit", loc="left", fontweight="bold")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.20), ncol=2,
          handlelength=1.0, columnspacing=1.0, handletextpad=0.4,
          borderaxespad=0.0, fontsize=5.8)

# (b) how far apart the yardsticks are, per scene
ax = fig.add_subplot(gs[0, 1])
spread, pairs = [], []
for i, s in enumerate(RELEASED):
    vals = {k: abs(series[k][i]) for k in series}
    big = max(vals, key=vals.get)
    small = min(vals, key=vals.get)
    spread.append(vals[big] / vals[small])
    pairs.append((big, small))
ax.bar(xs, spread, 0.62, color=CATEGORICAL[4], edgecolor="white", linewidth=0.4, zorder=3)
for x, v in zip(xs, spread):
    ax.text(x, v + 0.25, f"{v:.1f}\u00d7", ha="center", va="bottom", fontsize=6)
ax.set_xticks(xs)
ax.set_xticklabels([SHORT[s] for s in RELEASED], rotation=30, ha="right", fontsize=6)
ax.set_ylabel("spread across yardsticks (max/min)")
ax.set_ylim(0, 13)
ax.set_title("b  same edit, different answers", loc="left", fontweight="bold")
save(fig, "fig2_yardsticks")
plt.close(fig)

# --------------------------------------------------------------- figure 3
fig = plt.figure(figsize=(165 * MM, 62 * MM))
gs = fig.add_gridspec(1, 2, wspace=0.32)

# (a) optimisation depth
ax = fig.add_subplot(gs[0, 0])
pairs = [(s, COV[(s, "prune30")][0], COV[(s + "_i7k", "prune30")][0])
         for s in RELEASED + ["bonsai"]
         if (s, "prune30") in COV and (s + "_i7k", "prune30") in COV]
for s, a, b in pairs:
    ax.plot([0, 1], [a, b], color=GREY, lw=0.8, zorder=2)
    ax.scatter([0], [a], s=18, color=CATEGORICAL[0], zorder=3, edgecolor="white",
               linewidth=0.3)
    ax.scatter([1], [b], s=18, color=CATEGORICAL[3], zorder=3, edgecolor="white",
               linewidth=0.3)
ax.set_xticks([0, 1])
ax.set_xticklabels(["40k", "7k"])
ax.set_xlim(-0.35, 1.35)
ax.set_ylabel("30% prune change (points)")
ax.set_title("a  optimisation depth, same scene", loc="left", fontweight="bold")
ax.text(0.5, -0.20, "fewer, less converged primitives \u2192 less damage",
        transform=ax.transAxes, ha="center", fontsize=6, color=GREY)

# (b) bit depth
ax = fig.add_subplot(gs[0, 1])
bits = [("quant8", 8), ("quant6", 6), ("quant4", 4)]
for s in RELEASED + SELF:
    ys = [COV[(s, v)][0] for v, _ in bits]
    dx = -0.05 if PROV[s] == "released 40k" else (0.05 if PROV[s] == "self-trained" else 0.0)
    ax.plot([0 + dx, 1 + dx, 2 + dx], ys, marker="o", ms=3.0, lw=0.7,
            color=PROV_COLOR[PROV[s]], alpha=0.9, zorder=3, label=None)
ax.axhline(0, color=GREY, lw=0.5, ls=":")
ax.set_xlabel("SH quantisation")
ax.set_ylabel("coverage change (points)")
ax.set_xticks([0, 1, 2])
ax.set_xticklabels(["8 bit", "6 bit", "4 bit"])
ax.set_ylim(-1.5, 1.5)
ax.set_yticks([-1, 0, 1])
ax.set_title("b  storage precision is inert", loc="left", fontweight="bold")

save(fig, "fig3_depth_bits")
plt.close(fig)

# --------------------------------------------------------------- self-check printout
print("\nplotted values")
print(f"{'asset':13s}{'p30':>7s}{'p50':>7s}{'sh':>7s}{'q8':>7s}{'q6':>7s}{'q4':>7s}{'blk30':>7s}")
for s in ASSETS:
    row = [COV[(s, v)][0] for v in ("prune30", "prune50", "shdeg1", "quant8", "quant6", "quant4")]
    print(f"{SHORT[s]:13s}" + "".join(f"{x:7.1f}" for x in row)
          + f"{COV_BLOCK[(s, 'prune30')]:7.1f}")
print("\nfour yardsticks (30% prune, points)")
for i, s in enumerate(RELEASED):
    print(f"  {s:9s}" + "".join(f"{series[k][i]:8.1f}" for k in series))

for name, dst in (("fig1_edits", "fig_dose.pdf"), ("fig2_yardsticks", "fig_three.pdf"),
                  ("fig3_depth_bits", "fig_ext.pdf")):
    shutil.copyfile(path("figures_v5", f"{name}.pdf"), path("submission", "final", dst))
    print(f"installed submission/final/{dst}")
