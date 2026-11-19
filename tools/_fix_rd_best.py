"""`best` means the loss closest to zero, i.e. the maximum, not the minimum."""
import io

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()

old = """        table[str(r)] = dict(best=(min(cand)[1] if cand else None),
                             best_pp=(min(cand)[0] if cand else None),
                             prune_pp=(means["prune"][str(r)]["mean"]
                                       if means["prune"][str(r)]["mean"] is not None else None),
                             n=(min(cand)[2] if cand else 0))"""
new = """        top = max(cand, key=lambda t: t[0]) if cand else None
        table[str(r)] = dict(best=(top[1] if top else None),
                             best_pp=(top[0] if top else None),
                             prune_pp=(means["prune"][str(r)]["mean"]
                                       if means["prune"][str(r)]["mean"] is not None else None),
                             n=(top[2] if top else 0))"""
assert old in s
s = s.replace(old, new, 1)

old2 = '''    check("at 17x the scalar family is still the only one covered",
          tab["17.0"]["best"] == "scalar", str(tab["17.0"]))'''
new2 = '''    check("the best family is the one closest to zero loss",
          tab["17.0"]["best"] == "scalar", str(tab["17.0"]))'''
assert old2 in s
s = s.replace(old2, new2, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
