import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")

anchor = "\\paragraph{The envelope holds, and its slack is measurable.}"
assert anchor in t
add = (
    "\\paragraph{What the audit is worth in a decision.} The two checks have different prices and\n"
    "different outputs, and so far we have reported them separately. Re-issuing needs labelled views\n"
    "--- two restore the nominal level --- but it widens the tolerance by $53$--$122\\%$, a permanent\n"
    "cost on every future coverage claim the asset carries. Auditing needs no labels and costs\n"
    "renders: $5.1$ points of error from one view, $3.6$ from two, $2.7$ from four. The choice is\n"
    "therefore not a preference but a condition. A recipient that holds two labelled views and does\n"
    "not need a tight tolerance should re-issue. A recipient that holds no labels --- the case a\n"
    "certificate exists for --- should audit, and four renders is the right place to stop. The\n"
    "comparison that decides it is the one we can now make: the audit's error at four views ($2.7$\n"
    "points) is smaller than the median slack of the envelope it is checking ($4.4$ points), so\n"
    "spending renders on the audit buys a sharper answer than the bound it is meant to test. That is\n"
    "the concrete reason we call the audit the primary check and the envelope the secondary one, and\n"
    "it is a comparison no previous certificate in this area could make, because there was nothing to\n"
    "audit with.\n\n")
t = t.replace(anchor, add + anchor)
p.write_text(t, encoding="utf-8")
print("inserted decision paragraph")
