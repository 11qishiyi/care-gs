import io
P = r"D:\3dsg_1\experiments\m1_check_bytes.py"
s = io.open(P, encoding="utf-8").read()
old = '''    grids = {"m1": Q.DEFAULT_VARIANTS, "m2": Q.AFQ_VARIANTS, "m3": Q.M3_VARIANTS,'''
new = '''    # Product quantisation splits the block, so it only exists for degrees whose
    # coefficient count is divisible by the group count; skip those pairs instead of
    # pretending the variant is measurable there.
    def _splits(name, deg):
        tok = [t for t in name.split("_") if t.startswith("pq")]
        if not tok:
            return True
        m = int(tok[0][2:].split("-")[0])
        return Q.sh_cols(deg) % m == 0

    grids = {"m1": Q.DEFAULT_VARIANTS, "m2": Q.AFQ_VARIANTS, "m3": Q.M3_VARIANTS,'''
assert old in s
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
