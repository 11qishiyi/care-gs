"""Point m32_analyse at the corrected coefficient metric (error against the original 45 columns)."""
import io

P = "tools/m32_analyse.py"
s = io.open(P, encoding="utf-8").read()

old_load = '''        coef_path = os.path.join(a.root, f"coef_{scene}.json")
        coef = {}
        if os.path.exists(coef_path):
            coef = {r["plan"]: r["rel_rmse"] for r in json.load(open(coef_path, encoding="utf-8"))}'''
new_load = '''        coef_path = os.path.join(a.root, f"coef2_{scene}.json")
        if not os.path.exists(coef_path):
            coef_path = os.path.join(a.root, f"coef_{scene}.json")
        coef, coef_naive = {}, {}
        if os.path.exists(coef_path):
            for r in json.load(open(coef_path, encoding="utf-8")):
                coef[r["plan"]] = r["rel_rmse_full"] if "rel_rmse_full" in r else r["rel_rmse"]
                coef_naive[r["plan"]] = r["rel_rmse"]'''
assert old_load in s
s = s.replace(old_load, new_load)

old_row = '''                         "coef": coef.get(plan)})'''
new_row = '''                         "coef": coef.get(plan), "coef_naive": coef_naive.get(plan)})'''
assert old_row in s
s = s.replace(old_row, new_row)

old_head = '''        print("| plan | file | ratio | PSNR | delta vs ship | bytes vs ship | coef rel_rmse |")
        print("|---|---|---|---|---|---|---|")'''
new_head = '''        print("| plan | file | ratio | PSNR | delta vs ship | bytes vs ship | coef err (full) | "
              "coef err (in subspace) |")
        print("|---|---|---|---|---|---|---|---|")'''
assert old_head in s
s = s.replace(old_head, new_head)

old_line = '''                  f"{('%.2f%%' % (100*r['coef'])) if r['coef'] is not None else '--'} |")'''
new_line = '''                  f"{('%.2f%%' % (100*r['coef'])) if r['coef'] is not None else '--'} | "
                  f"{('%.2f%%' % (100*r['coef_naive'])) if r['coef_naive'] is not None else '--'} |")'''
assert old_line in s
s = s.replace(old_line, new_line)

old_j4 = '''            print(f"   J4 Spearman(coef error, PSNR) = {spearman(err, ps):+.3f}  (want -1.000)")'''
new_j4 = '''            print(f"   J4 Spearman(coef error full, PSNR) = {spearman(err, ps):+.3f}  (want -1.000)")
        naive = [(r["coef_naive"], r["psnr"]) for r in rows
                 if r["coef_naive"] is not None and r["psnr"] is not None]
        if len(naive) >= 3:
            print(f"   J4 Spearman(in-subspace error, PSNR) = "
                  f"{spearman([n[0] for n in naive], [n[1] for n in naive]):+.3f}  (the naive metric)")'''
assert old_j4 in s
s = s.replace(old_j4, new_j4)

io.open(P, "w", encoding="utf-8").write(s)
print("patched", P)
