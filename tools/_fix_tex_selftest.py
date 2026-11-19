import io

p = r"D:\3dsg_1\experiments\frontier_tex.py"
s = io.open(p, encoding="utf-8").read()
a = '''    check("each asset gets a row", tex.count("sh12\\\\_g16") == 1 and "| a |" in tex.replace("\\\\\\\\", "|"))'''
b = '''    lines = [ln for ln in tex.splitlines() if ln.startswith("a & ") or ln.startswith("b & ")]
    check("each asset gets a row", len(lines) == 2, f"{len(lines)} row(s)")'''
assert a in s, "assertion line not found"
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
print("ok")
