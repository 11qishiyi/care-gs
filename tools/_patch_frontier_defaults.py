import io

p = r"D:\3dsg_1\experiments\frontier.py"
s = io.open(p, encoding="utf-8").read()
a = 'ap.add_argument("--window", type=float, default=0.10)'
b = 'ap.add_argument("--window", type=float, default=0.02)'
assert a in s, "window default not found"
s = s.replace(a, b)
c = 'abs(row12["max_rate"] - 12.2)'
d = 'abs(row12["max_rate"] - 12.0)'
if c in s:
    s = s.replace(c, d)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
