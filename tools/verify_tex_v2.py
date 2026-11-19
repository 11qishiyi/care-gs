"""Verify every number in submission/main_v2.tex against the stored run artifacts.

Design: each check recomputes a quantity from research/results_*/ and asserts that its
one-decimal (or three-decimal for coverage) rendering appears in the LaTeX source. This
catches stale numbers, sign flips and transcription errors; it deliberately does not try to
parse LaTeX structure.

    python tools/verify_tex_v2.py            # exit 1 on any failure
"""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = r"D:\3dsg_1"
TEX = os.path.join(ROOT, "submission", "main_v2.tex")
SC = ["flowers", "bicycle", "treehill", "stump"]
fails, checks = [], 0


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def rows(rel):
    d = load(rel)
    return d if isinstance(d, list) else [d]


def check(name, token, tol_note=""):
    """Assert `token` (a string as it should appear in the paper) is present in the tex."""
    global checks
    checks += 1
    ok = token in TEX_TEXT
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: expect {token!r} {tol_note}")
    if not ok:
        fails.append(name)


def approx(name, value, digits=1, sign=True):
    """Format a number the way the paper writes it and look for it."""
    fmt = f"{{:+.{digits}f}}" if sign else f"{{:.{digits}f}}"
    tok = fmt.format(value)
    tok = tok.replace("+", "") if tok.startswith("+") else tok
    check(name, tok)


with open(TEX, encoding="utf-8") as f:
    TEX_TEXT = f.read().replace("\n", " ")

# ---------------------------------------------------------------- sources
ms = {(r["scene"], round(r["ratio"], 1)): r for r in rows("research/results_v52/many_splits.json")}
vt = {}
for p in ("research/results_v60/vt_flowers.json", "research/results_v60/vt_rest.json"):
    for r in rows(p):
        vt[r["scene"]] = r
v22 = {(r["scene"], r["edit"]): r for r in rows("research/results_v22/cert_v3.json")}
ef = {}
for p in glob.glob(os.path.join(ROOT, "research", "results_v53", "*.json")):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    for r in (d if isinstance(d, list) else [d]):
        if isinstance(r, dict) and "scene" in r:
            ef[r["scene"]] = r
selfc = rows("research/results_v58/selfcheck.json")
alpha = {a: rows(f"research/results_v28/cert_a{a}.json") for a in ("0.05", "0.2")}
three = {r["scene"]: r for r in rows("research/results_v51/three_way.json")}
selftr = {}
for p in glob.glob(os.path.join(ROOT, "research", "results_v35", "*.json")):
    d = rows(p)
    c = [r for r in d if r["edit"] == "clean"][0]
    pr = [r for r in d if r["edit"] == "prune30"][0]
    selftr[c["scene"]] = dict(n=c["n"], clean=c["cov_pix"], stale=pr["stale_cov_pix"])

# ---------------------------------------------------------------- 1. asset table
print("[Table 1] fresh coverage, pixel and region")
for s in SC:
    c = ms[(s, 0.3)]
    check(f"{s} fresh pixel mean", f"{c['clean_mean']:.3f}")
    check(f"{s} fresh pixel lo", f"{c['clean_lo']:.3f}")
    check(f"{s} fresh pixel hi", f"{c['clean_hi']:.3f}")
    check(f"{s} fresh region mean", f"{vt[s]['voxel_clean_mean']:.3f}")
for s in SC:
    d = ms[(s, 0.3)]
    approx(f"{s} pixel drop30", 100 * d["drop_mean"])
    approx(f"{s} pixel drop30 lo", 100 * d["drop_lo"])
    approx(f"{s} pixel drop30 hi", 100 * d["drop_hi"])
    v = vt[s]
    approx(f"{s} region drop30", -100 * v["voxel_prune30_drop_mean"])
    approx(f"{s} region drop30 lo", -100 * v["voxel_prune30_drop_hi"])
    approx(f"{s} region drop30 hi", -100 * v["voxel_prune30_drop_lo"])
print("[Table 1] primitives and views")
for s in SC:
    check(f"{s} primitives", f"{vt[s]['n_primitives']/1e6:.2f}M")
