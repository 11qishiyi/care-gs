import io
P = r"D:\3dsg_1\experiments\m11_report.py"
s = io.open(P, encoding="utf-8").read()
old = '''    miss = evaluate(_synth(2.0))
    check("P3 reports under_covered rather than fail",'''
new = '''    miss_doc = _synth(2.0)
    for sc in miss_doc["scenes"]:
        sc["rows"] = [r for r in sc["rows"] if r["rate"] < 18.0]
    miss = evaluate(miss_doc)
    check("P3 reports under_covered rather than fail",'''
assert old in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
