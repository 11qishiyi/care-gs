import io, json
# values transcribed from the run logs of edit_families.py / criteria_stats.py
# (the JSON for the flowers run was lost to an OOM crash; these are the printed numbers)
rows = [
 dict(scene="flowers", q_clean=0.1541, q_prune50=0.1845, q_prune30=0.2376,
      q_shdeg1=0.1717, q_quant8=0.1575),
 dict(scene="bicycle", q_clean=0.1871, q_prune30=0.3204, q_shdeg1=0.2174, q_quant8=0.2097),
 dict(scene="treehill", q_clean=0.2357, q_prune30=0.3360, q_shdeg1=0.1954, q_quant8=0.1931),
 dict(scene="stump", q_clean=0.2996, q_prune30=0.3772, q_shdeg1=0.3097, q_quant8=0.3008),
]
for r in rows:
    for k in list(r):
        if k.startswith("q_") and k != "q_clean":
            r[k + "_growth_pct"] = round(100 * (r[k] / r["q_clean"] - 1), 1)
json.dump(rows, open(r"D:\3dsg_1\research\results_v55\widths.json", "w", encoding="utf-8"),
          indent=1)
print(json.dumps([{k: r[k] for k in r if k.endswith("growth_pct") or k == "scene"} for r in rows],
                 indent=1))
