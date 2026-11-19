"""Write the competing-interest declaration as a .docx, so the upload step has the file ready.

Elsevier requires the declaration to come from its own declarations tool; the text below is the same text that
appears in the manuscript's "Declaration of competing interest" section, and the file is formatted so it can be
uploaded directly if the tool's output is unavailable. Nothing else is claimed here.

    python tools/make_declaration_docx.py
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Pt

OUT = Path("submission/jvcir/declaration_of_competing_interest.docx")

TITLE = "Declaration of competing interest"
AUTHOR = "Tianji Su, Ningbo University, Ningbo, China"
MANUSCRIPT = "CARE-GS: coverage-aware rate reduction for 3D Gaussian Splatting assets"
BODY = [
    'The author declares that he has no known competing financial interests or personal relationships that '
    'could have appeared to influence the work reported in this paper.',
    'No funding body had any role in the design of the study; in the collection, analysis or interpretation of '
    'data; in the writing of the manuscript; or in the decision to submit it for publication.',
    'This research did not receive any specific grant from funding agencies in the public, commercial, or '
    'not-for-profit sectors.',
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
    p.add_run(AUTHOR)

    for para in BODY:
        doc.add_paragraph(para)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("Signature: ").bold = True
    p.add_run("______________________")
    p = doc.add_paragraph()
    p.add_run("Date: ").bold = True
    p.add_run("____ / ____ / 2026")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} B)")


if __name__ == "__main__":
    main()
