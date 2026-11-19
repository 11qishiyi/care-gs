import io
p = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(p, encoding="utf-8").read()
old = 'choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9"],'
new = 'choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9", "m10"],'
assert old in s, "anchor missing"
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("patched")
