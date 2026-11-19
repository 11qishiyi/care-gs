"""The selftest must interpolate on the same rate grid it judges on."""
import io

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace("    out, means = curves(scenes, [5.0, 9.0, 20.0])",
              "    out, means = curves(scenes, [5.0, 9.0, 17.0, 20.0])", 1)

old = """    check("interpolated value is linear",
          abs(out["a"]["prune"]["3.3"] if False else out["a"]["prune"]["5.0"] - (-20.0)) < 1e-9,
          "5x is a measured knot")"""
new = """    check("a measured knot reproduces its own value",
          abs(out["a"]["prune"]["5.0"] - (-20.0)) < 1e-9,
          "prune at 5x is -20.0 pp")"""
assert old in s
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
