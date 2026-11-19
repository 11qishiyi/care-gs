import json, io, re
p = r"C:\Users\71736\.dsh\skills\research-expert-team\data\methods.json"
j = json.load(io.open(p, encoding="utf-8"))
# figure out the structure
print("top-level type:", type(j).__name__)
if isinstance(j, dict):
    print("keys:", list(j.keys())[:8])
    for k, v in list(j.items())[:2]:
        print(" sample", k, "->", str(v)[:200])
