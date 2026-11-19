import json

d = json.load(open(r"D:\3dsg_1\experiments\artifacts\a4\m5_rd_v2.json", encoding="utf-8"))
for sc in d["scenes"]:
    rows = [r for r in sc["rows"] if r["rate"] < 4.6]
    if not rows:
        continue
    print(f"== {sc['scene']}")
    for r in sorted(rows, key=lambda x: x["rate"]):
        dp = r.get("d_psnr")
        print(f"  {r['variant']:>16} {r['rate']:6.3f}x {r['drop_pp']:+7.2f} pp  "
              f"dPSNR {dp:+.3f}" if dp is not None else f"  {r['variant']:>16} {r['rate']:6.3f}x {r['drop_pp']:+7.2f} pp")
    break
