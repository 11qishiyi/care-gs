"""Widen the scalar ladder: band truncation and bit narrowing are the same knob family
(M8's J2 measured them as equivalent at matched bytes), so one ladder spanning both is
the honest curve for "how far does scalar SH coding go".
"""
import io

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()
old = '    "scalar": re.compile(r"^c\\d+_o8_sh\\d+$"),'
new = '    "scalar": re.compile(r"^(d\\d+_)?c\\d+_o8_sh\\d+$"),'
assert old in s, "ladder anchor missing"
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
