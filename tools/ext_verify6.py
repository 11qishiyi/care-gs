import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
# the main table now comes from the 400-split run; verify those numbers too
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- main table from the 400-split protocol ----------
print("[3.1] main table (400 random splits)")
MS = os.path.join(ROOT, "research", "results_v52", "many_splits.json")
if os.path.isfile(MS):
    ms = json.load(io.open(MS, encoding="utf-8"))
    want = {("flowers", 0.3): -10.9, ("bicycle", 0.3): -18.6,
            ("treehill", 0.3): -12.8, ("stump", 0.3): -11.7,
            ("flowers", 0.5): -3.6, ("bicycle", 0.5): -5.3,
            ("treehill", 0.5): -4.5, ("stump", 0.5): -2.1}
    for r in ms:
        key = (r["scene"], round(r["ratio"], 1))
        if key in want:
            check(f'3.1 {key[0]} prune{int(key[1]*100)} drop(pp)',
                  100 * r["drop_mean"], want[key], tol=0.15)
        checks += 1
        okc = abs(r["clean_mean"] - 0.90) < 0.01
        print(f"  {'OK ' if okc else 'FAIL'} {r['scene']} clean coverage "
              f"{r['clean_mean']:.3f} near nominal 0.90")
        if not okc:
            fails.append(f"{r['scene']} clean coverage")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
s = s.replace('if __name__', 'if __name__')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: 400-split main table checks added")
