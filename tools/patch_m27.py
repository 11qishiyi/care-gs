import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()
old = '    order, _, _, _ = group(splats["means"], meta["voxel"])'
new = '    order = group(splats["means"], meta["voxel"])[0]'
assert old in s
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")
