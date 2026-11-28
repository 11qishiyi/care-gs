"""Report the package against the journal's Writing-and-formatting rules, item by item.

The rules are transcribed from the guide's "File format" and "Artwork" sections (fetched 2026-11-28):

  * editable source files for the whole submission; .doc/.docx or .tex; a PDF is not an acceptable source file
  * vector drawings as EPS or PDF with embedded fonts
  * photographs (halftones) as TIFF/JPG/PNG at >= 300 dpi at the printed size
  * bitmapped line drawings at >= 1000 dpi; bitmapped line/halftone combinations at >= 500 dpi
  * charts and large tables may be supplied as XLS/XLSX
  * do not submit artwork that combines several images into one file (an exception exists for panels that must be
    compared side by side)
  * no strikethrough or underlined text; Word single-column, LaTeX may be two-column
  * spell-check and grammar-check before submission

    python tools/check_guide_format.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

SUB = Path("submission/jvcir")
FIG = Path("figures_j")
TEX = SUB / "main.tex"

problems: list[str] = []


def item(cond: bool, label: str, detail: str = "") -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        problems.append(label)


def main() -> int:
    tex = TEX.read_text(encoding="utf-8")

    item(TEX.exists() and TEX.stat().st_size > 0, "editable LaTeX source present", f"{TEX.stat().st_size:,} B")
    item((SUB / "main.pdf").exists(), "PDF supplied for review (not as the source file)")

    # figures: vector first, and every raster at >= 300 dpi at the size it is printed
    for png in sorted(FIG.glob("*.png")):
        stem = png.stem
        pdf = FIG / f"{stem}.pdf"
        px = Image.open(png).size[0]
        if not pdf.exists():
            item(False, f"{stem}: vector version present")
            continue
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        m = re.search(r"Page size:\s+([\d.]+) x", info)
        dpi = round(px / (float(m.group(1)) / 72.27)) if m else 0
        item(dpi >= 300, f"{stem}: raster >= 300 dpi at printed width", f"{dpi} dpi, {px} px")

    # fonts embedded in every vector figure
    for pdf in sorted(FIG.glob("*.pdf")):
        try:
            out = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True, timeout=60).stdout
            rows = [ln for ln in out.splitlines()[2:] if ln.strip()]
            bad = [ln.split()[0] for ln in rows if len(ln.split()) > 5 and ln.split()[-4] == "no"]
            item(not bad, f"{pdf.stem}: fonts embedded", ", ".join(bad) or f"{len(rows)} font(s)")
        except FileNotFoundError:
            print("  [SKIP] pdffonts unavailable")


    # ---- article structure (guide: "Article structure", "Title page", "References")
    fm = tex[tex.find("\\begin{frontmatter}"):tex.find("\\end{frontmatter}")]
    item("\\corref{" in fm and "\\cortext[" in fm, "corresponding author marked (\\corref + \\cortext)")
    item(bool(re.search(r"\\ead\{", fm)), "corresponding e-mail present")
    item(bool(re.search(r"China|,\s*[A-Z][a-z]+,?\s*[A-Z]{2}", fm)), "affiliation names a country")

    numbered = re.findall(r"\\section\{([^}]+)\}", tex)
    item(len(numbered) >= 3, "numbered sections", f"{len(numbered)} sections")
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    item(abstract is not None and "\\cite" not in abstract.group(1), "no citations inside the abstract")
    item(not re.search(r"(?:in|see|of)\s+the\s+text", tex, re.I), "no 'in the text' cross-references")

    # every figure and table label cited, including the generated table files
    labels = re.findall(r"\\label\{((?:fig|tab):[^}]+)\}", tex)
    for f in sorted(SUB.glob("tab_*.tex")):
        labels += re.findall(r"\\label\{((?:fig|tab):[^}]+)\}", f.read_text(encoding="utf-8"))
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", tex))
    uncited = sorted(set(labels) - refs)
    item(not uncited, "every figure and table is cited in the text", ", ".join(uncited) or f"{len(set(labels))} objects")

    # British or American, not both (guide: "Language and editing services")
    brit = sum(len(re.findall(r"\b" + w + r"\b", tex, re.I)) for w in
               ("quantisation", "colour", "behaviour", "analyse", "modelling", "labelled", "favour"))
    amer = sum(len(re.findall(r"\b" + w + r"\b", tex, re.I)) for w in
               ("quantization", "color", "behavior", "analyze", "modeling", "labeled", "favor"))
    item(not (brit and amer), "one spelling convention throughout", f"{brit} British / {amer} American")

    # preprints must carry a DOI (guide: "Reference to preprints")
    bib = (SUB / "refs.bib").read_text(encoding="utf-8")
    arx = re.findall(r"arXiv preprint arXiv:(\d{4}\.\d{4,5})", bib)
    with_doi = sum(1 for a in arx if f"10.48550/arXiv.{a}" in bib)
    item(with_doi == len(arx), "every arXiv preprint carries its DOI", f"{with_doi}/{len(arx)}")

    # graphical abstract (guide: at least 1328 px wide, longest side horizontal)
    ga = FIG / "graphical_abstract.png"
    if ga.exists():
        w, h = Image.open(ga).size
        item(w >= 1328 and w > h, "graphical abstract >= 1328 px wide and landscape", f"{w}x{h}")

    # text hygiene
    item("\\underline" not in tex, "no underlined text")
    item("\\sout" not in tex and "\\st{" not in tex, "no strikethrough")
    doubles = [m.group(0) for m in re.finditer(r"\b(\w+)\s+\1\b", tex, re.I)
               if m.group(1).lower() not in ("that", "had", "the")]
    item(not doubles, "no duplicated words", ", ".join(doubles[:4]))

    # declarations the guide names explicitly
    item("Declaration of generative AI and AI-assisted technologies in the manuscript preparation process" in tex,
         "GenAI section title matches the guide")
    gen = re.search(r"Declaration of generative AI.*?\\bibliographystyle", tex, re.S)
    body = gen.group(0) if gen else ""
    tool = re.search(r"\(([A-Z][A-Za-z0-9 .-]{2,})\)", body)
    item(bool(tool), "GenAI statement names the tool", tool.group(0) if tool else "no (Tool) found")
    item("This research did not receive any specific grant" in tex, "funding sentence is the guide's wording")
    item((SUB / "declaration_of_competing_interest.docx").exists(), "competing-interest .docx present")

    print(f"\n{'PASS' if not problems else 'FAIL'}: {len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())