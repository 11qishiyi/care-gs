import json, sys

p = r"D:\3dsg_1\experiments\artifacts\a4\m12_rd.json"
d = json.load(open(p, encoding="utf-8"))
print("top keys:", list(d.keys()))
sc = d["scenes"][0]
print("scene keys:", list(sc.keys()))
print("row keys:", list(sc["rows"][0].keys()))
print("sample row:", json.dumps(sc["rows"][0])[:300])
print("meta:", json.dumps(d.get("meta"))[:400])
