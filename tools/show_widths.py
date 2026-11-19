import io, json, os
ROOT = r"D:\3dsg_1"
def load(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)

qs = {}
# unified/main runs carry q_clean and <variant>_q
for rel in ("research/results_v53/edit_families.json",
            "research/results_v53/ef_bicycle.json",
            "research/results_v53/ef_rest.json",
            "research/results_v54/crit_a.json",
            "research/results_v54/crit_b.json",
            "research/results_v54/crit_c.json"):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        continue
    for r in load(rel):
        s = r["scene"]
        qs.setdefault(s, {})["clean"] = r.get("q_clean")
        for k in r:
            if k.endswith("_q"):
                qs[s][k[:-2]] = r[k]

print(f"{'scene':10s} {'q_clean':>8s} {'prune30 q':>10s} {'growth':>8s}")
for s, v in qs.items():
    q0 = v.get("clean"); q1 = v.get("prune30")
    if q0 and q1:
        print(f"{s:10s} {q0:8.4f} {q1:10.4f} {100*(q1/q0-1):+7.0f}%")
