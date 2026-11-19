"""Exclude the broken bonsai checkpoint and report the numbers the text needs.

bonsai's re-stitched archive renders at 15.8 dB against its ground truth (the mirror's
cameras.json does not pair with the nvs-bench images), so its residuals are dominated by a
global misalignment rather than by the edit.  Leaving it in the grid is what produced the
0.9-point 30%-prune loss that contradicts the earlier campaign's 10.3.
"""
import json
import sys

import numpy as np

SRC = "results_v120/audit_bound.json"
DST = "results_v120/audit_bound_nobonsai.json"
a = json.load(open(SRC, encoding="utf-8"))
rows = [r for r in a["rows"] if r["scene"] != "bonsai"]
a["rows"] = rows
a["summary"]["n_cells"] = len(rows)
a["summary"]["excluded"] = "bonsai (camera/ground-truth pairing broken in this campaign)"
json.dump(a, open(DST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

mae = np.array([r["audit_mae_pp"] for r in rows])
bias = np.array([r["audit_bias_pp"] for r in rows])
tight = np.array([r["tightness_mean"] for r in rows])
prune = [r for r in rows if r["variant"] in ("prune50", "prune30", "pup30")]
tp = np.array([r["tightness_mean"] for r in prune])
noop = [r for r in rows if r["variant"] == "quant8"]
kv = {}
for r in rows:
    for k, d in (r.get("kview") or {}).items():
        if d:
            kv.setdefault(int(k), []).append(d["mae_pp"])
print("cells", len(rows), "scenes", len({r["scene"] for r in rows}))
print(f"MAE mean {mae.mean():.1f} max {mae.max():.1f} |bias| {abs(bias).mean():.2f}")
print(f"noop bias {np.mean([r['audit_bias_pp'] for r in noop]):+.1f} "
      f"noop MAE {np.mean([r['audit_mae_pp'] for r in noop]):.1f}")
print(f"tight prune median {np.median(tp):.2f} min {tp.min():.2f} max {tp.max():.2f} "
      f"n_over1 {int((tp > 1).sum())} n_nonpos {int((np.array([r['drop_mean'] for r in rows]) >= 0).sum())}")
print("ks_alone min", min(r["ks_alone_holds_frac"] for r in rows),
      "n cells below 1:", sum(1 for r in rows if r["ks_alone_holds_frac"] < 0.999))
print("kview", {k: round(float(np.mean(v)), 1) for k, v in sorted(kv.items())})
print("all-MAE min/max", round(mae.min(), 1), round(mae.max(), 1))
