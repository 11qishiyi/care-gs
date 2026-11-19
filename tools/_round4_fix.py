import pathlib

# 1. cover letter: the assertion count must match the manuscript (29, not 494)
C = pathlib.Path("submission/cviu/COVER_LETTER.md")
c = C.read_text(encoding="utf-8")
old = ("and 494 automated assertions that re-derive every number in the manuscript from the stored\n"
       "artifacts and fail the build on any mismatch.")
new = ("and 29 automated assertions that re-derive the numbers in the manuscript from the stored\n"
       "artifacts and fail the build on any mismatch (the earlier version of this study carried a\n"
       "larger suite for a longer manuscript; the count here is the one that runs on this file).")
assert old in c, "cover-letter assertion sentence"
c = c.replace(old, new)
C.write_text(c, encoding="utf-8")

# 2. Table 4 provenance: the criterion table is from the earlier grid
M = pathlib.Path("submission/cviu/main.tex")
t = M.read_text(encoding="utf-8")
old_cap = ("Coverage drops and paired quantile growth as before, ground truth as captured.}")
new_cap = ("Coverage drops and paired quantile growth as before, ground truth as captured.\n"
           "This table was measured in the earlier campaign; the \\texttt{pup30} row of\n"
           "Table~\\ref{tab:dose} comes from the later grid and differs from the Fisher column here by\n"
           "up to $2.4$ points, which is a difference between two grids and not a correction.}")
assert old_cap in t, "table4 caption"
t = t.replace(old_cap, new_cap)
M.write_text(t, encoding="utf-8")
print("patched cover letter and table-4 caption")
