"""Numbers behind the fidelity subsection: what PSNR does and does not predict."""
import json
import numpy as np

a = json.load(open("results_v120/audit_bound.json", encoding="utf-8"))
d = json.load(open("results_v120/dump_summary.json", encoding="utf-8"))
fresh = {sc["scene"]: sc["variants"]["clean"]["psnr"] for sc in d["scenes"]}
psnr = {}
for sc in d["scenes"]:
    for v, st in sc["variants"].items():
        if v != "clean" and st.get("psnr") is not None:
            psnr[(sc["scene"], v)] = fresh[sc["scene"]] - st["psnr"]

rows = []
for r in a["rows"]:
    k = (r["scene"], r["variant"])
    if k in psnr:
        rows.append((r["scene"], r["variant"], -100 * r["drop_mean"], psnr[k],
                     r["tightness_mean"], r["ks_cal_mean"] * 100))

cov = np.array([x[2] for x in rows])
db = np.array([x[3] for x in rows])
geo = [x for x in rows if x[1] in ("prune50", "prune30", "pup30")]
print(f"cells {len(rows)}; Spearman(cov loss, dB lost) = {np.corrcoef(cov, db)[0,1]:+.2f}")

rat = [(c / b, s, v, c, b) for s, v, c, b, *_ in rows if b > 0.3]
rat.sort()
print(f"ratio points-per-dB over {len(rat)} cells with dPSNR>0.3: "
      f"min {rat[0][0]:.1f} ({rat[0][1]}/{rat[0][2]})  "
      f"median {np.median([x[0] for x in rat]):.1f}  max {rat[-1][0]:.1f} ({rat[-1][1]}/{rat[-1][2]})")

geo_rat = [x for x in rat if x[2] in ("prune50", "prune30", "pup30")]
print("geometric only:",
      f"min {min(r[0] for r in geo_rat):.1f} max {max(r[0] for r in geo_rat):.1f} "
      f"n={len(geo_rat)}")

# spread of coverage loss within a narrow dB band
for lo, hi in [(2.0, 4.0), (4.0, 6.0), (6.0, 9.0)]:
    band = [x for x in rows if lo <= x[3] < hi]
    if band:
        cs = [x[2] for x in band]
        print(f"dPSNR in [{lo},{hi}): {len(band)} cells, coverage loss {min(cs):.1f}..{max(cs):.1f}")

tight_geo = [x[4] for x in rows if x[1] in ("prune50", "prune30", "pup30")]
print(f"tightness geometric: median {np.median(tight_geo):.2f}, "
      f"min {min(tight_geo):.2f}, max {max(tight_geo):.2f}")
tight_pos = [x[4] for x in rows if x[4] > 0]
print(f"tightness positive: median {np.median(tight_pos):.2f}, over-statement "
      f"{1/np.median(tight_pos):.1f}x")
print(f"KS>=loss in {sum(1 for x in rows if x[2] <= x[5] + 1e-9)}/{len(rows)} cells (loss in points, KS in points)")
