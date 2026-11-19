import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")

# 1. the rho sentence
old_rho = ("over the $56$ cells the rank correlation between decibels lost and points of\n"
           "coverage lost is $+0.91$")
assert old_rho in t, "rho sentence"
t = t.replace(old_rho,
              "over the $56$ cells the rank correlation between decibels lost and points of\n"
              "coverage lost is $+0.90$")

# 2. the limits paragraph still says nine scene-checkpoints / six scenes
old_gap = ("First, the audit is measured on\nnine scene-checkpoints, and two of them are the same four "
           "scenes at two optimisation depths, so it\ncovers six distinct scenes rather than the nine assets "
           "of section~\\ref{sec:setup}; amsterdam and\nthe three assets we trained appear in the degradation "
           "tables but not in\nTable~\\ref{tab:audit}.")
assert old_gap in t, "gap sentence"
new_gap = ("First, the audit is measured on\neight scene-checkpoints, and four of them are the same scenes at "
           "two optimisation depths, so it\ncovers four distinct scenes and their short-training twins rather "
           "than the nine assets of\nsection~\\ref{sec:setup}; amsterdam and the three assets we trained appear "
           "in the degradation\ntables but not in Table~\\ref{tab:audit}.")
t = t.replace(old_gap, new_gap)

# 3. the bonsai paragraph, appended to the same bullet list
anchor = "--- invalidates the audit's own premise, and nothing in this paper covers it."
assert anchor in t, "anchor"
add = anchor + (
    "\n\nThe third exclusion is an instrument failure rather than a gap, and we report it instead of\n"
    "hiding it. Bonsai appears in the degradation tables of the earlier campaign (1.24M primitives, 37\n"
    "held-out views, a $10.3$-point loss at 30\\% pruning). For this campaign we re-stitched it from a\n"
    "public mirror, and the re-stitched asset renders at $15.8$\\,dB against its own ground truth --- a\n"
    "camera/ground-truth pairing failure, not a property of the asset. Under that failure the residuals\n"
    "are dominated by a global misalignment, pruning barely moves the threshold count, and the audit\n"
    "reports a $0.9$-point loss: a plausible number produced by a broken measurement. We excluded the\n"
    "checkpoint rather than report the number, which is why the audit grid has eight\n"
    "scene-checkpoints and not nine. The deposit's build script regenerates the entry; rebuilt that\n"
    "way it should match the appendix's $10.3$ rather than our $0.9$, and if it does not, our earlier\n"
    "number is the one to distrust.")
t = t.replace(anchor, add)
p.write_text(t, encoding="utf-8")
print("patched")
