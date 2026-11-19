import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- §3.1a three-way compact-model table ----------
print("[3.1a] three-way compact-model table")
TW = os.path.join(ROOT, "research", "results_v51", "three_way.json")
if os.path.isfile(TW):
    tw = {r["scene"]: r for r in json.load(io.open(TW, encoding="utf-8"))}
    for sc, want in (("flowers", -11.6), ("bicycle", -10.9),
                     ("treehill", -12.9), ("stump", -10.3)):
        check(f"3.1a {sc} drop(pp)", 100 * tw[sc]["drop_mean"], want, tol=0.15)
        checks += 1
        okc = abs(tw[sc]["clean_mean"] - 0.90) < 0.005
        print(f"  {'OK ' if okc else 'FAIL'} 3.1a {sc} clean coverage "
              f"{tw[sc]['clean_mean']:.3f} == nominal 0.900")
        if not okc:
            fails.append(f"3.1a {sc} clean coverage")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: 3.1a checks added")
