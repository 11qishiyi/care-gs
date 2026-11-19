import json
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "/workspace/res/m7/dump/m1_manifest.json"
doc = json.load(open(p))
for sc in doc["scenes"]:
    vs = sc.get("variants", {})
    clean = vs.get("clean", {}).get("psnr")
    print(f"== {sc['scene']} clean={clean} n={sc.get('n')}")
    for k, v in vs.items():
        if k == "clean":
            continue
        print(f"   {k:16s} psnr={v.get('psnr')} bpp={v.get('bytes_per_prim')} rate={v.get('ratio_vs_fp32')}")
