import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")
subs = [
    (r"\TBD{MAE} points for one render pass", r"$2.2$ points for one render pass"),
    (r"\TBD{mae} points (section~\ref{sec:auditres})",
     r"$2.2$ points (section~\ref{sec:auditres})"),
    (r"Across the \TBD{N} asset$\times$edit cells of section~\ref{sec:results}",
     r"Across the $63$ asset$\times$edit cells of section~\ref{sec:results}"),
    (r"the ratio of measured loss to $\mathrm{KS}$ is \TBD{tightness}, and the certified part",
     r"the ratio of measured loss to $\mathrm{KS}$ has median $0.60$ (range "
     r"$0.09$--$1.02$), and the certified part"),
    (r"respects the bound in \TBD{frac}\% of cells", r"respects the bound in all $63$ cells"),
    (r"automated check of \TBD{NA} assertions", r"automated check of 34 assertions"),
]
for old, new in subs:
    assert old in t, old[:60]
    t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
left = sorted({x for x in __import__("re").findall(r"\\TBD\{([^}]*)\}", t)})
print("remaining TBDs:", left)
