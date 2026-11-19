"""Judge the best-family check on a rate the synthetic world actually covers."""
import io

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace("    out, means = curves(scenes, [5.0, 9.0, 17.0, 20.0])",
              "    out, means = curves(scenes, [5.0, 9.0, 17.0, 18.7, 20.0])", 1)

old = """    tab = best_coding(means, [17.0, 20.0], 3)
    check("best coding at 17x is a dictionary family",
          tab["17.0"]["best"] in ("vq", "rvq"), str(tab["17.0"]))"""
new = """    tab = best_coding(means, [17.0, 18.7, 20.0], 3)
    check("at 17x the scalar family is still the only one covered",
          tab["17.0"]["best"] == "scalar", str(tab["17.0"]))
    check("at 18.7x the residual dictionary wins",
          tab["18.7"]["best"] == "rvq", str(tab["18.7"]))"""
assert old in s
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
