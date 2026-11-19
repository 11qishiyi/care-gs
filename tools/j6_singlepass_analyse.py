"""J6 --- the single-pass audit, measured instead of modelled.

`tools/jvcir_resolution.py` had to *model* a single pass as `truth + N(0, sigma_cell)`, because the archived
artifacts keep only split averages. `experiments/audit_bound.py --save-splits` now stores the per-split pair
(audit estimate, true loss) for every cell, so a single pass can be read off exactly: each split *is* one pass.

Input: the `audit_single.json` pulled from the J6 node (`_pull_j6/audit_single.json`).
Output: `experiments/artifacts/a4/j6_singlepass.json` and `submission/jvcir/tab_singlepass.tex`.

    python tools/j6_singlepass_analyse.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SRC = Path("_pull_j6/audit_single.json")
A4 = Path("experiments/artifacts/a4")
SUB = Path("submission/jvcir")
EPS_LIST = [0.5, 1.0, 2.0, 5.0]
DELTAS = [0.0, 1.0, 2.0, 3.0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(SUB))
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    d = json.loads(SRC.read_text(encoding="utf-8"))
    cells = [r for r in d["rows"] if r.get("splits")]
    print(f"{len(cells)} cells with per-split pairs")

    def stats(eps: float, delta: float = 0.0) -> dict:
        decided = correct = fa = fr = 0
        for c in cells:
            for est, tru in zip(c["splits"]["est_pp"], c["splits"]["true_pp"]):
                if abs(est - eps) <= delta:
                    continue                       # unresolved: no verdict
                decided += 1
                ship = est <= eps
                ok = ship == (tru <= eps)
                correct += int(ok)
                fa += int(ship and tru > eps)
                fr += int((not ship) and tru <= eps)
        return dict(eps=eps, delta=delta, decided=decided, total=len(cells) * 400,
                    accuracy=round(correct / decided, 4) if decided else None,
                    false_accept=fa, false_reject=fr,
                    decided_frac=round(decided / (len(cells) * 400), 3))

    by_eps = [stats(e) for e in EPS_LIST]
    by_delta = [stats(1.0, dl) for dl in DELTAS]
    pooled = {
        "n_cells": len(cells),
        "cells": sorted({(c["scene"], c["variant"]) for c in cells}),
        "by_eps": by_eps,
        "eps1_by_delta": by_delta,
        "note": "each split is one audit pass; est = (clean_cov - edited_cov_on_calibration)*100, "
                "true = (clean_cov - edited_cov_on_deployment)*100",
    }
    A4.mkdir(parents=True, exist_ok=True)
    (A4 / "j6_singlepass.json").write_text(json.dumps(pooled, indent=1), encoding="utf-8")

    lines = []
    for r in by_eps:
        acc = "--" if r["accuracy"] is None else f"${100 * r['accuracy']:.1f}$"
        lines.append(f"${r['eps']:g}$ & ${100 * r['decided_frac']:.0f}$ & {acc} & "
                     f"{r['false_accept']} & {r['false_reject']} \\\\")
    tex = "\n".join([
        "\\begin{tabular}{rrrrr}", "\\toprule",
        "$\\varepsilon$ (pp) & decided (\\%) & accuracy (\\%) & false accepts & false rejects \\\\",
        "\\midrule", *lines, "\\bottomrule", "\\end{tabular}"])
    SUB.mkdir(parents=True, exist_ok=True)
    (out_dir / "tab_singlepass.tex").write_text(tex + "\n", encoding="utf-8")

    lines2 = []
    for r in by_delta:
        acc = "--" if r["accuracy"] is None else f"${100 * r['accuracy']:.1f}$"
        lines2.append(f"${r['delta']:g}$ & ${100 * r['decided_frac']:.0f}$ & {acc} & {r['false_accept']} \\\\")
    tex2 = "\n".join([
        "\\begin{tabular}{rrrr}", "\\toprule",
        "$\\delta$ (pp) & decided (\\%) & accuracy (\\%) & false accepts \\\\",
        "\\midrule", *lines2, "\\bottomrule", "\\end{tabular}"])
    (out_dir / "tab_singlepass_abstain.tex").write_text(tex2 + "\n", encoding="utf-8")

    print(f"{'eps':>5s} {'decided%':>9s} {'accuracy':>9s} {'false acc':>10s} {'false rej':>10s}")
    for r in by_eps:
        print(f"{r['eps']:5.1f} {100*r['decided_frac']:8.0f}% {100*(r['accuracy'] or 0):8.1f}% "
              f"{r['false_accept']:10d} {r['false_reject']:10d}")
    print("\nabstention at eps=1")
    for r in by_delta:
        print(f"  delta={r['delta']:.0f}  decided {100*r['decided_frac']:3.0f}%  "
              f"acc {100*(r['accuracy'] or 0):5.1f}%  FA {r['false_accept']}")
    print(f"\nwrote {A4/'j6_singlepass.json'}, {SUB/'tab_singlepass.tex'}, {SUB/'tab_singlepass_abstain.tex'}")


if __name__ == "__main__":
    main()
