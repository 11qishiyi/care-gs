import json, io
d = json.load(io.open("research/results_v22/cert_v3.json", encoding="utf-8"))
for r in d:
    if r["scene"] == "stump":
        print(f"{r['edit']:10s} stale={r.get('stale_cov_pix')} cov={r['cov_pix']:.4f} drift={r.get('drift_pix')}")
