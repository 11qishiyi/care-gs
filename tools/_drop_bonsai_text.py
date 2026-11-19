import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")
subs = [
    # abstract: the audit grid is eight checkpoints, not nine
    ("On nine scene-checkpoints (four released assets, four\nshort-training twins, one further asset) with 400 splits each and four pruning\nstrengths",
     "On eight scene-checkpoints (four released assets and four\nshort-training twins of the same scenes) with 400 splits each and four pruning\nstrengths"),
    # abstract + contributions: the audit's MAE
    ("recover post-edit coverage to within\n$2.2$ points for one render pass",
     "recover post-edit coverage to within\n$2.0$ points for one render pass"),
    ("$2.2$ points (section~\\ref{sec:auditres})", "$2.0$ points (section~\\ref{sec:auditres})"),
    # setup: which assets are measured where
    ("and bonsai --- nine scene-checkpoints in total. Amsterdam and\nthe three self-trained assets are therefore absent from Table~\\ref{tab:audit};",
     "--- eight scene-checkpoints in total. Bonsai, amsterdam and the three self-trained assets\nare therefore absent from Table~\\ref{tab:audit}; bonsai for a reason we state below, the other\nfour because the earlier campaign measured them and this one did not;"),
    # 5.8 cell count and headline errors
    ("Across the $63$ cells --- nine scene-checkpoints times seven\nedits --- the mean absolute error is $2.2$ points, the worst cell is $5.0$ points, and the mean\nsigned error is $-0.3$ points",
     "Across the $56$ cells --- eight scene-checkpoints times seven\nedits --- the mean absolute error is $2.0$ points, the worst cell is $3.4$ points, and the mean\nsigned error is $0.2$ points"),
    ("the audit's mean signed error is $+0.1$ points and its mean\nabsolute error $2.0$ points",
     "the audit's mean signed error is $0.0$ points and its mean\nabsolute error $1.8$ points"),
    ("most of the $2.2$-point average is this floor", "most of the $2.0$-point average is this floor"),
    # k-view curve
    ("$5.9$ points from one view,\n$4.0$ from two, $3.0$ from four and $2.5$ from eight, against $2.2$ for the whole shipped set",
     "$5.1$ points from one view,\n$3.6$ from two, $2.7$ from four and $2.2$ from eight, against $2.0$ for the whole shipped set"),
    # envelope paragraph
    ("holds in\n$63/63$ cells. $\\mathrm{KS}$ alone, without the slack, holds in $49/63$; the ratio of measured\nloss to $\\mathrm{KS}$ has median $0.60$ over the $27$ pruning cells (range $0.09$--$1.02$), and it\nexceeds one in the two \\texttt{pup30} cells on stump, where the slack is doing the work.",
     "holds in\n$56/56$ cells. $\\mathrm{KS}$ alone, without the slack, holds in $43/56$; the ratio of measured\nloss to $\\mathrm{KS}$ has median $0.64$ over the $24$ pruning cells (range $0.33$--$1.02$), and it\nexceeds one in the two \\texttt{pup30} cells on stump, where the slack is doing the work."),
    ("over-states the damage by about $1.7\\times$ at the median and by up to $11\\times$\nin the least favourable cell, while eight cells have a non-positive loss",
     "over-states the damage by about $1.6\\times$ at the median and by up to $3\\times$\nin the least favourable cell, while six cells have a non-positive loss"),
]
for old, new in subs:
    if old not in t:
        print("MISS:", old[:70].replace("\n", " "))
        continue
    t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("remaining '63' mentions:", t.count("$63$"))
