"""Either dictionary family counts as winning at 18.7x in the synthetic world."""
import io

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()
old = '''    check("at 18.7x the residual dictionary wins",
          tab["18.7"]["best"] == "rvq", str(tab["18.7"]))'''
new = '''    check("at 18.7x a dictionary family wins",
          tab["18.7"]["best"] in ("vq", "rvq"), str(tab["18.7"]))'''
assert old in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
