import pathlib

p = pathlib.Path("tools/cviu_audit_tables.py")
t = p.read_text(encoding="utf-8")
n = 0
for name in ("tab_audit.tex", "tab_kview.tex", "tab_fidelity.tex"):
    old = ('open(os.path.join(out_dir, "%s"), "w", encoding="utf-8").write(tex)'
           % name)
    new = '_emit(out_dir, "%s", tex)' % name
    if old in t:
        t = t.replace(old, new)
        n += 1
p.write_text(t, encoding="utf-8")
print("replaced", n)
