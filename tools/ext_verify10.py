import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('_ok = "九个" in _t', '_ok = "十个" in _t')
s = s.replace('print(f"  {\'OK \' if _ok else \'FAIL\'} appendix title says nine: {_t[:24]}")',
              'print(f"  {\'OK \' if _ok else \'FAIL\'} appendix title says ten: {_t[:24]}")')
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- §3.7 self-check retraction ----------
SC = os.path.join(ROOT, "research", "results_v58", "selfcheck.json")
if os.path.isfile(SC):
    print("[3.7] self-check leaks coverage (circularity)")
    for r in json.load(io.open(SC, encoding="utf-8")):
        for k in ("prune50", "prune30"):
            e = 100 * r[f"{k}_selfcheck_err_mean"]
            checks += 1
            leak = e > 2.0
            print(f"  {'OK ' if leak else 'FAIL'} {r['scene']} {k}: self-check over-predicts "
                  f"by {e:+.1f}pp (> 2pp means it cannot detect staleness)")
            if not leak:
                fails.append(f"3.7 {r['scene']} {k} self-check not leaking")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: self-check checks added")