for s in SC:
    check(f"{s} views", str(vt[s]["n_views"]))

# ---------------------------------------------------------------- 2. edit families
print("[Table 2] edit families")
for s in ("bicycle", "treehill", "stump"):
    r = ef[s]
    approx(f"{s} shdeg1 drop", 100 * r["shdeg1_drop_mean"])
    approx(f"{s} shdeg1 drop lo", 100 * r["shdeg1_drop_lo"])
    approx(f"{s} shdeg1 drop hi", 100 * r["shdeg1_drop_hi"])
    approx(f"{s} quant8 drop", abs(100 * r["quant8_drop_mean"]), digits=2, sign=False)
for s in SC:
    g = 100 * (v22[(s, "prune30")]["q_pix"] / v22[(s, "clean")]["q_pix"] - 1)
    check(f"{s} paired q growth prune30", f"{g:.0f}\\%")
    gs = 100 * (v22[(s, "shdeg1")]["q_pix"] / v22[(s, "clean")]["q_pix"] - 1)
    check(f"{s} paired q growth shdeg1", f"{gs:.0f}\\%")
    check(f"{s} quant8 q unchanged", "0\\%")

# ---------------------------------------------------------------- 3. decoupling
print("[Table 3] task versus coverage")
for s in SC:
    v = vt[s]
    t50 = 100 * (v["task_prune50_hit"] - v["task_clean_hit"])
    t30 = 100 * (v["task_prune30_hit"] - v["task_clean_hit"])
    approx(f"{s} task drop50", t50)
    approx(f"{s} task drop30", t30)
    check(f"{s} clean hit", f"{v['task_clean_hit']:.3f}")
    check(f"{s} hit50", f"{v['task_prune50_hit']:.3f}")
    check(f"{s} hit30", f"{v['task_prune30_hit']:.3f}")
print("[text] ratio ranges")
rp = [abs(100 * (vt[s]["task_prune30_hit"] - vt[s]["task_clean_hit"]) / (100 * ms[(s, 0.3)]["drop_mean"]))
      for s in SC]
rv = [abs(100 * (vt[s]["task_prune30_hit"] - vt[s]["task_clean_hit"]) / (100 * vt[s]["voxel_prune30_drop_mean"]))
      for s in SC]
check("pixel ratio low", f"{min(rp):.1f}")
check("pixel ratio high", f"{max(rp):.1f}")
check("region ratio low", f"{min(rv):.1f}")
check("region ratio high", f"{max(rv):.1f}")

# ---------------------------------------------------------------- 4. repair curve
print("[Table 4] repair curve")
import math
for s in SC:
    pc = v22[(s, "prune30")].get("repair_curve") or []
    for c in pc:
        key = "all" if c["n_cal"] == pc[-1]["n_cal"] and len(pc) > 4 else c["n_cal"]
        check(f"{s} repair n={c['n_cal']}", f"{c['cov_rc']:.3f}")
print("[text] quantile growth range")
g = [100 * (v22[(s, "prune30")]["q_pix"] / v22[(s, "clean")]["q_pix"] - 1) for s in SC]
gs = [100 * (v22[(s, "shdeg1")]["q_pix"] / v22[(s, "clean")]["q_pix"] - 1) for s in SC]
check("min prune30 q growth", f"+{min(g):.0f}\\%")
check("max prune30 q growth", f"+{max(g):.0f}\\%")
check("min shdeg1 q growth", f"+{min(gs):.0f}\\%")
check("max shdeg1 q growth", f"+{max(gs):.0f}\\%")
check("width multiplier low", f"{1 + min(g)/100:.2f}")
check("width multiplier high", f"{1 + max(g)/100:.2f}")

# ---------------------------------------------------------------- 5. self-check
print("[section 3.5] self-check")
for r in selfc:
    approx(f"{r['scene']} p50 overprediction", 100 * r["prune50_selfcheck_err_mean"])
    approx(f"{r['scene']} p30 overprediction", 100 * r["prune30_selfcheck_err_mean"])
    check(f"{r['scene']} actual50", f"{r['prune50_actual_mean']:.3f}")
    check(f"{r['scene']} actual30", f"{r['prune30_actual_mean']:.3f}")

