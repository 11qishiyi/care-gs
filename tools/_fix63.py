import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")
subs = [
    (r"Across the $63$ asset$\times$edit cells of section~\ref{sec:results}",
     r"Across the $56$ asset$\times$edit cells of section~\ref{sec:results}"),
    (r"$\mathrm{KS}$ alone already respects the bound in all $63$ cells",
     r"$\mathrm{KS}$ alone already respects the bound in $43$ of the $56$ cells, and in all "
     r"$56$ once the slack is added"),
    (r"over the $63$ cells the rank correlation",
     r"over the $56$ cells the rank correlation"),
    (r"most of the $2.2$-point average", r"most of the $2.0$-point average"),
]
for a, b in subs:
    if a in t:
        t = t.replace(a, b)
        print("ok  ", a[:60])
    else:
        print("MISS", a[:60])
p.write_text(t, encoding="utf-8")
print("lines with $63$:", sum(1 for ln in t.splitlines() if "$63$" in ln))
