"""Keep OPENREVIEW_SUBMISSION.md's pasted fields in sync with submission/main_v3.tex.

Extracts the abstract from the LaTeX source, flattens the markup to plain text, and replaces the
fenced block under "## Abstract".  Run after every abstract edit:

    python tools/sync_openreview.py
"""
import io
import re

TEX = "submission/main_v3.tex"
MD = "submission/final/OPENREVIEW_SUBMISSION.md"


def plain(s: str) -> str:
    s = s.replace("\\emph{", "").replace("\\textbf{", "")
    s = re.sub(r"\\citet\{[^}]*\}", "", s)
    s = s.replace("\\alpha", "alpha").replace("\\%", "%").replace("\\times", "×")
    s = s.replace("~", " ").replace("$", "")
    s = s.replace("---", "—").replace("--", "-").replace("\\ ", " ")
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s).strip()
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 98:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return "\n".join(lines)


tex = io.open(TEX, encoding="utf-8").read()
m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
abstract = plain(" ".join(m.group(1).split()))

doc = io.open(MD, encoding="utf-8").read()
start = doc.index("## Abstract")
fence1 = doc.index("```", start)
fence2 = doc.index("```", fence1 + 3)
new = doc[:fence1 + 3] + "\n" + abstract + "\n" + doc[fence2:]
io.open(MD, "w", encoding="utf-8").write(new)
print(f"abstract synced ({len(abstract)} chars)")
print(abstract)
