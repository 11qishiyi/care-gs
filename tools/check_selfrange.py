import json, io, os
R = r"D:\3dsg_1\research\results_v62"
vals = []
for s in ("garden","room","counter","kitchen","bonsai"):
    for k in ("base","small","ft"):
        p = os.path.join(R, f"{s}_{k}.json")
        if not os.path.isfile(p): continue
        rows = json.load(io.open(p, encoding="utf-8"))
        c = [r for r in rows if r["edit"]=="clean"][0]
        pr = [r for r in rows if r["edit"]=="prune30"][0]
        vals.append((s,k,100*(pr["stale_cov_pix"]-c["cov_pix"])))
print("  all 13:", " ".join(f"{v:+.1f}" for _,_,v in vals))
print("  range: %+.1f .. %+.1f" % (min(v for _,_,v in vals), max(v for _,_,v in vals)))
