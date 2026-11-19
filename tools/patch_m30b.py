import io

p = "experiments/m30_adapt.py"
s = io.open(p, encoding="utf-8").read()

if "target_div" in s:
    print("already wired")
    raise SystemExit(0)

s = s.replace(
    "          level: int = 12, log=print) -> dict:",
    "          level: int = 12, target_div: float = None, log=print) -> dict:", 1)
s = s.replace(
    "    bits = choose_bits(ext, lo=lo, hi=hi, ref=float((1 << int(nominal)) - 1))",
    "    ref = float(target_div if target_div else (1 << int(nominal)) - 1)\n"
    "    bits = choose_bits(ext, lo=lo, hi=hi, ref=ref)", 1)
s = s.replace(
    '    ap.add_argument("--selftest", action="store_true")',
    '    ap.add_argument("--target-div", type=float, default=None)\n'
    '    ap.add_argument("--selftest", action="store_true")', 1)
s = s.replace(
    "    row = adapt(a.gs1, a.out, nominal=a.nominal, lo=a.lo, hi=a.hi, level=a.level, log=log)",
    "    row = adapt(a.gs1, a.out, nominal=a.nominal, lo=a.lo, hi=a.hi, level=a.level,\n"
    "                target_div=a.target_div, log=log)", 1)
s = s.replace('            "nominal": int(nominal)}',
              '            "nominal": int(nominal), "target_div": float(target_div or 0)}', 1)
io.open(p, "w", encoding="utf-8").write(s)
print("target_div wired")
