import io

p = "tools/m25_time.py"
lines = io.open(p, encoding="utf-8").read().splitlines(True)
out = []
for ln in lines:
    if 'ap.add_argument("--glob"' in ln and "\\n" in ln:
        out.append('    ap.add_argument("--glob", default="*_auto.gs1")\n')
    else:
        out.append(ln)
io.open(p, "w", encoding="utf-8").write("".join(out))
print("repaired", len(out))
