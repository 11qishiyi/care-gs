"""Restructure the TMLR manuscript into the CVIU reading order.

Moves (no prose is rewritten here, only relocated):

  * ``\\section{Related work}``  -> immediately after the introduction
  * ``\\subsection{A tempting label-free check cannot work}`` -> dropped here; its
    content is folded into the new audit section (written by hand afterwards)
  * the bibliography is replaced by ``\\bibliography{refs}``

Run once; it writes ``main.tex`` and keeps ``main_pre_restructure.tex``.
"""
import re
import shutil
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "submission" / "cviu" / "main.tex"
src = P.read_text(encoding="utf-8")
shutil.copy2(P, P.with_name("main_pre_restructure.tex"))


def cut(text, start_marker, end_marker):
    """Remove [start, end) and return (new_text, removed_block)."""
    i = text.index(start_marker)
    j = text.index(end_marker)
    return text[:i] + text[j:], text[i:j]


# 1) lift Related work out and re-insert before \section{Setup}
src, related = cut(src, "\\section{Related work}", "\\section{Discussion and limitations}")
assert related.startswith("\\section{Related work}")
k = src.index("\\section{Setup}")
src = src[:k] + related + src[k:]

# 2) drop the old "circular check" subsection (content moves into the audit section)
#    NOTE: after step 1 the *next* top-level section is Discussion, not Related work.
src, circular = cut(src, "\\subsection{A tempting label-free check cannot work}",
                    "\\section{Discussion and limitations}")
Path(P.with_name("_lifted_circular.tex")).write_text(circular, encoding="utf-8")

# 3) bibliography: thebibliography block -> \bibliography{refs}
src = re.sub(r"\\begin\{thebibliography\}\{99\}.*?\\end\{thebibliography\}\s*",
             "\\bibliographystyle{elsarticle-harv}\n\\bibliography{refs}\n\n",
             src, flags=re.S)

P.write_text(src, encoding="utf-8")
print("ok: related work moved, circular subsection lifted, bibliography switched")
print("lines:", src.count("\n"))
