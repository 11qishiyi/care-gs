import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''print(f"\\n{checks} numeric checks, {len(fails)} failures")''',
'''# ---------- abstract-level summary claims ----------
print("[abstract] summary ranges")
drops = []
for sname in SCENES_LIST:
    c = by[(sname, "clean")]["cov_pix"]
    d = 100 * (by[(sname, "prune30")]["stale_cov_pix"] - c)
    drops.append(d)
check("abstract drop min (pp, abs)", min(drops), 11.4, tol=0.2)
check("abstract drop max (pp, abs)", max(drops), 20.6, tol=0.2)
drifts = []
for sname in SCENES_LIST:
    c = by[(sname, "clean")]["cov_pix"]
    for e in ("shdeg1", "quant8_sh"):
        drifts.append(abs(100 * (by[(sname, e)]["cov_pix"] - c)))
check("abstract appearance/precision max |drift| (pp)", max(drifts), 0.7, tol=0.05)
grow = [100 * (by[(sn, "prune30")]["q_pix"] / by[(sn, "clean")]["q_pix"] - 1) for sn in SCENES_LIST]
check("abstract width growth min (%)", min(grow), 26, tol=1.0)
check("abstract width growth max (%)", max(grow), 83, tol=1.0)

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
s = s.replace('SCENES = ["flowers", "treehill", "bicycle", "stump"]',
              'SCENES = ["flowers", "treehill", "bicycle", "stump"]\nSCENES_LIST = SCENES')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier extended with abstract-level checks")
