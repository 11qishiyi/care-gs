import io

p = r"D:\3dsg_1\experiments\frontier.py"
s = io.open(p, encoding="utf-8").read()
a = 'SOURCES = ["m1_rd_measured", "m5_rd_v2", "m9_rd", "m10_rd", "m11_rd", "m12_rd"]'
b = ('SOURCES = ["m1_rd_measured", "m13_i7k", "m5_rd_v2", "m9_rd", "m10_rd",\n'
     '           "m11_rd", "m12_rd"]')
assert a in s, "SOURCES line not found"
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
print("ok")