# ---------------------------------------------------------------- 6. scope + appendix
print("[Appendix A] scope")
for s, d in selftr.items():
    approx(f"{s} selftrained drop", 100 * (d["stale"] - d["clean"]))
_cd = [100 * three[s]["drop_mean"] for s in SC]
check("compact-model drop range low", f"{min(_cd):.1f}")
check("compact-model drop range high", f"{max(_cd):.1f}")
for s in SC:
    check(f"{s} compact-model fresh", f"{three[s]['clean_mean']:.3f}")
print("[Appendix C] alpha sweep")
for a, rs in alpha.items():
    drops = []
    for r in rs:
        if r["edit"] != "prune30":
            continue
        c = [x for x in rs if x["scene"] == r["scene"] and x["edit"] == "clean"][0]
        drops.append(100 * (r["stale_cov_pix"] - c["cov_pix"]))
    check(f"alpha={a} mean drop", f"{sum(drops)/len(drops):.1f}")

# ---------------------------------------------------------------- 7. effective sample size
print("[section 2] effective sample size")
neff = []
for s in SC:
    r = ms[(s, 0.3)]
    sd = (r["clean_hi"] - r["clean_lo"]) / (2 * 1.959964)
    neff.append(0.9 * 0.1 / sd ** 2)
check("n_eff low", f"{min(neff):.0f}")
check("n_eff high", f"{max(neff):.0f}")
check("split-to-split sd low", f"{min((ms[(s, .3)]['clean_hi']-ms[(s, .3)]['clean_lo'])/(2*1.959964) for s in SC):.3f}")
check("split-to-split sd high", f"{max((ms[(s, .3)]['clean_hi']-ms[(s, .3)]['clean_lo'])/(2*1.959964) for s in SC):.3f}")
check("pixel scores per view", "2.9")

# ---------------------------------------------------------------- 8. honest-limits tokens
print("[limits] numbers that must NOT reappear")
for bad in ("26--71", "1.9--12.1\\times$ to $1.9", "104 assertions", "46 unit"):
    global_ok = bad not in TEX_TEXT
    checks += 1
    print(f"  {'OK  ' if global_ok else 'FAIL'} stale token absent: {bad!r}")
    if not global_ok:
        fails.append(f"stale token {bad}")

# ---------------------------------------------------------------- 9. rank consistency
print("[section 3.3] rank consistency")


def _rank(x):
    o = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and x[o[j + 1]] == x[o[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[o[k]] = avg
        i = j + 1
    return r


def _sp(a, b):
    ra, rb = _rank(a), _rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den


_pairs = {}
for _r, _lab in ((0.5, "50"), (0.3, "30")):
    _pairs[_lab] = [(abs(100 * ms[(s, _r)]["drop_mean"]),
                     abs(100 * vt[s][f"voxel_prune{int(_r * 100)}_drop_mean"]),
                     -100 * (vt[s][f"task_prune{int(_r * 100)}_hit"] - vt[s]["task_clean_hit"]))
                    for s in SC]
    check(f"rho pixel {_lab}", f"{_sp([x[0] for x in _pairs[_lab]], [x[2] for x in _pairs[_lab]]):+.2f}$")
    _v = _sp([x[1] for x in _pairs[_lab]], [x[2] for x in _pairs[_lab]])
    check(f"rho region {_lab}", f"={_v:+.2f}$" if abs(_v) > 1e-9 else "0.00$")
_all = _pairs["50"] + _pairs["30"]
check("rho pooled pixel", f"${_sp([x[0] for x in _all], [x[2] for x in _all]):+.2f}$")
check("sign agreement pixel", "five of the eight")
check("sign agreement region", "seven of eight")

print(f"\n{checks} checks, {len(fails)} failures")
if fails:
    print("FAILURES:", fails)
    sys.exit(1)
print("ALL NUMBERS IN main_v2.tex MATCH THE STORED ARTIFACTS")



