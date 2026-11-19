"""Audit resolution and the abstention band.

Two objects have to be separated, and they give very different numbers:

  (a) the **split-averaged** estimate --- what Table 8 uses, and what gives 56/56;
  (b) a **single pass** --- what a recipient actually runs. Modelled here as `truth + N(0, sigma_cell)` with
      `sigma_cell` the per-cell mean absolute error over the 400 splits.

A single pass cannot decide cells that sit within its own error of the tolerance, so the usable object is a
decision rule **with an abstention band**: ship iff the audit estimate is below `eps - delta`, refuse iff it is
above `eps + delta`, and report *unresolved* in between. This script measures that rule's operating
characteristic --- how many cells it decides, at what accuracy, with how many false accepts --- for delta in
{0, 1, 2, 3} pp.

The Gaussian single-pass model is an assumption, stated as such: the per-split values are not in the artifacts.

    python tools/jvcir_resolution.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import argparse

A4 = Path("experiments/artifacts/a4")
SUB = Path("submission/jvcir")
SRC = Path("results_v120/audit_bound_nobonsai.json")
BUCKETS = [("at the boundary", 0.0, 1.0), ("near", 1.0, 2.0), ("clear", 2.0, 5.0), ("far", 5.0, 1e9)]
EPS_LIST = [0.5, 1.0, 2.0, 5.0]
DELTAS = [0.0, 1.0, 2.0, 3.0]


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(SUB))
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    d = json.loads((A4 / "j2_audit_decision.json").read_text(encoding="utf-8"))
    cells = d["per_cell"]
    sigma = {}
    if SRC.exists():
        for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"]:
            sigma[(r["scene"], r["variant"])] = float(r["audit_mae_pp"])
    for c in cells:
        c["sigma"] = sigma.get((c["scene"], c["variant"]), 2.0)

    # ---- (a) split-averaged, bucketed by distance from the tolerance
    buckets = []
    for label, lo, hi in BUCKETS:
        pairs = [(c, e) for c in cells for e in EPS_LIST if lo <= abs(c["truth"] - e) < hi]
        if not pairs:
            continue
        acc = sum(1 for c, e in pairs if (c["audit"] <= e) == (c["truth"] <= e)) / len(pairs)
        fa = sum(1 for c, e in pairs if c["audit"] <= e < c["truth"])
        buckets.append(dict(bucket=label, n_cells=len({id(c) for c, _ in pairs}), n_pairs=len(pairs),
                            accuracy=round(acc, 3), false_accept=fa))

    # ---- (b) single pass, expected decisions
    single = []
    for e in EPS_LIST:
        fa = sum(phi((e - c["truth"]) / max(1e-6, c["sigma"])) for c in cells if c["truth"] > e)
        fr = sum(1.0 - phi((e - c["truth"]) / max(1e-6, c["sigma"])) for c in cells if c["truth"] <= e)
        single.append(dict(eps=e, expected_false_accept=round(fa, 2), expected_false_reject=round(fr, 2),
                           expected_accuracy=round(1.0 - (fa + fr) / len(cells), 3)))

    # ---- (c) the abstention rule on the split-averaged estimate
    abstain = []
    for delta in DELTAS:
        decided = correct = fa = 0
        for c in cells:
            for e in EPS_LIST:
                a = c["audit"]
                if abs(a - e) <= delta:
                    continue                                   # unresolved: neither ship nor refuse
                decided += 1
                correct += int((a <= e) == (c["truth"] <= e))
                fa += int(a <= e < c["truth"])
        abstain.append(dict(delta=delta, decided=decided, of=len(cells) * len(EPS_LIST),
                            accuracy=round(correct / decided, 3) if decided else None, false_accept=fa))

    # ---- (d) abstention on a *single pass*: P(false accept) = P(a <= eps - delta | truth > eps)
    pass_abstain = []
    for delta in DELTAS:
        for e in EPS_LIST:
            fa = sum(phi((e - delta - c["truth"]) / max(1e-6, c["sigma"]))
                     for c in cells if c["truth"] > e)
            decided = sum(
                (phi((e - c["truth"]) / max(1e-6, c["sigma"])) - phi((e + delta - c["truth"]) / max(1e-6, c["sigma"])))
                + (1.0 - phi((e - delta - c["truth"]) / max(1e-6, c["sigma"])))
                if c["truth"] > e else
                (phi((e - delta - c["truth"]) / max(1e-6, c["sigma"]))
                 + (phi((e + delta - c["truth"]) / max(1e-6, c["sigma"])) - phi((e - c["truth"]) / max(1e-6, c["sigma"]))))
                for c in cells)
            pass_abstain.append(dict(delta=delta, eps=e, expected_false_accept=round(fa, 3),
                                     expected_decided=round(decided, 1), of=len(cells)))

    out = {"source": "j2_audit_decision.json + audit_bound_nobonsai.json",
           "note": "d = |truth - eps|; single pass modelled as truth + N(0, sigma_cell); "
                   "abstention rule: unresolved when |audit - eps| <= delta",
           "split_averaged_by_distance": buckets, "single_pass_model": single,
           "abstention": abstain, "single_pass_abstention": pass_abstain}
    (A4 / "j5_resolution.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    lines = [f"{a['bucket']} & {a['n_cells']} & {a['n_pairs']} & ${a['accuracy'] * 100:.0f}$ & "
             f"{a['false_accept']} \\\\" for a in buckets]
    tex = "\n".join([
        "\\begin{tabular}{lrrrr}", "\\toprule",
        "$|\\ell-\\varepsilon|$ & cells & pairs & accuracy (\\%) & false accepts \\\\",
        "\\midrule", *lines, "\\bottomrule", "\\end{tabular}"])
    (out_dir / "tab_resolution.tex").write_text(tex + "\n", encoding="utf-8")

    lines2 = [f"{a['delta']:.0f} & {a['decided']}/{a['of']} & "
              f"${100 * (a['accuracy'] or 0):.0f}$ & {a['false_accept']} \\\\" for a in abstain]
    tex2 = "\n".join([
        "\\begin{tabular}{rrrr}", "\\toprule",
        "$\\delta$ (pp) & decisions taken & accuracy (\\%) & false accepts \\\\",
        "\\midrule", *lines2, "\\bottomrule", "\\end{tabular}"])
    (out_dir / "tab_abstain.tex").write_text(tex2 + "\n", encoding="utf-8")

    print("(a) split-averaged estimate, by distance from the tolerance")
    print(f"{'bucket':18s} {'cells':>6s} {'pairs':>6s} {'accuracy':>9s} {'false acc':>10s}")
    for a in buckets:
        print(f"{a['bucket']:18s} {a['n_cells']:6d} {a['n_pairs']:6d} {a['accuracy'] * 100:8.1f}% "
              f"{a['false_accept']:10d}")
    print("\n(b) single pass (modelled): expected decisions over 56 cells")
    for s in single:
        print(f"  eps={s['eps']:.1f}  E[false accept]={s['expected_false_accept']:.2f}  "
              f"E[false reject]={s['expected_false_reject']:.2f}  E[accuracy]={s['expected_accuracy']:.3f}")
    print("\n(c) abstention rule on the split-averaged estimate")
    print(f"{'delta':>6s} {'decided':>12s} {'accuracy':>9s} {'false acc':>10s}")
    for a in abstain:
        acc = "n/a" if a["accuracy"] is None else f"{a['accuracy'] * 100:.1f}%"
        print(f"{a['delta']:6.1f} {a['decided']:5d}/{a['of']:<6d} {acc:>9s} {a['false_accept']:10d}")
    print("\n(d) abstention on a single pass (modelled)")
    for a in pass_abstain:
        if a["eps"] in (1.0, 2.0):
            print(f"  eps={a['eps']:.1f} delta={a['delta']:.0f}  E[decided]={a['expected_decided']:.1f}/{a['of']} "
                  f" E[false accept]={a['expected_false_accept']:.3f}")
    print(f"\nwrote {A4/'j5_resolution.json'}, {SUB/'tab_resolution.tex'}, {SUB/'tab_abstain.tex'}")


if __name__ == "__main__":
    main()
