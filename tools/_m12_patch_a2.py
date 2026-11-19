import io
Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()
old = '''                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None) -> float:'''
new = '''                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None, sh_pq: tuple = None) -> float:'''
assert old in s
io.open(Q, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
