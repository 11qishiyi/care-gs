import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- figures must be regenerated from the current data ----------
print("[figures] freshness")
import subprocess
_fig_dir = os.path.join(ROOT, "figures")
_newest_data = 0
for rel in ("research/results_v52/many_splits.json", "research/results_v53/ef_rest.json",
            "research/results_v54/crit_c.json", "research/results_v55/widths.json"):
    q = os.path.join(ROOT, rel)
    if os.path.isfile(q):
        _newest_data = max(_newest_data, os.path.getmtime(q))
for f in ("fig1_edit_families.png", "fig2_interval_width.png",
          "fig3_alpha.png", "fig4_pruning_criterion.png"):
    q = os.path.join(_fig_dir, f)
    checks += 1
    fresh = os.path.isfile(q) and os.path.getmtime(q) >= _newest_data
    print(f"  {'OK ' if fresh else 'FAIL'} {f} is newer than its source data")
    if not fresh:
        fails.append(f"stale figure: {f}")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: figure freshness check added")
