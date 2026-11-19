import json, io
# ratio check for the "2-12x" claim
rows = []
for rel in ("research/results_v60/vt_flowers.json","research/results_v60/vt_rest.json"):
    rows += json.load(io.open(rel, encoding="utf-8"))
print(f"{'scene':9s} {'cert_drop':>10s} {'task_drop':>10s} {'ratio':>6s}")
for r in rows:
    cert = abs(100*r["voxel_prune30_drop_mean"])
    task = abs(100*(r["task_prune30_hit"] - r["task_clean_hit"]))
    print(f"{r['scene']:9s} {cert:>10.1f} {task:>10.1f} {task/cert:>6.1f}x")
