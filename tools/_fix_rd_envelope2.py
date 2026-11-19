"""Coverage loss is negative-is-worse, so the envelope must keep *improvements* (v > best).

The first version kept ``v < best``, which is the wrong direction: it walked towards the
worst member of each family instead of the best one.
"""
import io

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()

old = """        if best is None or v < best - 1e-12:"""
new = """        if best is None or v > best + 1e-12:"""
assert old in s
s = s.replace(old, new, 1)

old2 = '''    bad = envelope([(9.0, -0.5, "good"), (12.0, -9.0, "bad"), (15.0, -0.9, "worse")])
    check("the envelope drops dominated points",
          [n for _, _, n in bad] == ["good"], str([n for _, _, n in bad]))'''
new2 = '''    env = envelope([(9.0, -2.0, "coarse"), (12.0, -0.5, "better"),
                    (15.0, -0.9, "dominated")])
    check("the envelope keeps only improving points",
          [n for _, _, n in env] == ["coarse", "better"], str([n for _, _, n in env]))'''
assert old2 in s
s = s.replace(old2, new2, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
