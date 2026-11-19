import io

P = r"D:\3dsg_1\experiments\run_m11.sh"
s = io.open(P, encoding="utf-8").read()
old = '''  "$PY" -m pip install --quiet rich jaxtyping'''
new = '''  "$PY" -m pip install --quiet rich jaxtyping ninja'''
assert old in s
s = s.replace(old, new, 1)
s = s.replace('''  # --no-deps also skips imports that are not torch dependencies: rich (the JIT backend
  # banner) and jaxtyping.  Without rich the first render dies on ModuleNotFoundError.''',
              '''  # --no-deps also skips imports that are not torch dependencies: rich (the JIT backend
  # banner), jaxtyping, and ninja (the JIT compiles the CUDA sources on first use).  The
  # 2026-11-14 node needed all three before the first render succeeded.''')
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
