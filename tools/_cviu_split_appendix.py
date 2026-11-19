"""Split the appendix out of the CVIU manuscript into a separate supplementary file.

Main text keeps a pointer section; ``xr`` pulls the appendix labels back in so every
``\\ref{app:...}`` still resolves.  Run from the repo root.
"""
from pathlib import Path

D = Path("submission/cviu")
main = (D / "main.tex").read_text(encoding="utf-8")

i = main.index("\\appendix")
head, app = main[:i], main[i:]

sup_head = r"""%% Supplementary material for the CVIU submission.
%% Compile with:  pdflatex supplementary && pdflatex supplementary
\documentclass[preprint,authoryear]{elsarticle}

\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{multirow}
\usepackage{xcolor}
\usepackage{url}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}

\newcommand{\TBD}[1]{{\color{red}[TBD: \detokenize{#1}]}}
\journal{Computer Vision and Image Understanding}

\begin{document}

\begin{frontmatter}
\title{Supplementary material for\\ \emph{Valid but Unusable, and Auditable}}
\author[nbu]{Tianji Su}
\address[nbu]{Ningbo University, Ningbo, China}
\end{frontmatter}

\noindent This supplement carries the measurements that support, but are not needed to
follow, the main text: region granularity (A), the repair curve (B), the scope of the effect
(C), two methodological traps (D), a learned matcher (E), bit depth and optimisation depth (F),
and the tooling that reproduces every number (G). Section numbers here are cited from the main
text as ``Appendix~X''.

"""

(D / "supplementary.tex").write_text(sup_head + app, encoding="utf-8")

pointer = r"""\section*{Supplementary material}

Seven appendices accompany this paper and are submitted as a separate file: region granularity
(pixel, $64\times64$ block and world-space voxel certificates), the repair curve as a function of
the number of held-out views, the scope condition that the effect needs a fully optimised asset,
the two methodological traps (split design and view disjointness), the learned-matcher control,
bit depth and optimisation depth with two further assets, and the tooling with a one-click
reproduction script. Every appendix number is re-derived by the same assertion suite as the main
text.

"""
head = head.rstrip() + "\n\n" + pointer
head = head.replace("\\usepackage{url}",
                    "\\usepackage{url}\n\\usepackage{xr}\n\\externaldocument{supplementary}")
(D / "main.tex").write_text(head, encoding="utf-8")

print("main lines:", head.count("\n"), " supplementary lines:",
      (sup_head + app).count("\n"))
