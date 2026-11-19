import io

P = r"D:\3dsg_1\experiments\run_m11.sh"
s = io.open(P, encoding="utf-8").read()
old = '''  "$PY" -m pip install --quiet plyfile pillow packaging "gsplat>=1.5,<2" zstandard'''
new = '''  # ``gsplat`` must be installed --no-deps: the plain requirement makes pip pull a
  # fresh torch (2.6 GB) even though the image already ships torch+cu124, which cost
  # ~11 minutes and 3.6 GB of wheel cache on 2026-11-14 before it was killed.
  "$PY" -m pip install --quiet plyfile pillow packaging zstandard
  "$PY" -c 'import gsplat' 2>/dev/null || "$PY" -m pip install --quiet --no-deps "gsplat>=1.5,<2"'''
assert old in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("patched run_m11.sh")
