import json, sys
p = sys.argv[1]
d = json.load(open(p))
for row in d.get("scenes", []):
    for name, st in row.get("variants", {}).items():
        print(row.get("scene"), name, round(float(st.get("psnr", float("nan"))), 3),
              round(float(st.get("ssim") or float("nan")), 4), round(float(st.get("lpips") or float("nan")), 4))