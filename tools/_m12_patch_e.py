import io
P = r"D:\3dsg_1\experiments\m1_check_bytes.py"
s = io.open(P, encoding="utf-8").read()
old = '''             "m7": Q.M7_VARIANTS, "m8": Q.M8_VARIANTS, "m9": Q.M9_VARIANTS,
             "m10": Q.M10_VARIANTS}'''
new = '''             "m7": Q.M7_VARIANTS, "m8": Q.M8_VARIANTS, "m9": Q.M9_VARIANTS,
             "m10": Q.M10_VARIANTS, "m11": Q.M11_VARIANTS, "m12": Q.M12_VARIANTS}'''
assert old in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
