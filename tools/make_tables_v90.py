"""Turn the stage-9 artifacts (results_v90) into the numbers the paper needs.

Sources (written on the node by stage9_driver.sh, fetched into results_v90/):

    results_v90/stage9/<scene>.json              one-pass battery: clean / opacity30 / fisher30 / opv30
    results_v90/second_task_stump_treehill.json  registration consensus on stump, treehill
    results_v90/third_task_stump_treehill.json   two-view relative pose on stump, treehill
    results_v70/battery_<scene>.json             dose-response and the local task (stage 7)
    results_v70/second_task.json                 registration consensus on bicycle, flowers (stage 7)

Writes results_v90/derived/tables.json, the single artifact the paper checker reads, and prints a
human-readable summary.  Conventions match the submitted paper: captured ground truth, pixel
certificate, 400 random calibration/deployment splits, alpha = 0.10.  Registration intervals are
paired view-level bootstraps (4000 resamples, seed 0), the same recipe as tools/make_fig3.py.
"""
import glob
import json
import os

import numpy as np

D = os.environ.get("STAGE9_DIR", "results_v90")
SC = ["bicycle", "flowers", "stump", "treehill"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def boot(x, n=4000, seed=0):
    v = np.asarray(x, np.float64)
    v = v[~np.isnan(v)]
    rng = np.random.default_rng(seed)
    m = rng.choice(v, size=(n, v.size), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


stage9 = {os.path.basename(p)[:-5]: load(p) for p in sorted(glob.glob(os.path.join(D, "stage9", "*.json")))}
bat70 = {}
for p in sorted(glob.glob("results_v70/battery_*.json")):
    d = load(p)
    bat70[d["scene"]] = d
reg = {}
for p in ("results_v70/second_task.json", os.path.join(D, "second_task_stump_treehill.json")):
    if os.path.isfile(p):
        for d in load(p):
            reg[d["scene"]] = d
pose = {}
for p in ("results_v80/third_task.json", os.path.join(D, "third_task_stump_treehill.json")):
    if os.path.isfile(p):
        for d in load(p):
            pose[d["scene"]] = d

out = {"criterion": {}, "criterion_task": {}, "task2": {}, "residual_diag": {}, "factor": {}}

# ---------------------------------------------------------------- criterion table (Table 3)
for s in SC:
    if s not in stage9:
        continue
    d = stage9[s]
    out["criterion"][s] = {}
    out["criterion_task"][s] = {}
    for name in ("opacity30", "fisher30", "opv30"):
        c = d["coverage"].get(name)
        if c:
            out["criterion"][s][name] = {
                "drop": 100 * c["drop_mean"], "lo": 100 * c["drop_lo"], "hi": 100 * c["drop_hi"],
                "q_growth": 100 * c["q_growth_mean"]}
        grid = d.get("task", {}).get("tol2_peak0.6", {})
        if name in grid and "clean" in grid:
            out["criterion_task"][s][name] = 100 * (grid[name] - grid["clean"])

# ---------------------------------------------------------------- four yardsticks (Table 6)
for s in SC:
    row = {}
    bat = bat70.get(s)
    if bat:
        row["cov30"] = 100 * bat["coverage"]["prune30"]["drop_mean"]
        row["cov10"] = 100 * bat["coverage"]["prune10"]["drop_mean"]
        ts = bat["task_sweep"]["s32_w24"]["tol2_peak0.6"]
        row["local30"] = 100 * (ts["prune30"] - ts["clean"])
        row["local10"] = 100 * (ts["prune10"] - ts["clean"])
    if s in reg:
        clean = np.asarray([r["inlier_ratio"] for r in reg[s]["variants"]["clean"]["per_view"]])
        for lvl in ("30", "10"):
            v = np.asarray([r["inlier_ratio"] for r in reg[s]["variants"]["prune" + lvl]["per_view"]])
            dpt = 100 * (v - clean)
            lo, hi = boot(dpt)
            row["reg" + lvl] = float(dpt.mean())
            row["reg" + lvl + "_lo"] = lo
            row["reg" + lvl + "_hi"] = hi
    if s in pose:
        for lvl in ("30", "10"):
            v = pose[s]["variants"]["prune" + lvl]["success_5deg"] - pose[s]["variants"]["clean"]["success_5deg"]
            row["pose" + lvl] = 100 * v
        row["pose_clean_success"] = pose[s]["variants"]["clean"]["success_5deg"]
        row["pose_pairs"] = pose[s]["variants"]["clean"]["n_pairs"]
        row["rot_med_clean"] = pose[s]["variants"]["clean"]["rot_err_median"]
        row["rot_med_30"] = pose[s]["variants"]["prune30"]["rot_err_median"]
        row["dir_med_clean"] = pose[s]["variants"]["clean"]["dir_err_median"]
        row["inlier_clean"] = reg[s]["variants"]["clean"]["inlier_ratio_mean"] if s in reg else None
        row["inlier_30"] = reg[s]["variants"]["prune30"]["inlier_ratio_mean"] if s in reg else None
        row["n_views"] = reg[s]["n_views"] if s in reg else None
    out["task2"][s] = row

# ---------------------------------------------------------------- residual diagnostics (section 3.1)
for s in SC:
    if s not in stage9:
        continue
    d = stage9[s]["resid_diag"]["clean"]
    br, sat, p99 = d["brightness_ratio"], d["sat_white"], d["p99"]
    out["residual_diag"][s] = {
        "brightness_lo": min(br), "brightness_hi": max(br), "views": len(br),
        "views_gt12": sum(1 for x in br if x > 1.2),
        "sat_views_gt5": sum(1 for x in sat if x > 0.05), "sat_max": max(sat),
        "p99_max": max(p99), "beyond_q_mean": float(np.mean(d["beyond_q"]))}

# ---------------------------------------------------------------- spread across yardsticks
for s in SC:
    row = out["task2"].get(s, {})
    vals = [abs(row[k]) for k in ("cov30", "local30", "reg30", "pose30") if row.get(k) is not None]
    if len(vals) >= 3:
        lo, hi = min(vals), max(vals)
        out["factor"][s] = {"min": lo, "max": hi, "ratio": (hi / lo) if lo > 0 else None}

os.makedirs(os.path.join(D, "derived"), exist_ok=True)
dst = os.path.join(D, "derived", "tables.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, sort_keys=True)
print(f"wrote {dst}")

# ---------------------------------------------------------------- report
print("=== C. three pruning criteria at the 30% budget (captured GT, pixel certificate) ===")
for s in SC:
    if s not in out["criterion"]:
        continue
    cells = []
    for name in ("opacity30", "fisher30", "opv30"):
        c = out["criterion"][s].get(name)
        cells.append(f"{c['drop']:+6.1f} [{c['lo']:+5.1f},{c['hi']:+5.1f}]" if c else f"{'—':>21s}")
    print(f"{s:9s} " + " ".join(f"{c:>21s}" for c in cells))

print("\n--- task drop under each criterion (s32/w24, tol2/peak0.6) ---")
for s in SC:
    if s in out["criterion_task"]:
        print(f"{s:9s} " + "  ".join(f"{k}={v:+.1f}" for k, v in out["criterion_task"][s].items()))

print("\n=== A. four yardsticks at 30% / 10% (drops in points) ===")
for s in SC:
    r = out["task2"].get(s, {})
    if not r:
        continue
    print(f"{s:9s} cov {r['cov30']:+.1f}/{r['cov10']:+.1f}  local {r['local30']:+.1f}/{r['local10']:+.1f}  "
          f"reg {r['reg30']:+.1f} [{r['reg30_lo']:+.1f},{r['reg30_hi']:+.1f}] / "
          f"{r['reg10']:+.1f} [{r['reg10_lo']:+.1f},{r['reg10_hi']:+.1f}]  "
          f"pose {r['pose30']:+.1f}/{r['pose10']:+.1f}")
    if "factor" in out and s in out["factor"]:
        print(f"          spread across yardsticks: {out['factor'][s]['ratio']:.1f}x")

print("\n=== B. per-view residual diagnostics (clean asset) ===")
for s in SC:
    d = out["residual_diag"].get(s)
    if d:
        print(f"{s:9s} brightness {d['brightness_lo']:.2f}-{d['brightness_hi']:.2f}  "
              f"views>1.2 {d['views_gt12']}/{d['views']}  sat>5% {d['sat_views_gt5']}/{d['views']} "
              f"(max {100*d['sat_max']:.1f}%)  p99 max {d['p99_max']:.3f}")

print("\n=== D. cross-check against the submitted numbers (v70 battery) ===")
for s in SC:
    if s in bat70 and s in stage9:
        old = 100 * bat70[s]["coverage"]["prune30"]["drop_mean"]
        new = out["criterion"][s]["opacity30"]["drop"]
        print(f"{s:9s} v70={old:+.1f}pt  stage9={new:+.1f}pt  diff={new-old:+.2f}pt")
