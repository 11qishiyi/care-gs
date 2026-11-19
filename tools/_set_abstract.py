import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")
I = r"\begin{abstract}"
J = r"\end{abstract}"
i = t.index(I) + len(I)
j = t.index(J)
new = r"""
A 3D Gaussian Splatting (3DGS) asset can ship with a distribution-free \emph{coverage
certificate}: with probability $1-\alpha$ a pixel of a held-out view has rendering error below a
threshold $q$. It describes one model, yet recipients re-prune, re-quantise and re-fit it. A
certificate is usually read as valid, or as silently wrong. We argue and measure a third status: it
is \emph{auditable}. On nine assets with 400 calibration/deployment splits each and four pruning
strengths, geometric edits cost $10.8$--$27.7$ points of per-pixel coverage and grow the quantile
$53$--$122\%$, while harmonic truncation and 8-bit quantisation cost at most $3.3$ points and
nothing; the criterion that chooses what to delete matters as much as the budget. We supply two
missing objects. An \emph{audit} needs no new labels: re-render the edited asset on the shipped
calibration views, count residuals below the shipped $q$, and recover post-edit coverage to within
\TBD{MAE} points for one render pass. A \emph{Kolmogorov envelope} bounds the loss from above ---
coverage loss $\le\mathrm{KS}(F,F')$ between pre- and post-edit residual distributions --- and an
issuer can evaluate it \emph{before} shipping by simulating the edit family, so the certificate
declares how much damage it tolerates. Re-issuing is cheap in data (two views restore the level)
and expensive in information (width $+53$--$122\%$). Auditing fixes neither the ground-truth
convention, worth up to $2.4\times$ in magnitude, nor the fact that the certified quantity tracks
none of four downstream task families, which disagree by four to eleven times.
"""
p.write_text(t[:i] + new + t[j:], encoding="utf-8")
print("abstract replaced")
