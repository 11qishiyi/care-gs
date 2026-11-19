import json, io
for rel in ("research/results_v53/ef_rest.json","research/results_v53/ef_bicycle.json"):
    for r in json.load(io.open(rel, encoding="utf-8")):
        print(f"{r['scene']:9s} shdeg1 {100*r['shdeg1_drop_mean']:+.1f} "
              f"[{100*r['shdeg1_drop_lo']:+.1f},{100*r['shdeg1_drop_hi']:+.1f}]  "
              f"quant8 {100*r['quant8_drop_mean']:+.2f}")
