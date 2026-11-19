"""Consistency checks for the CVIU submission.  Exits non-zero on any failure.

This is the successor of ``tools/verify_tex_v3.py`` for a manuscript whose tables are
*generated* rather than typed: the generator (``tools/cviu_audit_tables.py``) is the
single source for the new numbers, and this script checks that

  * the manuscript has no unfilled placeholder, and its abstract / highlights /
    keywords are inside Elsevier's stated limits;
  * every citation key exists in ``refs.bib`` and every generated table is present
    and non-empty;
  * the generated tables agree with the JSON artifacts, cell by cell;
  * the headline numbers of the earlier campaign are still the ones in the text;
  * the PDF builds and its page count is in the range the genre uses.

Usage
-----
    python tools/verify_cviu.py                 # after building the PDF
    python tools/verify_cviu.py --no-pdf        # manuscript checks only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

D = "submission/cviu"
AUDIT_JSON = "results_v120/audit_bound_nobonsai.json"
DUMP_SUMMARY = "results_v120/dump/dump_summary.json"

CHECKS = []
FAILED = []


def check(name, cond, detail=""):
    CHECKS.append(name)
    if not cond:
        FAILED.append(f"{name}: {detail}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args(argv)

    tex = open(os.path.join(D, "main.tex"), encoding="utf-8").read()

    # --- 1. placeholders and Elsevier's numbers -------------------------------
    # The two deposit placeholders are author actions, not manuscript defects: a
    # repository DOI cannot be created by this script.  Everything else must be filled.
    author_actions = {"Zenodo DOI", "GitHub URL"}
    left = set(re.findall(r"\\TBD\{([^}]*)\}", tex))
    check("no placeholders left (except the two deposits)",
          left <= author_actions, ", ".join(sorted(left - author_actions)))
    if left & author_actions:
        print("AUTHOR ACTION: fill", ", ".join(sorted(left & author_actions)),
              "before submitting")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    check("abstract present", m is not None)
    if m:
        body = re.sub(r"\\[a-zA-Z]+\*?", " ", m.group(1))
        body = re.sub(r"[${}~]", " ", body)
        words = len([w for w in re.split(r"\s+", body) if w.strip()])
        check("abstract <= 250 words", words <= 250, f"{words} words")
    kw = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", tex, re.S)
    check("keywords present", kw is not None)
    if kw:
        n = len([k for k in kw.group(1).split(r"\sep") if k.strip()])
        check("1 <= keywords <= 7", 1 <= n <= 7, f"{n} keywords")

    hl_path = os.path.join(D, "highlights.txt")
    if os.path.exists(hl_path):
        hl = [ln.rstrip("\n") for ln in open(hl_path, encoding="utf-8") if ln.strip()]
        check("3 <= highlights <= 5", 3 <= len(hl) <= 5, f"{len(hl)} lines")
        check("every highlight <= 85 chars", all(len(x) <= 85 for x in hl),
              f"longest {max(len(x) for x in hl)}")
    else:
        check("highlights.txt exists", False)

    # --- 2. citations -------------------------------------------------------
    cited = sorted({k.strip() for grp in re.findall(r"\\cite[pt]?\{([^}]*)\}", tex)
                    for k in grp.split(",") if k.strip()})
    bibp = os.path.join(D, "refs.bib")
    keys = set(re.findall(r"@\w+\{([^,]+),", open(bibp, encoding="utf-8").read()))
    missing = [c for c in cited if c not in keys]
    check("every cited key is in refs.bib", not missing, ", ".join(missing[:8]))
    check("cites at least 40 references", len(cited) >= 40, f"{len(cited)}")

    # --- 3. generated tables ------------------------------------------------
    rows = {}
    for name, floor in [("tab_audit.tex", 40), ("tab_kview.tex", 3),
                        ("tab_fidelity.tex", 40)]:
        p = os.path.join(D, name)
        if not os.path.exists(p):
            check(f"{name} exists", False)
            continue
        txt = open(p, encoding="utf-8").read()
        n = sum(1 for ln in txt.splitlines()
                if ln.rstrip().endswith("\\\\") and "&" in ln)
        rows[name] = (txt, n)
        check(f"{name} has >= {floor} data rows", n >= floor, f"{n} rows")
        check(f"{name} has no placeholder glyph", "TBD" not in txt)

    # --- 4. generated tables agree with the artifacts ------------------------
    if os.path.exists(AUDIT_JSON) and "tab_audit.tex" in rows:
        audit = json.load(open(AUDIT_JSON, encoding="utf-8"))
        txt = rows["tab_audit.tex"][0]
        bad = 0
        for r in audit["rows"]:
            cov = f"{100 * r['stale_mean']:.1f}"
            aud = f"{100 * r['audit_mean']:.1f}"
            if f"{cov} & {aud} &" not in txt:
                bad += 1
        check("tab_audit reproduces audit_bound.json", bad == 0, f"{bad} cells differ")
        check("audit summary present", "summary" in audit)

    if os.path.exists(DUMP_SUMMARY) and "tab_fidelity.tex" in rows:
        dump = json.load(open(DUMP_SUMMARY, encoding="utf-8"))
        txt = rows["tab_fidelity.tex"][0]
        bad = sum(1 for sc in dump["scenes"]
                  for v in sc["variants"].values()
                  if v.get("psnr") is not None and f"{v['psnr']:.2f}" not in txt)
        check("tab_fidelity reproduces dump_summary.json", bad == 0,
              f"{bad} PSNR cells differ")

    # --- 5. the numbers that must not drift ---------------------------------
    headline = ["22.1", "10.8", "27.7", "15.2", "2.4", "0.898", "0.902"]
    for h in headline:
        check(f"headline number {h} present", h in tex)

    # --- 6. the build ------------------------------------------------------
    if not args.no_pdf:
        pdf = os.path.join(D, "main.pdf")
        log = os.path.join(D, "main.log")
        pages = 0
        if os.path.exists(log):
            m = re.search(r"Output written on .*?\((\d+) pages", open(
                log, encoding="utf-8", errors="ignore").read())
            pages = int(m.group(1)) if m else 0
        check("main.pdf exists", os.path.exists(pdf))
        check("PDF page count in 18..40", 18 <= pages <= 40, f"{pages} pages")
        log = os.path.join(D, "main.log")
        if os.path.exists(log):
            lg = open(log, encoding="utf-8", errors="ignore").read()
            check("no undefined citations",
                  "Citation `" not in lg, "LaTeX reported undefined citations")
            check("no undefined references",
                  "Reference `" not in lg, "LaTeX reported undefined references")
            big = re.findall(r"Overfull \\hbox \(([2-9]\d|\d{3})\.", lg)
            check("no overfull hbox above 20pt", not big, f"{len(big)} found")

    # --- report ------------------------------------------------------------
    n = len(CHECKS)
    print(f"{n} assertions, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL", f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
