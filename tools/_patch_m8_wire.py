"""Wire the M8 grid into the CLI choices and the byte-model gate (idempotent)."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(ROOT, "experiments", "qfp_rd.py")
C = os.path.join(ROOT, "experiments", "m1_check_bytes.py")

s = io.open(Q, encoding="utf-8").read()
old = 'choices=["custom", "m1", "m2", "m3", "m7"],'
new = 'choices=["custom", "m1", "m2", "m3", "m7", "m8"],'
if new not in s:
    assert old in s
    io.open(Q, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
    print("qfp_rd choices -> m8")
else:
    print("qfp_rd already has m8")

t = io.open(C, encoding="utf-8").read()
old2 = '"m7": Q.M7_VARIANTS}'
new2 = '"m7": Q.M7_VARIANTS, "m8": Q.M8_VARIANTS}'
if new2 not in t:
    assert old2 in t
    io.open(C, "w", encoding="utf-8", newline="\n").write(t.replace(old2, new2, 1))
    print("check_bytes grids -> m8")
else:
    print("check_bytes already has m8")
