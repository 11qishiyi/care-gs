import io

p = r"D:\3dsg_1\experiments\frontier.py"
s = io.open(p, encoding="utf-8").read()

a = 'ap.add_argument("--window", type=float, default=0.02)'
b = ('ap.add_argument("--window", type=float, default=0.05,\n'
     '                    help="budget tolerance: a point counts if rate <= N*(1+window)")')
assert a in s
s = s.replace(a, b, 1)

c = ('"；预算语义 = **实测码率 ≤ N×**（2% 舍入余量），**不外推、不插值**。")')
d = ('f"；预算语义 = **实测码率 ≤ N×**（{window*100:.0f}% 容差，仅为阶梯坐标误差），"\n'
     '               "**不外推、不插值**。")')
assert c in s
s = s.replace(c, d, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
