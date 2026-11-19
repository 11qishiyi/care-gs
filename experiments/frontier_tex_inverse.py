"""Emit the inverse frontier table: coverage tolerance -> measured bytes needed.

The forward table ("given a cap, how much do I lose") saturates once a zero-loss point
exists at 2.8x, so every column repeats.  The inverse reading does not saturate and is
what a reader actually wants: to stay within 0.25 points, how many bytes do I need?
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import frontier as F                                              # noqa: E402
from frontier_tex import label                                    # noqa: E402

TOLS = (0.25, 0.5, 1.0, 2.0)
TEX_DIR = os.path.join("submission", "cviu")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=os.path.join("experiments", "artifacts", "a4"))
    ap.add_argument("--out", default=os.path.join(TEX_DIR, "tab_frontier_inv.tex"))
    args = ap.parse_args(argv)

    paths = [os.path.join(args.dir, s + ".json") for s in F.SOURCES]
    rows = F.load_rows([p for p in paths if os.path.exists(p)])
    inv = F.inverse(rows, TOLS)

    lines = [r"\begin{tabular}{lrrrr}", r"\toprule",
             "Asset & " + " & ".join(f"$\\le{t:g}$" for t in TOLS) + r" \\", r"\midrule"]
    for scene in sorted(inv):
        cells = []
        for t in TOLS:
            r = inv[scene].get(t)
            if r is None:
                cells.append("--")
            else:
                cells.append(f"{r['rate']:.2f}$\\times$ {label(r['variant'])}")
        lines.append(f"{scene.replace('_', chr(92) + '_')} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("WROTE", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
