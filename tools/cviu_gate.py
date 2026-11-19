"""Gate: the four published 30%-prune drops must reproduce to 0.1 pp on this campaign."""
import json
import sys

EXPECT = {"bicycle": 22.1, "flowers": 10.8, "stump": 27.7, "treehill": 15.2}
a = json.load(open("results_v120/audit_bound.json", encoding="utf-8"))
got = {}
for r in a["rows"]:
    if r["variant"] == "prune30" and r["scene"] in EXPECT:
        got[r["scene"]] = -100 * r["drop_mean"]
worst = 0.0
for s, want in EXPECT.items():
    have = got.get(s)
    d = abs(have - want) if have is not None else float("inf")
    worst = max(worst, d)
    print(f"{s:10s} paper {want:5.1f}  this run {have:5.1f}  |d| {d:4.1f}")
print(f"worst |d| = {worst:.2f} pp -> {'PASS' if worst <= 0.1 else 'FAIL'}")
sys.exit(0 if worst <= 0.1 else 1)
