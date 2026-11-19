"""Task-side uncertainty for Table 5, three ways (the red-team R2 question).

"Every coverage number carries a bracket, no task number does."

We answer with what the sweep already contains, in decreasing strength:
  1. the spread over the 108 protocol cells for the same scene and edit
     (min / median / max of the task loss, in points) -- a protocol-level interval;
  2. the pooled view-level bootstrap at the reference cell (81 views over four scenes);
  3. the fraction of cells in which the task loss exceeds the coverage loss, per scene.

Coverage losses and their 2.5/97.5 brackets come from `results_v110/region_<scene>.json`
(the same 400-split protocol as the paper), not from hard-coded constants.

Usage: python tools/task_intervals.py [results_v110/task_sweep_4.json]
"""
from __future__ import annotations

import glob
import json
import os
import statistics as st
import sys

CFG = dict(patch=32, search=24, tol=2, min_peak=0.6)
SCENES = ("bicycle", "flowers", "stump", "treehill")
REGION_DIR = "results_v110/region"


def coverage(scene: str, variant: str) -> tuple[float, float, float]:
    """(loss, lo, hi) in points from the region JSON written by region_coverage.py."""
    path = os.path.join(REGION_DIR, f"region_{scene}.json")
    blob = json.load(open(path, encoding="utf-8"))
    rows = blob["rows"] if isinstance(blob, dict) and "rows" in blob else blob
    for r in rows:
        if r.get("scene") == scene and r.get("variant") == variant and \
                (r.get("gran") or r.get("granularity")) == "pixel":
            lo = 100 * abs(r["drop_hi"])   # drop is negative; hi bound is the shallower one
            hi = 100 * abs(r["drop_lo"])
            return abs(r["degradation_pp"]), min(lo, hi), max(lo, hi)
    raise KeyError((scene, variant))


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "results_v110/task_sweep_4.json"
    d = json.load(open(path, encoding="utf-8"))
    cfgs = d["per_config"]
    ref = [c for c in cfgs if c["patch"] == CFG["patch"] and c["search"] == CFG["search"]
           and c["tol"] == CFG["tol"] and abs(c["min_peak"] - CFG["min_peak"]) < 1e-9][0]
    print(f"reference cell: patch={ref['patch']} search={ref['search']} tol={ref['tol']} "
          f"peak={ref['min_peak']}, {ref['n_views_prune30']} views over four scenes")

    out: dict[str, dict] = {}
    for arm in ("prune30", "prune50"):
        lo = -100 * ref[f"delta_hi_{arm}"] if ref[f"delta_hi_{arm}"] < 0 else 100 * ref[f"delta_hi_{arm}"]
        hi = -100 * ref[f"delta_lo_{arm}"]
        print(f"\npooled view-level bootstrap, {arm}: [{lo:.1f}, {hi:.1f}] points")
        print(f"{'scene':10s} {'cell':>6s} {'grid min':>9s} {'median':>7s} {'grid max':>9s} "
              f"{'cells>cov':>10s} {'coverage [2.5,97.5]':>22s} {'cell outside?':>14s}")
        for s in SCENES:
            cell = -100 * ref["per_scene"][s][f"delta_{arm}"]
            vals = [-100 * c["per_scene"][s][f"delta_{arm}"] for c in cfgs]
            cov, clo, chi = coverage(s, arm)
            frac = sum(1 for v in vals if v > cov) / len(vals)
            outside = not (clo <= cell <= chi)
            out.setdefault(arm, {})[s] = dict(
                cell=round(cell, 1), grid_min=round(min(vals), 1), grid_med=round(st.median(vals), 1),
                grid_max=round(max(vals), 1), frac_cells_task_gt_cov=round(frac, 2),
                cov=round(cov, 1), cov_lo=round(clo, 1), cov_hi=round(chi, 1),
                cell_outside_cov_ci=outside)
            print(f"{s:10s} {cell:6.1f} {min(vals):9.1f} {st.median(vals):7.1f} {max(vals):9.1f} "
                  f"{frac:10.2f} {f'{cov:.1f} [{clo:.1f},{chi:.1f}]':>22s} {str(outside):>14s}")
        print(f"  pooled bootstrap: [{lo:.1f}, {hi:.1f}]")
        out[arm]["pooled_bootstrap"] = [round(lo, 1), round(hi, 1)]

    os.makedirs("results_v110", exist_ok=True)
    json.dump(out, open("results_v110/task_intervals.json", "w", encoding="utf-8"), indent=1)
    print("\nwrote results_v110/task_intervals.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
