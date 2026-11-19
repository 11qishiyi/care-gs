import json, io
d = json.load(io.open("research/results_v22/cert_v3.json", encoding="utf-8"))
print(f"{'scene':10s} {'edit':9s} {'n':>9s} {'q(半宽)':>9s} {'cov':>6s}")
for r in d:
    print(f"{r['scene']:10s} {r['edit']:9s} {r['n']:>9d} {r['q_pix']:>9.4f} {r['cov_pix']:>6.3f}")
