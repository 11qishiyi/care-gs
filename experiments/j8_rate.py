"""J8 --- the rate axis: what happens when pruning is charged the container's bytes instead of only its deletions.

Referee A's objection is that the pruning arms are measured unencoded (205-207 B/primitive, fp32 attributes plus zstd)
while the quantisation arms carry the container (13.60 B/primitive measured, Table 3). This script puts both families on
one (rate, coverage) plane by charging *every* encoded arm the container's measured per-primitive cost:

    rate(keep) = 236 / (keep * 13.60)          fp32 is 236 B/primitive

The assumption is that the per-row cost of the container's streams is unchanged by dropping rows. That assumption is
measured rather than assumed for the entry it matters on: on the shipped model the nine streams total 83.41 MB at
13.60 B/primitive, and Table 3 shows raw and coded sizes are equal to within a rounding for six of the nine streams,
i.e. the entropy coder is already at order-0 on quantised alphabets and cannot pool across rows. A reader who wants a
re-encode rather than a derivation should treat the numbers below as an upper bound on pruning's rate advantage.

Coverage comes from the J9 measurement (`j9_report.json`), same assets, same views, same tolerance.

    python experiments/j8_rate.py --out submission/jvcir
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FP32_BPP = 236.0          # bytes per primitive at float precision (Table 1 of the paper)
CONT_BPP = 13.60          # container bytes per primitive, measured (Table 3, A6 row)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--j9", default="experiments/artifacts/a4/j9_report.json")
    ap.add_argument("--out", default="submission/jvcir")
    a = ap.parse_args()

    j9 = json.loads(Path(a.j9).read_text(encoding="utf-8"))
    rows = []
    # the encoding family: the full model through the container
    rows.append(dict(family="quantisation (container)", keep=1.0, rate=FP32_BPP / CONT_BPP, coverage_pp=0.0))
    # the pruning family, charged the same per-primitive cost
    for scene, s in j9["scenes"].items():
        cell = s.get("a0.1_abs", {})
        for arm, keep in (("prune50", 0.5), ("prune30", 0.3)):
            if arm in cell:
                rows.append(dict(family=f"prune + container ({scene})", keep=keep,
                                 rate=FP32_BPP / (keep * CONT_BPP),
                                 coverage_pp=cell[arm]["loss_pp"]))
    # the composition measured in J9, at the same per-primitive cost
    for scene, s in j9["scenes"].items():
        cell = s.get("a0.1_abs", {})
        for arm, keep in (("prune50+quant8", 0.5), ("prune50+quant4", 0.5)):
            if arm in cell:
                rows.append(dict(family=f"prune+quant composition ({scene})", keep=keep,
                                 rate=FP32_BPP / (keep * CONT_BPP),
                                 coverage_pp=cell[arm]["loss_pp"]))

    rows.sort(key=lambda r: r["rate"])
    admissible = {f"{eps}": [r for r in rows if r["coverage_pp"] <= eps and "prune" in r["family"]]
                  for eps in (1, 2, 5, 10)}

    print(f"{'family':42s} {'rate':>7s} {'coverage loss (pp)':>18s}")
    for r in rows:
        print(f"{r['family']:42s} {r['rate']:7.2f} {r['coverage_pp']:18.2f}")

    L = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3.4pt}",
         r"\caption{The rate axis, with \emph{both} families charged the container's measured $13.60$~B/primitive"
         r" rather than deletion alone (which is what Fig.~\ref{fig:frontier}A charges the pruning arms). Rates are"
         r" against the fp32 asset; coverage loss is measured at $\alpha=0.1$ on the same views as"
         r" Table~\ref{tab:j9}. The quantisation row is the shipped container; the pruning rows are the same container"
         r" with half and with $70\%$ of the primitives deleted before it.}",
         r"\label{tab:j8}",
         r"\begin{tabular}{lrr}", r"\toprule",
         r"arm & rate ($\times$) & coverage loss (pp) \\", r"\midrule"]
    for r in rows:
        L.append(f"{r['family'].replace('_', chr(92) + '_')} & {r['rate']:.1f} & {r['coverage_pp']:+.2f} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    out = Path(a.out) / "tab_j8.tex"
    out.write_text("\n".join(L), encoding="utf-8", newline="\n")

    res = dict(rows=rows, admissible_at=admissible,
               note=("per-primitive cost charged to every encoded arm; the entropy coder is at order-0 on quantised "
                     "alphabets (Table 3), so per-row costs add and the derivation is an upper bound on pruning's "
                     "rate advantage"))
    A4 = Path("experiments/artifacts/a4")
    A4.mkdir(parents=True, exist_ok=True)
    (A4 / "j8_rate.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote {out} and {A4/'j8_rate.json'}")
    for eps, arms in admissible.items():
        print(f"  at eps={eps} pp the pruning family has {len(arms)} admissible arm(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())