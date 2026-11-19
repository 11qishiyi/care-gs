import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- width-growth claims (§3.3) ----------
print("[3.3] interval width growth (400-split q values)")
WP = os.path.join(ROOT, "research", "results_v55", "widths.json")
if os.path.isfile(WP):
    wd = json.load(io.open(WP, encoding="utf-8"))
    g = [r["q_prune30_growth_pct"] for r in wd]
    check("3.3 width growth min (%)", min(g), 26, tol=1.0)
    check("3.3 width growth max (%)", max(g), 71, tol=1.0)
    print(f"  --   per-scene prune30 growth: " + " ".join(f"{x:+.0f}%" for x in g))

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: width checks added")
