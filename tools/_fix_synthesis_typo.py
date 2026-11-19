import io

P = r"D:\3dsg_1\experiments\METHOD_SYNTHESIS.md"
s = io.open(P, encoding="utf-8").read()
a = "| ≤0.25 pp | 2.14 – 7.71×（中位 ~4.7×） |"
b = "| ≤0.25 pp | 2.10 – 7.71×（中位 ~4.7×） |"
assert a in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
print("ok")
