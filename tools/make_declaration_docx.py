"""Write the competing-interest declaration as a .docx, in the wording Elsevier's declaration tool produces.

The author has confirmed there is nothing to declare, so the file carries the canonical sentence that the tool emits
for that case, plus the funder-role sentence and a signature block. The tool's own output should replace this file at
submission if Editorial Manager offers it; until then this is the same statement in the same format.

    python tools/make_declaration_docx.py
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Pt

OUT = Path("submission/jvcir/declaration_of_competing_interest.docx")

TITLE = "Declaration of competing interest"
MANUSCRIPT = "CARE-GS: coverage-aware rate reduction for 3D Gaussian Splatting assets"
AUTHOR = ("Tianji Su\nNingbo University, No. 818 Fenghua Road, Jiangbei District, Ningbo 315211, Zhejiang, China\n"
          "71736850@qq.com")
BODY = [
    "The author declares no known competing financial interests or personal relationships that could have appeared to "
    "influence the work reported in this paper. "
    "This statement covers, for the single author, all of the interests the journal asks about: employment, "
    "consultancies, stock ownership, honoraria, paid expert testimony, patent applications or registrations, grants or "
    "other funding, and affiliation with the journal as an editor or advisory board member. None applies.",
    "No funding body had any role in the design of the study; in the collection, analysis or interpretation of data; in "
    "the writing of the manuscript; or in the decision to submit it for publication. This research did not receive any "
    "specific grant from funding agencies in the public, commercial, or not-for-profit sectors.",
]


def main() -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    doc.add_heading(TITLE, level=1)
    p = doc.add_paragraph()
    p.add_run("Manuscript: ").bold = True
    p.add_run(MANUSCRIPT)
    p = doc.add_paragraph()
    p.add_run("Author: ").bold = True
    p.add_run(AUTHOR).add_break()
    doc.add_paragraph("I have nothing to declare.")
    for para in BODY:
        doc.add_paragraph(para)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("Signature: ").bold = True
    p.add_run("______________________")
    p = doc.add_paragraph()
    p.add_run("Date: ").bold = True
    p.add_run("____ / ____ / 2026")
    p = doc.add_paragraph()
    p.add_run("(Signatures are not required by the journal; this block is for the author's own record.)").italic = True

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} B)")


if __name__ == "__main__":
    main()