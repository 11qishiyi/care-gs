import json, io, os
ROOT = r"D:\3dsg_1\research\results_v62"
print(f"{'scene':9s} {'state':6s} {'n':>8s} {'clean':>7s} {'stale':>7s} {'drop':>8s}")
for s in ("garden","room","counter","kitchen","bonsai"):
    for k in ("base","small","ft"):
        p = os.path.join(ROOT, f"{s}_{k}.json")
        if not os.path.isfile(p):
            continue
        rows = json.load(io.open(p, encoding="utf-8"))
        c = [r for r in rows if r["edit"] == "clean"][0]
        pr = [r for r in rows if r["edit"] == "prune30"][0]
        print(f"{s:9s} {k:6s} {c['n']:>8d} {c['cov_pix']:>7.3f} {pr['stale_cov_pix']:>7.3f} "
              f"{100*(pr['stale_cov_pix']-c['cov_pix']):>+7.1f}")
