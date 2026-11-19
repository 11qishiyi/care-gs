import json
import os

base = r"D:\3dsg_1\experiments\artifacts\a4"
for tag in ["m1_rd", "m3_rd", "m5_rd_v2", "m9_rd", "m10_rd", "m11_rd", "m12_rd"]:
    p = os.path.join(base, tag + ".json")
    if not os.path.exists(p):
        print(tag, "MISSING")
        continue
    d = json.load(open(p, encoding="utf-8"))
    sc = d["scenes"][0]
    rows = sc["rows"]
    n_ssim = sum(1 for r in rows if r.get("ssim") is not None)
    n_lp = sum(1 for r in rows if r.get("lpips") is not None)
    print(f"{tag:12s} rows={len(rows):3d} ssim={n_ssim:3d} lpips={n_lp:3d} "
          f"rate_src={d.get('meta', {}).get('rate_source')} "
          f"keys={[k for k in rows[0].keys() if k not in ('variant','family','note')]}")
