import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")
old = "shipping by simulating the edit family, so it\ndeclares how much damage it tolerates."
new = "shipping by simulating the edit family, so it\ndeclares its damage tolerance."
assert old in t
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("trimmed")
