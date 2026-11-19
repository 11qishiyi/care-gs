import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- appendix numbers ----------
print("[appendix] claims re-derived from data")
APP = os.path.join(ROOT, "APPENDIX_negative_results.md")
if os.path.isfile(APP):
    app = io.open(APP, encoding="utf-8").read()
    v6 = load("research/results_v6/var_flowers_err.json")
    check("N2 V_mm spearman", v6["err_corr_mm"], 0.241, tol=0.002)
    check("N2 V_ind spearman", v6["err_corr_ind"], 0.556, tol=0.002)
    check("N2 V_cpl spearman", v6["err_corr_cpl"], 0.274, tol=0.002)
    v8 = load("research/results_v8/occl_flowers.json")
    hid = [100 * r["hidden_frac"] for r in v8["rows"]]
    check("N5 occlusion bound min (%)", min(hid), 1.9, tol=0.1)
    check("N5 occlusion bound max (%)", max(hid), 3.2, tol=0.1)
    for sc, want in (("garden", -0.2), ("room", 3.2), ("counter", 0.0),
                     ("kitchen", 1.1), ("bonsai", -0.8)):
        rel = f"research/results_v35/{sc}.json"
        if os.path.isfile(os.path.join(ROOT, rel)):
            rows = load(rel)
            c = [r for r in rows if r["edit"] == "clean"][0]
            pr = [r for r in rows if r["edit"] == "prune30"][0]
            check(f"N9 {sc} drop (pp)", 100 * (pr["stale_cov_pix"] - c["cov_pix"]), want, tol=0.15)
    checks += 1
    _t = app.lstrip().splitlines()[0]
    _ok = "九个" in _t
    print(f"  {'OK ' if _ok else 'FAIL'} appendix title says nine: {_t[:24]}")
    if not _ok:
        fails.append("appendix title count")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: appendix checks added")
