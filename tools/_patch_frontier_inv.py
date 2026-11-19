import io

p = r"D:\3dsg_1\experiments\frontier.py"
s = io.open(p, encoding="utf-8").read()
a = '''    check("the inverse picks the cheapest point inside the tolerance",
          inv["a"][3.0]["variant"] == "p50", inv["a"][3.0]["variant"])'''
b = '''    check("the inverse picks the cheapest point inside the tolerance",
          inv["a"][3.0]["variant"] == "pq4-4_c8_o8", inv["a"][3.0]["variant"])'''
assert a in s
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
print("patched")
