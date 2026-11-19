"""Summarise the stage-10 learned-matcher run and write results_v100/derived/learned.json.

Source: results_v100/stage10/<scene>.json, produced by experiments/stage10_learned.py
on the GPU node.  Each scene file holds, per variant (clean / prune30 / prune10):
  * loftr: precision@2px per view, match counts, median displacement, mean confidence
  * ncc:   the paper's reduced patch task on the identical half-resolution renders
The derived file keeps the per-view arrays so the paper checker can recompute every
number it cites (mean precision, drop in points, and the treehill-excluded range).
"""
import glob
import json
import os

import numpy as np

D = os.environ.get("STAGE10_DIR", "results_v100")
SC = ["bicycle", "flowers", "stump", "treehill"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


out = {"stage10": {}, "points": {}, "n_views": {}}
for p in sorted(glob.glob(os.path.join(D, "stage10", "*.json"))):
    d = load(p)
    s = d["scene"]
    out["n_views"][s] = d["n_views"]
    out["stage10"][s] = {"W": d["W"], "H": d["H"], "factor": d["factor"], "variants": {}}
    for name, v in d["variants"].items():
        row = {"psnr": v["psnr"], "n_primitives": v["n_primitives"],
               "loftr_precision": v["loftr"]["precision"],
               "loftr_precision_mean": float(np.nanmean(v["loftr"]["precision"])),
               "loftr_n_mean": float(np.nanmean(v["loftr"]["n"]))}
        if "ncc" in v:
            row["ncc_hit"] = v["ncc"]["hit"]
            row["ncc_hit_mean"] = float(np.nanmean(v["ncc"]["hit"]))
        out["stage10"][s]["variants"][name] = row

    clean_l = out["stage10"][s]["variants"]["clean"]["loftr_precision_mean"]
    out["points"][s] = {}
    for name in ("prune30", "prune10"):
        if name not in out["stage10"][s]["variants"]:
            continue
        v = out["stage10"][s]["variants"][name]
        out["points"][s][f"loftr_{name}"] = 100 * (v["loftr_precision_mean"] - clean_l)
        if "ncc_hit_mean" in v:
            clean_n = out["stage10"][s]["variants"]["clean"]["ncc_hit_mean"]
            out["points"][s][f"ncc_{name}"] = 100 * (v["ncc_hit_mean"] - clean_n)

os.makedirs(os.path.join(D, "derived"), exist_ok=True)
dst = os.path.join(D, "derived", "learned.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, sort_keys=True)
print(f"wrote {dst}")

print("\n=== LoFTR (learned, detector-free) vs NCC (hand-built) on identical renders ===")
for s in SC:
    if s not in out["stage10"]:
        continue
    v = out["stage10"][s]["variants"]
    print(f"{s:9s} clean: LoFTR {v['clean']['loftr_precision_mean']:.3f}  "
          f"NCC {v['clean'].get('ncc_hit_mean', float('nan')):.3f}", end="")
    for name in ("prune30", "prune10"):
        if name in v:
            print(f" | {name}: LoFTR {v[name]['loftr_precision_mean']:.3f} "
                  f"({100*(v[name]['loftr_precision_mean']-v['clean']['loftr_precision_mean']):+.1f}pt) "
                  f"NCC {v[name].get('ncc_hit_mean', float('nan')):.3f} "
                  f"({100*(v[name].get('ncc_hit_mean', float('nan'))-v['clean'].get('ncc_hit_mean', float('nan'))):+.1f}pt)",
                  end="")
    print()

print("\n=== spread across the four yardsticks at 30% including LoFTR ===")
for s in SC:
    if s not in out["points"]:
        continue
    print(f"{s:9s} " + "  ".join(f"{k}={v:+.1f}" for k, v in out["points"][s].items()))
