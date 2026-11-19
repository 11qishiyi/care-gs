import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
old = "| stump | 0.903 [0.854, 0.940] | 8 | **0.885** | **−12.5** | ✅ |"
new = "| stump | 0.903 [0.854, 0.940] | 8 | **0.778** | **−12.5** | ✅ |"
assert old in s, "row not found"
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("fixed stump prune30 value: 0.885 -> 0.778")
