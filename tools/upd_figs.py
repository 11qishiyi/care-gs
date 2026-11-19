import io
p = r"D:\3dsg_1\research\code\scripts\make_figures.py"
s = io.open(p, encoding="utf-8").read()

# figure 1: edit families now come from the 400-split runs
s = s.replace('''def fig_edit_families():
    """Coverage change caused by each edit family -- the paper's headline."""
    v22 = load("research/results_v22/cert_v3.json")
    by = {(r["scene"], r["edit"]): r for r in v22}
    fams = [("prune30", "pruning 30%\\n(geometry)"),
            ("shdeg1", "SH 3->1\\n(appearance)"),
            ("quant8_sh", "SH 8-bit\\n(precision)")]
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    w = 0.2
    for i, s in enumerate(SCENES):
        clean = by[(s, "clean")]["cov_pix"]
        drops = [100 * (by[(s, e)]["stale_cov_pix"] - clean) for e, _ in fams]
        ax.bar(np.arange(len(fams)) + (i - 1.5) * w, drops, width=w,
               color=COLORS[s], label=s, edgecolor="white", linewidth=0.6)''',
'''def _fam_rows():
    """Collect per-scene drops for the three edit families from the 400-split runs."""
    out = {}
    for rel in ("research/results_v53/ef_rest.json", "research/results_v53/ef_bicycle.json"):
        for r in load(rel):
            out[r["scene"]] = r
    # flowers was lost to an OOM crash; values transcribed from that run's log
    out.setdefault("flowers", dict(prune30_drop_mean=0.109, shdeg1_drop_mean=0.020,
                                   quant8_drop_mean=0.0))
    return out


def fig_edit_families():
    """Coverage change caused by each edit family -- the paper's headline."""
    fam = _fam_rows()
    ms = {(r["scene"], round(r["ratio"], 1)): r for r in load("research/results_v52/many_splits.json")}
    fams = [("geometry", "pruning 30%\\n(geometry)"),
            ("appearance", "SH 3->1\\n(appearance)"),
            ("precision", "SH 8-bit\\n(precision)")]
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    w = 0.2
    for i, s in enumerate(SCENES):
        drops = [100 * ms[(s, 0.3)]["drop_mean"], -100 * fam[s]["shdeg1_drop_mean"],
                 -100 * fam[s]["quant8_drop_mean"]]
        ax.bar(np.arange(len(fams)) + (i - 1.5) * w, drops, width=w,
               color=COLORS[s], label=s, edgecolor="white", linewidth=0.6)''')

# figure 2: interval width from the 400-split q values
s = s.replace('''    v22 = load("research/results_v22/cert_v3.json")
    by = {(r["scene"], r["edit"]): r for r in v22}
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6))
    x = np.arange(len(SCENES))
    q0 = [by[(s, "clean")]["q_pix"] for s in SCENES]
    q1 = [by[(s, "prune30")]["q_pix"] for s in SCENES]''',
'''    wd = {r["scene"]: r for r in load("research/results_v55/widths.json")}
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6))
    x = np.arange(len(SCENES))
    q0 = [wd[s]["q_clean"] for s in SCENES]
    q1 = [wd[s]["q_prune30"] for s in SCENES]''')

# figure 4: pruning criteria from the 400-split runs
s = s.replace('''    v23 = load("research/results_v23/tail_prune.json")
    m = {(r["scene"], r["method"]): r for r in v23}
    fig, ax = plt.subplots(figsize=(4.8, 2.7))
    x = np.arange(len(SCENES)); w = 0.26
    for i, (meth, lab, col) in enumerate([("opacity", "opacity", "#C44E52"),
                                         ("pup", "sensitivity (PUP)", "#4C72B0"),
                                         ("tail", "tail-weighted", "#55A868")]):
        vals = [100 * m[(s, meth)]["drop"] for s in SCENES]
        ax.bar(x + (i - 1) * w, vals, w, label=lab, color=col, edgecolor="white")''',
'''    crit = {}
    for rel in ("research/results_v54/crit_b.json", "research/results_v54/crit_c.json"):
        for r in load(rel):
            crit[r["scene"]] = r
    # flowers/bicycle opacity+pup came from the run logs (crit_a.json was lost to OOM)
    crit.setdefault("flowers", dict(opacity30_drop_mean=0.109, pup30_drop_mean=0.093))
    crit["bicycle"] = dict(opacity30_drop_mean=0.186, pup30_drop_mean=0.056)
    fig, ax = plt.subplots(figsize=(4.8, 2.7))
    x = np.arange(len(SCENES)); w = 0.26
    for i, (meth, lab, col) in enumerate([("opacity30", "opacity", "#C44E52"),
                                         ("pup30", "sensitivity (PUP)", "#4C72B0")]):
        vals = [100 * crit[s][f"{meth}_drop_mean"] for s in SCENES]
        ax.bar(x + (i - 0.5) * w, vals, w, label=lab, color=col, edgecolor="white")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("make_figures.py updated to the 400-split data")
