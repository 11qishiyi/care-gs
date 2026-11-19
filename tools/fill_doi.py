"""Fill the two author-supplied slots in the manuscript and re-verify.

The Data-availability section carries two macros, `\\TBD{Zenodo DOI}` and `\\TBD{GitHub URL}`, because the archive
DOI cannot be minted until the repository is released. This script substitutes them, recompiles, and runs the
submission gate, so the last step of a submission is one command instead of five.

    python tools/fill_doi.py --doi 10.5281/zenodo.1234567
    python tools/fill_doi.py --doi 10.5281/zenodo.1234567 --url https://github.com/11qishiyi/care-gs --no-build

Refuses to run if the DOI does not look like a DOI, or if the slots are already filled (so it cannot be run twice
by accident and silently produce "DOI DOI").
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(".").resolve()
TEX = ROOT / "submission" / "jvcir" / "main.tex"
DOI_RX = re.compile(r"^10\.\d{4,9}/\S+$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", required=True)
    ap.add_argument("--url", default="https://github.com/11qishiyi/care-gs")
    ap.add_argument("--no-build", action="store_true", help="edit only; do not recompile or run the gate")
    a = ap.parse_args()

    if not DOI_RX.match(a.doi):
        print(f"not a DOI: {a.doi!r}")
        return 2

    tex = TEX.read_text(encoding="utf-8")
    have_doi = "\\TBD{Zenodo DOI}" in tex
    have_url = "\\TBD{GitHub URL}" in tex
    if not have_doi and not have_url:
        print("both slots are already filled; nothing to do")
        return 0
    if have_doi:
        tex = tex.replace("\\TBD{Zenodo DOI}", a.doi)
    if have_url:
        tex = tex.replace("\\TBD{GitHub URL}", a.url)
    TEX.write_text(tex, encoding="utf-8")
    print(f"filled: doi={'yes' if have_doi else 'already'} url={'yes' if have_url else 'already'}")

    if a.no_build:
        return 0

    sub = ROOT / "submission" / "jvcir"
    for cmd in (["pdflatex", "-interaction=nonstopmode", "main.tex"],
                ["bibtex", "main"],
                ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
        r = subprocess.run(cmd, cwd=sub, capture_output=True, text=True)
        if cmd[0] == "bibtex" and r.returncode not in (0, 1):      # bibtex warns a lot; only hard failures matter
            print(r.stdout[-400:])
    gate = subprocess.run([sys.executable, "tools/verify_jvcir.py"], cwd=ROOT, capture_output=True, text=True)
    print((gate.stdout.strip().splitlines() or [""])[-1])
    return gate.returncode


if __name__ == "__main__":
    sys.exit(main())
