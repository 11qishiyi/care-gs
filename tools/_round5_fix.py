import pathlib

M = pathlib.Path("submission/cviu/main.tex")
t = M.read_text(encoding="utf-8")
n = 0

# (1) the envelope is empirical: cite DKW / Massart and say so
anchor = "\\paragraph{How tight is the envelope?}"
assert anchor in t, "envelope paragraph anchor"
add = (
    "\\paragraph{The envelope is empirical, not a finite-sample guarantee.} "
    "$\\mathrm{KS}(F,F')$ is a supremum of two \\emph{empirical} CDFs, so it carries its own sampling\n"
    "error. A Dvoretzky--Kiefer--Wolfowitz band at the effective sample size this protocol actually\n"
    "has ($77$--$508$ independent scores, section~\\ref{sec:setup}) and $\\delta=0.05$ is about\n"
    "$\\pm0.14$ \\citep{dwk1956,massart1990} --- the same order as the $\\mathrm{KS}$ values themselves\n"
    "($0.03$--$0.33$). Two consequences we accept rather than hide. The envelope bounds the loss of\n"
    "\\emph{this} calibration set, not of a re-drawn one; and what we call certified is the\n"
    "\\emph{form} of the bound, not a finite-sample level. That is why the audit of\n"
    "section~\\ref{sec:audit} is the primary check and the envelope is the secondary one: the audit's\n"
    "error is measured ($2.0$ points) and the envelope's slack is measured ($\\varepsilon$, median\n"
    "$4.4$ points), while neither is a theorem about unseen views.\n\n")
t = t.replace(anchor, add + anchor)
n += 1

# (2) task table: say which grid it came from
old = ("so its two entries move by one pair and should not be read as an\neffect.}")
new = ("so its two entries move by one pair and should not be read as an\neffect. The coverage column is\n"
       "the same measurement as Table~\\ref{tab:main}; the three task columns were measured in the\n"
       "earlier campaign on the same protocol, and the shipped 108-cell sweep of the deposit places\n"
       "treehill's local task at $21.3$ rather than $34.4$ points --- the ordering of the four\n"
       "yardsticks is unchanged, the absolute magnitude of the weakest asset is not.}")
if old in t:
    t = t.replace(old, new)
    n += 1
else:
    print("TASK CAPTION MISS")

M.write_text(t, encoding="utf-8")
print("patched", n, "sites; cites present:",
      t.count("dwk1956"), t.count("massart1990"))
