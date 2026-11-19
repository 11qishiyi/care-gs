import json, io
d = json.load(io.open("research/results_v51/three_way.json", encoding="utf-8"))
print(f"{'scene':10s} {'clean':>7s} {'stale':>7s} {'drop%':>8s} {'CI':>18s}")
for r in d:
    print(f"{r['scene']:10s} {r['clean_mean']:.3f} {r['stale_mean']:>7.3f} "
          f"{100*r['drop_mean']:>+7.1f}  [{100*r['drop_lo']:+.1f},{100*r['drop_hi']:+.1f}]")
