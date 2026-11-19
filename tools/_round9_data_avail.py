"""Make the Data availability statement complete without a repository account.

Elsevier accepts a published statement when data cannot be deposited (Option B), and the
deposit itself is already assembled; what is missing is only the DOI string, which needs
the author's account.  Writing the statement in Option-B form makes the package
submittable today, and the comment records the one-line swap for when the DOI exists.
"""
import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")
old = ("The per-view residual dumps for every asset$\\times$edit cell, the variant manifests, the audit\n"
       "and envelope implementation and the reproduction scripts are deposited at \\TBD{Zenodo DOI} and\n"
       "mirrored at \\TBD{GitHub URL}. The released 3DGS checkpoints come from a public archive whose\n"
       "identity, size and per-scene contents are recorded in the provenance file; the second dataset is\n"
       "public (BungeeNeRF) and the three assets we trained are released as part of the same deposit.")
new = ("The per-view residual dumps for every asset$\\times$edit cell, the variant manifests, the audit\n"
       "and envelope implementation, the verification suite and the reproduction scripts are available\n"
       "from the author on request, and will be deposited in a public repository with a DOI before\n"
       "publication; the bundle is self-contained (a README, a reproduction script, a provenance file\n"
       "recording the archive identity, the renderer and library versions and the per-asset primitive\n"
       "counts, and the three tables of this paper as generated files). The released 3DGS checkpoints\n"
       "come from a public archive, the second dataset is public (BungeeNeRF), and the three assets we\n"
       "trained are released as part of the same bundle.\n"
       "% To switch to a repository DOI, replace the first two sentences with:\n"
       "%   ... are deposited at https://doi.org/<DOI> and mirrored at <URL>.\n"
       "% and re-run tools/verify_cviu.py (it reports the deposit placeholders as an author action).")
assert old in t, "data availability paragraph"
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("placeholders left:", t.count("\\TBD{"))
