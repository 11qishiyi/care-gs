import io
P = r"D:\3dsg_1\experiments\frontier.py"
s = io.open(P, encoding="utf-8").read()
old = '''    check("the table renders the mean", "+" in md and "12.0\u00d7" in md)'''
new = '''    check("the table renders the mean", "12.0\u00d7" in md and "pp**" in md)'''
assert old in s, "pattern missing"
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
