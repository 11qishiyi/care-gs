"""Drop the SSIM column: it was promised but never computed.

The dump stage skipped SSIM (the skimage path raised and the warning was swallowed),
so every SSIM cell in tab_fidelity.tex is ``--``.  A table of dashes is worse than a
table without the column, and the fidelity argument only needs PSNR: the claim is that
the *scale* of a decibel loss does not transfer to points of coverage.
"""
import pathlib

G = pathlib.Path("tools/cviu_audit_tables.py")
g = G.read_text(encoding="utf-8")

pairs = [
    ('''            ss = f"{st['ssim']:.3f}" if st.get("ssim") is not None else "--"
''', ''''''),
    ('''                         f"{st['psnr']:.2f} & {dpsnr} & {ss} & {dpp} \\\\\\\\")''',
     '''                         f"{st['psnr']:.2f} & {dpsnr} & {dpp} \\\\\\\\")'''),
    ("\\caption{Fidelity against the certificate on the very same renders. PSNR (dB) and SSIM are mean\n"
     "over the held-out views of each asset; $\\Delta$PSNR is against the fresh asset, so a negative value\n"
     "is a fidelity loss; ``cov.\\ drop'' is the per-pixel paired coverage drop of\n"
     "Table~\\ref{tab:main}, in points.}",
     "\\caption{Fidelity against the certificate on the very same renders. PSNR (dB) is the mean over\n"
     "the held-out views of each asset; $\\Delta$PSNR is against the fresh asset, so a negative value is a\n"
     "fidelity loss; ``cov.\\ drop'' is the per-pixel paired coverage drop of Table~\\ref{tab:main}, in\n"
     "points.}"),
    ("\\begin{tabular}{llrrrr}", "\\begin{tabular}{llrrr}"),
    ("Asset & edit & PSNR & $\\Delta$PSNR & SSIM & cov.\\ drop \\\\",
     "Asset & edit & PSNR & $\\Delta$PSNR & cov.\\ drop \\\\"),
]
for a, b in pairs:
    if a not in g:
        print("GEN MISS:", a[:60].replace("\n", " "))
        continue
    g = g.replace(a, b)
G.write_text(g, encoding="utf-8")

M = pathlib.Path("submission/cviu/main.tex")
t = M.read_text(encoding="utf-8")
mt = [
    ("path, and the fidelity of each variant is reported with PSNR and SSIM",
     "path, and the fidelity of each variant is reported with PSNR"),
    ("Table~\\ref{tab:fidelity} answers with the same renders: PSNR and SSIM for the fresh asset\n"
     "and after each edit",
     "Table~\\ref{tab:fidelity} answers with the same renders: PSNR for the fresh asset and\nafter each edit"),
    ("\\caption{Fidelity against the certificate on the same renders. PSNR (dB) and SSIM are over the\n"
     "held-out views of each asset; coverage change is the per-pixel paired drop of\n"
     "Table~\\ref{tab:main}. $\\Delta$PSNR is in decibels against the fresh asset, so a negative value is\n"
     "a fidelity loss.}",
     "\\caption{Fidelity against the certificate on the same renders. PSNR (dB) is over the held-out\n"
     "views of each asset; coverage change is the per-pixel paired drop of Table~\\ref{tab:main}.\n"
     "$\\Delta$PSNR is in decibels against the fresh asset, so a negative value is a fidelity loss.}"),
]
for a, b in mt:
    if a not in t:
        print("TEX MISS:", a[:60].replace("\n", " "))
        continue
    t = t.replace(a, b)
M.write_text(t, encoding="utf-8")
print("SSIM mentions left in tex:", t.count("SSIM"))
print("SSIM in generator:", g.count("ssim"))
