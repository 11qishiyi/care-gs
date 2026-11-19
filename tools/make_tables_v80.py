"""Turn the stage-8 artifacts (results_v80) into the numbers the paper needs."""
import glob
import json
import os

D = os.environ.get("STAGE8_DIR", "results_v80")
SC = ["bicycle", "flowers", "stump", "treehill"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


bat = {}
for p in sorted(glob.glob(os.path.join(D, "battery", "*.json"))):
    d = load(p)
    bat[d["scene"]] = d

print("=== C. criterion comparison at the 30% budget (points) ===")
print(f"{'scene':9s} {'opacity':>18s} {'sensitivity':>18s} {'q grow op':>10s} {'q grow sens':>11s}")
crit_rows = []
for s in SC:
    if s not in bat:
        continue
    b = bat[s]
    op = b["coverage"].get("prune30")
    pu = b["coverage"].get("pup30")
    if not op or not pu:
        print(f"{s:9s}  missing variant (have: {sorted(b['coverage'])})")
        continue
    print(f"{s:9s} "
          f"{100*op['drop_mean']:+7.1f} [{100*op['drop_lo']:+6.1f},{100*op['drop_hi']:+6.1f}] "
          f"{100*pu['drop_mean']:+7.1f} [{100*pu['drop_lo']:+6.1f},{100*pu['drop_hi']:+6.1f}] "
          f"{100*op['q_growth_mean']:+9.0f}% {100*pu['q_growth_mean']:+10.0f}%")
    crit_rows.append((s, op, pu))

print("\n=== B. merge edit (40% of the primitives) ===")
for s in SC:
    if s not in bat:
        continue
    b = bat[s]
    mg = b["coverage"].get("merge40")
    if not mg:
        print(f"{s:9s}  no merge40 variant (have: {sorted(b['coverage'])})")
        continue
    blk = b["block"].get("merge40", {})
    print(f"{s:9s} pixel {100*mg['drop_mean']:+7.1f} [{100*mg['drop_lo']:+6.1f},{100*mg['drop_hi']:+6.1f}]"
          f"  block {100*blk.get('drop_mean', float('nan')):+7.1f}"
          f"  q {100*mg['q_growth_mean']:+7.0f}%  PSNR {b['psnr']['merge40']['psnr']:.1f}")

print("\n=== A. third task family (two-view relative pose) ===")
tp = os.path.join(D, "third_task.json")
if os.path.isfile(tp):
    for d in load(tp):
        print(f"-- {d['scene']} ({d['n_views']} views) --")
        for name, v in d["variants"].items():
            print(f"   {name:8s} pairs={v['n_pairs']:3d}  rot_err_med={v['rot_err_median']:6.2f} deg  "
                  f"dir_err_med={v['dir_err_median']:6.2f} deg  success@5deg={v['success_5deg']:.2f}")
else:
    print("third_task.json not present yet")

print("\n=== task sweep on the new variants (if scored) ===")
for s in SC:
    if s not in bat:
        continue
    for key, grid in bat[s]["task_sweep"].items():
        vals = grid.get("tol2_peak0.6", {})
        if "merge40" in vals or "pup30" in vals:
            print(f"{s:9s} {key}: " + "  ".join(f"{k}={v:.3f}" for k, v in vals.items()))
