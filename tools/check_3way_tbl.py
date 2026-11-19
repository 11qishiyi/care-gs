import json, io, re
d = json.load(io.open(r"D:\3dsg_1\research\results_v51\three_way.json", encoding="utf-8"))
paper = io.open(r"D:\3dsg_1\PAPER_certificate_invalid.md", encoding="utf-8").read()
for r in d:
    val = f"{100*r['drop_mean']:+.1f}"
    ok = val.replace("+","−") in paper or val in paper
    print(f"  {'OK ' if ok else 'CHECK'} {r['scene']}: {val}pp present in paper")
