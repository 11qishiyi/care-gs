import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# the "drop is Nx the CI width" claim
ratios = []
for sname in SCENES_LIST:
    c = by[(sname, "clean")]
    p30 = by[(sname, "prune30")]
    width = c["ci_hi"] - c["ci_lo"]
    ratios.append(abs(p30["stale_cov_pix"] - c["cov_pix"]) / width)
print(f"  --   drop / CI-width ratios: " + " ".join(f"{r:.2f}" for r in ratios))
ok(1.4 <= min(ratios) and max(ratios) <= 2.8,
   f"claim '1.5-2.7x' consistent with data ({min(ratios):.2f}-{max(ratios):.2f})")
checks += 1
if not (1.4 <= min(ratios) and max(ratios) <= 2.8):
    fails.append("drop/CI-width claim")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: CI-width ratio check added")
