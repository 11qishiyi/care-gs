"""Print the state of an M1 dump directory (manifest coverage + npz list)."""
import json
import os
import sys

dump = sys.argv[1] if len(sys.argv) > 1 else "/workspace/res/m1/dump"
man = os.path.join(dump, "m1_manifest.json")
if os.path.exists(man):
    m = json.load(open(man, encoding="utf-8"))
    for r in m.get("scenes", []):
        vs = r.get("variants", {})
        miss = [k for k in ("ratio_vs_fp32", "ssim", "lpips")
                if isinstance(vs.get("clean"), dict) and vs["clean"].get(k) is None]
        print(f"manifest {r.get('scene'):10s} variants={len(vs):3d} "
              f"clean_psnr={vs.get('clean', {}).get('psnr')} missing_on_clean={miss}")
else:
    print("no manifest")
for fn in sorted(os.listdir(dump)):
    if fn.endswith(".npz"):
        p = os.path.join(dump, fn)
        print(f"npz {fn:16s} {os.path.getsize(p) / 2**30:6.2f} GiB")
