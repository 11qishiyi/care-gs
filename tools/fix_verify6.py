import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''ok(1.4 <= min(ratios) and max(ratios) <= 2.8,
   f"claim '1.5-2.7x' consistent with data ({min(ratios):.2f}-{max(ratios):.2f})")
checks += 1
if not (1.4 <= min(ratios) and max(ratios) <= 2.8):
    fails.append("drop/CI-width claim")''',
'''_ok = 1.4 <= min(ratios) and max(ratios) <= 2.8
checks += 1
print(f"  {'OK ' if _ok else 'FAIL'} claim '1.5-2.7x' vs data "
      f"{min(ratios):.2f}-{max(ratios):.2f}")
if not _ok:
    fails.append("drop/CI-width claim")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed")
