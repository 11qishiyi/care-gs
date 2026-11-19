import io, json, os
ROOT = r"D:\3dsg_1"
def load(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)

print("=== N2 (results_v6) ===")
d = load("research/results_v6/var_flowers_err.json")
for k in ("err_corr_mm", "err_corr_ind", "err_corr_cpl", "median_ratio_mm"):
    print(f"  {k} = {d.get(k)}")

print("=== N5 (results_v8) ===")
o = load("research/results_v8/occl_flowers.json")
for r in o["rows"]:
    print(f"  {r['W']}x{r['H']}: hidden={100*r['hidden_frac']:.1f}%")

print("=== N9 (results_v35) ===")
for s in ("garden","room","counter","kitchen","bonsai"):
    p = os.path.join(ROOT, "research", "results_v35", f"{s}.json")
    if os.path.isfile(p):
        rows = json.load(io.open(p, encoding="utf-8"))
        c = [r for r in rows if r["edit"]=="clean"][0]
        pr = [r for r in rows if r["edit"]=="prune30"][0]
        print(f"  {s}: n={c['n']} clean={c['cov_pix']:.3f} prune30={pr['stale_cov_pix']:.3f} "
              f"drop={100*(pr['stale_cov_pix']-c['cov_pix']):+.1f}pp")
