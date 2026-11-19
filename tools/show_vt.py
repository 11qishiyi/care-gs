import json, io
rows = []
for rel in ("research/results_v60/vt_flowers.json", "research/results_v60/vt_rest.json"):
    rows += json.load(io.open(rel, encoding="utf-8"))
print(f"{'scene':10s} {'vox_clean':>10s} {'v50':>7s} {'v30':>7s} | {'task_clean':>10s} {'t50':>6s} {'t30':>6s} {'task_drop':>9s}")
for r in rows:
    tc, t3 = r["task_clean_hit"], r["task_prune30_hit"]
    print(f"{r['scene']:10s} {r['voxel_clean_mean']:>10.3f} "
          f"{100*r['voxel_prune50_drop_mean']:>+6.1f} {100*r['voxel_prune30_drop_mean']:>+6.1f} | "
          f"{tc:>10.3f} {r['task_prune50_hit']:>6.3f} {t3:>6.3f} {100*(t3-tc):>+8.1f}")
