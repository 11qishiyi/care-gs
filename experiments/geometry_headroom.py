"""How much does packing the geometry buy?  A purely arithmetic estimate from measured rates.

The quaternion is 4 of the 11 geometric scalars.  A unit quaternion lives on a 3-sphere, and
"smallest three" (store the index of the largest component plus the other three at b bits)
codes it in 2 + 3b bits: 11 bits at b=3, i.e. 1.4 B instead of 4 B.  Dropping opacity to 4
bits and the scalars to 5 bits saves about as much again.  This script only asks what a
3 B/primitive saving would do to the ratios and to the 12x shelf, using measured bytes.
"""
import glob
import json
import os

A4 = os.path.join("experiments", "artifacts", "a4")
FP32 = 236.0
SAVE = 3.0

WANT = ["m16_o6_sh3", "m16_o6_sh2", "m16_o8_sh3", "m16_o8_sh2",
        "c10_o8_sh3", "c8_o8_sh3", "c8_o8_sh2", "sh4_g16", "sh4_g32"]

seen = {}
for path in sorted(glob.glob(os.path.join(A4, "*.json"))):
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(doc, dict) or "scenes" not in doc:
        continue
    for sc in doc["scenes"]:
        if not isinstance(sc, dict):
            continue
        for row in sc.get("rows", []):
            name = row.get("variant")
            if name in WANT and row.get("rate"):
                key = (sc["scene"], name)
                if key not in seen:
                    seen[key] = (float(row["bytes_per_prim"]), float(row["rate"]),
                                 float(row["drop_pp"]))

print(f"{'asset':12s} {'variant':12s} {'B/prim':>7s} {'rate':>6s} {'drop':>7s} "
      f"{'packed':>7s} {'newrate':>7s}")
for (scene, name) in sorted(seen):
    bpp, rate, drop = seen[(scene, name)]
    packed = max(bpp - SAVE, 1.0)
    new_rate = rate * bpp / packed
    print(f"{scene:12s} {name:12s} {bpp:7.2f} {rate:6.2f} {drop:+7.2f} "
          f"{packed:7.2f} {new_rate:7.2f}")

print()
print("12x shelf check: which variants would cross 12x at their *current* quality")
for (scene, name) in sorted(seen):
    bpp, rate, drop = seen[(scene, name)]
    packed = bpp - SAVE
    new_rate = rate * bpp / packed
    if rate < 12.0 <= new_rate:
        print(f"  {scene:12s} {name:12s} {rate:5.2f}x -> {new_rate:5.2f}x at "
              f"{drop:+.2f} pp")
