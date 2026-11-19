"""CVIU compliance checks that need no PDF: abstract budget, highlights, placeholders."""
import re
import sys
from pathlib import Path

D = Path("submission/cviu")


def abstract_words(tex: str) -> int:
    a = tex.split(r"\begin{abstract}")[1].split(r"\end{abstract}")[0]
    # strip TeX control sequences and math delimiters before counting, the way a
    # word processor would count the rendered text
    # keep the *content* of \emph{...} / \citep{...} braces; only control-sequence
    # names are dropped, which is what a word processor would count as rendered text
    a = re.sub(r"\\[a-zA-Z]+\*?", " ", a)
    a = re.sub(r"[${}~]", " ", a)
    a = re.sub(r"--+", "-", a)
    return len([w for w in re.split(r"\s+", a) if w.strip()])


def main() -> int:
    tex = (D / "main.tex").read_text(encoding="utf-8")
    n = abstract_words(tex)
    tbd = len(re.findall(r"\\TBD\{", tex))
    cites = sorted({k.strip() for grp in re.findall(r"\\cite[pt]?\{([^}]*)\}", tex)
                    for k in grp.split(",")})
    bib = (D / "refs.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    missing = [c for c in cites if c not in keys]
    unused = sorted(keys - set(cites))

    ok = True
    print(f"abstract words: {n}  (limit 250) -> {'OK' if n <= 250 else 'OVER'}")
    ok &= n <= 250
    print(f"placeholders left (\\TBD): {tbd} -> {'OK' if tbd == 0 else 'MUST BE FILLED'}")
    ok &= tbd == 0
    print(f"citation keys cited: {len(cites)}, in refs.bib: {len(keys)}")
    if missing:
        ok = False
        print("  MISSING from refs.bib:", ", ".join(missing))
    if unused:
        print(f"  unused entries ({len(unused)}): " + ", ".join(unused[:12]))
    print(f"keywords: {len(re.findall(r'\\\\sep', tex)) + 1} (limit 7)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
