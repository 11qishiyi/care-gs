import io
P = r"D:\3dsg_1\experiments\m1_check_bytes.py"
s = io.open(P, encoding="utf-8").read()
old = '''            for name in names:
                total += 1
                spec = Q.parse_spec(name)'''
new = '''            for name in names:
                if not _splits(name, deg):
                    continue
                total += 1
                spec = Q.parse_spec(name)'''
assert old in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
