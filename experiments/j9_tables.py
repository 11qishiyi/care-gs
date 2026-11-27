"""Render the J9 generalisation test as a table for the paper.

Reads the report `j9_analyse.py` writes and emits `tab_j9.tex`: for every scene and every tolerance, the least damaging
geometric edit against the most damaging attribute edit. A reader should be able to see, without the prose, whether the
two families overlap at any tolerance.

    python experiments/j9_tables.py --report experiments/artifacts/a4/j9_report.json --out submission/jvcir
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALPHAS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="experiments/artifacts/a4/j9_report.json")
    ap.add_argument("--out", default="submission/jvcir")
    a = ap.parse_args()

    d = json.loads(Path(a.report).read_text(encoding="utf-8"))
    scenes = d["scenes"]
    rows = []
    for scene in sorted(scenes):
        for alpha in ALPHAS:
            key = f"a{alpha}_abs"
            cell = scenes[scene].get(key)
            if not cell:
                continue
            geo = {k: v["loss_pp"] for k, v in cell.items() if k in ("prune50", "prune30")}
            attr = {k: v["loss_pp"] for k, v in cell.items() if k.startswith(("quant", "shdeg"))}
            if not geo or not attr:
                continue
            best_geo = min(geo.values())
            worst_attr = max(attr.values())
            rows.append((scene, alpha, best_geo, worst_attr, best_geo > worst_attr))

    L = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3.2pt}",
         r"\caption{The same comparison at six tolerances, on scenes the frontier figure does not use for its"
         r" headline. \emph{Least} geometric is the most forgiving deletion; \emph{worst} attribute is the least"
         r" forgiving quantisation or {SH} truncation; the two families overlap only if the first number is not"
         r" strictly above the second. Losses in coverage points at the clean model's $(1-\alpha)$ quantile.}",
         r"\label{tab:j9}",
         r"\begin{tabular}{llrrr}", r"\toprule",
         r"scene & $\alpha$ & least geometric (pp) & worst attribute (pp) & separated \\", r"\midrule"]
    for scene, alpha, g, w, sep in rows:
        L.append(f"{scene} & {alpha:g} & {g:+.2f} & {w:+.2f} & {'yes' if sep else '\\\\textbf{no}'} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    out = Path(a.out) / "tab_j9.tex"
    out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    n_sep = sum(1 for r in rows if r[4])
    print(f"{len(rows)} cells, separated in {n_sep}; wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())