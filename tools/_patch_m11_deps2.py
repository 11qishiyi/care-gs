import io

P = r"D:\3dsg_1\experiments\run_m11.sh"
s = io.open(P, encoding="utf-8").read()
old = '''  "$PY" -c 'import gsplat' 2>/dev/null || "$PY" -m pip install --quiet --no-deps "gsplat>=1.5,<2"'''
new = '''  "$PY" -c 'import gsplat' 2>/dev/null || "$PY" -m pip install --quiet --no-deps "gsplat>=1.5,<2"
  # --no-deps also skips imports that are not torch dependencies: rich (the JIT backend
  # banner) and jaxtyping.  Without rich the first render dies on ModuleNotFoundError.
  "$PY" -m pip install --quiet rich jaxtyping'''
assert old in s, "pattern missing"
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("patched")
