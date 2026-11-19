"""JVCIR submission compliance gate (the hard items from the journal's Guide for Authors).

Checks, in order:
  * abstract   <= 250 words            (Guide: "does not exceed 250 words")
  * highlights 3-5 bullets, each <= 85 characters including spaces
  * keywords   1-7
  * no leftover \\TBD placeholders other than the allowed author-supplied DOI slots

Sources are read from the plan file while the manuscript is being written, then from the
LaTeX itself once `submission/jvcir/main.tex` exists. Exit code 1 on any failure, so it can
be used as a submission gate.

Usage:
    python tools/jvcir_compliance.py                    # auto-detect sources
    python tools/jvcir_compliance.py --tex F --plan P
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ABSTRACT_LIMIT = 250
HIGHLIGHT_LIMIT = 85
HIGHLIGHT_MIN, HIGHLIGHT_MAX = 3, 5
KEYWORD_MIN, KEYWORD_MAX = 1, 7
TBD_ALLOWED = 1  # the Zenodo DOI slot; every other placeholder is a defect


def words(text: str) -> int:
    """Count words the way a copy editor would: whitespace-separated tokens."""
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def from_tex(tex: str) -> dict:
    out: dict = {}
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if m:
        body = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", "", m.group(1))
        out["abstract"] = re.sub(r"\s+", " ", body).strip()
    m = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", tex, re.S)
    if m:
        out["keywords"] = [k.strip() for k in re.split(r"\\sep", m.group(1)) if k.strip()]
    out["tbd"] = len(re.findall(r"\\TBD", tex))
    return out


def from_plan(md: str) -> dict:
    out: dict = {}
    m = re.search(r"##\s*2 .*?\n(.*?)\n##\s*3 ", md, re.S)
    if m:
        body = "\n".join(ln.lstrip("> ").rstrip() for ln in m.group(1).strip().splitlines())
        out["abstract"] = re.sub(r"\s+", " ", body).strip()
    m = re.search(r"```(.*?)```", md.split("## 3", 1)[1] if "## 3" in md else "", re.S)
    if m:
        out["highlights"] = [ln.strip() for ln in m.group(1).strip().splitlines() if ln.strip()]
    m = re.search(r"##\s*7 .*?Keywords\s*\*?\*?(\d+)\s*[–-]\s*(\d+)", md)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", type=Path, default=Path("submission/jvcir/main.tex"))
    ap.add_argument("--plan", type=Path, default=Path("submission/jvcir/PLAN.md"))
    ap.add_argument("--highlights", type=Path, default=Path("submission/jvcir/highlights.txt"))
    args = ap.parse_args()

    info: dict = {}
    if args.tex.exists():
        info.update(from_tex(args.tex.read_text(encoding="utf-8")))
        src = str(args.tex)
    elif args.plan.exists():
        info.update(from_plan(args.plan.read_text(encoding="utf-8")))
        src = str(args.plan)
    else:
        print("no manuscript and no plan found")
        return 1
    if args.highlights.exists():
        info["highlights"] = [ln.strip() for ln in
                              args.highlights.read_text(encoding="utf-8").splitlines() if ln.strip()]

    fails: list[str] = []
    print(f"source: {src}")

    if "abstract" in info:
        n = words(info["abstract"])
        ok = n <= ABSTRACT_LIMIT
        print(f"  abstract      {n:3d} words  (<= {ABSTRACT_LIMIT})  {'OK' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"abstract {n} words > {ABSTRACT_LIMIT}")
    else:
        fails.append("abstract not found")
        print("  abstract      not found  FAIL")

    hl = info.get("highlights", [])
    if hl:
        lo = HIGHLIGHT_MIN <= len(hl) <= HIGHLIGHT_MAX
        print(f"  highlights    {len(hl)} bullets (must be {HIGHLIGHT_MIN}-{HIGHLIGHT_MAX})  "
              f"{'OK' if lo else 'FAIL'}")
        if not lo:
            fails.append(f"{len(hl)} highlights, need {HIGHLIGHT_MIN}-{HIGHLIGHT_MAX}")
        for h in hl:
            n = len(h)
            ok = n <= HIGHLIGHT_LIMIT
            print(f"    [{n:3d}/{HIGHLIGHT_LIMIT}] {'OK  ' if ok else 'FAIL'} {h}")
            if not ok:
                fails.append(f"highlight {n} chars: {h}")
    else:
        print("  highlights    not found  (WARN)")

    kw = info.get("keywords")
    if kw:
        ok = KEYWORD_MIN <= len(kw) <= KEYWORD_MAX
        print(f"  keywords      {len(kw)}  (must be {KEYWORD_MIN}-{KEYWORD_MAX})  {'OK' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"{len(kw)} keywords")
    else:
        print("  keywords      not found  (WARN — required by the Guide)")

    tbd = info.get("tbd", 0)
    ok = tbd <= TBD_ALLOWED
    print(f"  \\TBD slots    {tbd}  (allowed: {TBD_ALLOWED} = the DOI slot)  {'OK' if ok else 'FAIL'}")
    if not ok:
        fails.append(f"{tbd} TBD placeholders")

    print()
    if fails:
        print(f"FAIL — {len(fails)} problem(s)")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("PASS — all JVCIR hard items satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
