"""J8 report --- does the action-family asymmetry survive when both families use the same container?

Reads the driver's `j8.json` and answers one question: at a matched rate, how much more coverage does the pruning
family lose than the quantisation family, once both are encoded with the same container?

Pre-registered branches (`experiments/J8_PLAN.md`, written before the run):

    ratio >= 3.0    the asymmetry survives; keep C1 but restrict the wording to the grid we tested
    1.5 .. 3.0      the claim weakens to "quantisation is steadier"; drop the word decoupling
    <= 1.5          the claim is overturned; the paper's centre has to move to the container plus the audit

The comparison is made at *matched rate*: for every pruning point the quantisation arms are interpolated (in log rate
versus coverage loss) to the pruning point's rate, so neither family is charged for an operating point it does not
have.

    python experiments/j8_report.py --res _pull_j8/j8.json
    python experiments/j8_report.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

A4 = Path("experiments/artifacts/a4")
SUB = Path("submission/jvcir")
KEEP_C1, WEAK = 3.0, 1.5


def interp_loss(points: list[tuple[float, float]], rate: float) -> float | None:
    """Coverage loss of the quantisation family at `rate`, interpolated in log-rate; None if outside its span."""
    pts = sorted(p for p in points if p[0] > 0)
    if not pts or not (pts[0][0] <= rate <= pts[-1][0]):
        return None
    import math
    for (r0, l0), (r1, l1) in zip(pts, pts[1:]):
        if r0 <= rate <= r1:
            if r1 == r0:
                return l0
            w = (math.log(rate) - math.log(r0)) / (math.log(r1) - math.log(r0))
            return l0 + w * (l1 - l0)
    return pts[-1][1]


def score(manifest: dict) -> dict:
    cells = []
    for sc in manifest["scenes"]:
        quant = [(r["rate"], r["loss_pp"]) for r in sc["rows"] if r["arm"] == "prune+container" and r["keep"] == 1.0]
        quant += [(r["rate"], r["loss_pp"]) for r in sc["rows"] if r["arm"] == "quant-only"]
        for r in sc["rows"]:
            if r["arm"] != "prune+container" or r["keep"] == 1.0:
                continue
            base = interp_loss(quant, r["rate"])
            ratio = (r["loss_pp"] / base) if (base and base > 1e-9) else None
            cells.append(dict(scene=sc["scene"], keep=r["keep"], rate=r["rate"],
                              loss_prune_pp=r["loss_pp"],
                              loss_quant_at_same_rate_pp=None if base is None else round(base, 2),
                              ratio=None if ratio is None else round(ratio, 2)))
    ratios = [c["ratio"] for c in cells if c["ratio"] is not None]
    if not ratios:
        verdict = "no comparable cell (the quantisation curve does not span the pruning rates)"
    elif min(ratios) >= KEEP_C1:
        verdict = "A — the asymmetry survives: keep C1, restrict it to the pruning grid we tested"
    elif min(ratios) >= WEAK:
        verdict = "B — weakened: say quantisation is steadier and drop the word decoupling"
    else:
        verdict = "C — OVERTURNED: the action family does not decide; the paper's centre must move"
    med = sorted(ratios)[len(ratios) // 2] if ratios else None
    return dict(cells=cells, n_cells=len(cells), ratio_median=med, ratio_min=min(ratios) if ratios else None,
                verdict=verdict)


def table(res: dict) -> str:
    lines = [f"{c['scene']} & {c['keep']:.1f} & {c['rate']:.1f} & {c['loss_prune_pp']:.2f} & "
             f"{'-' if c['loss_quant_at_same_rate_pp'] is None else f'{c[chr(39)+chr(39)] if False else c['loss_quant_at_same_rate_pp']:.2f}'} & "
             f"{'-' if c['ratio'] is None else f'{c[chr(39)+chr(39)] if False else c['ratio']:.2f}'} \\\\"
             for c in res["cells"]]
    return "\n".join([
        "\\begin{tabular}{lrrrrr}", "\\toprule",
        "scene & keep & rate & loss, prune+container (pp) & loss, quantisation at same rate (pp) & ratio \\\\",
        "\\midrule", *lines, "\\bottomrule", "\\end{tabular}"])


def selftest() -> int:
    def mk(pairs, quant):
        rows = [dict(keep=1.0, arm="prune+container", rate=quant[0][0], loss_pp=quant[0][1])]
        rows += [dict(keep=k, arm="prune+container", rate=r, loss_pp=l) for k, r, l in pairs]
        rows += [dict(keep=1.0, arm="quant-only", rate=r, loss_pp=l) for r, l in quant]
        return {"scenes": [{"scene": "s", "rows": rows}]}

    ok = True

    def check(cond, msg):
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
        ok = ok and cond

    quant = [(8.0, 0.5), (16.0, 2.0), (32.0, 6.0)]
    r = score(mk([(0.9, 16.0, 12.0)], quant))          # 12 pp against 2 pp at the same rate
    check(r["cells"][0]["ratio"] == 6.0 and r["verdict"].startswith("A"), "a 6x gap reads as branch A")
    r = score(mk([(0.9, 16.0, 4.0)], quant))
    check(r["verdict"].startswith("B"), "a 2x gap reads as branch B")
    r = score(mk([(0.9, 16.0, 1.6)], quant))
    check(r["verdict"].startswith("C"), "an 0.8x gap reads as branch C (overturned)")
    r = score(mk([(0.9, 90.0, 3.0)], quant))
    check(r["cells"][0]["ratio"] is None, "a rate outside the quantisation span is not scored")
    check("\\begin{tabular}" in table(score(mk([(0.9, 16.0, 12.0)], quant))), "the table renders")
    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="_pull_j8/j8.json")
    ap.add_argument("--out-dir", default=str(SUB))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    man = json.loads(Path(a.res).read_text(encoding="utf-8"))
    res = score(man)
    A4.mkdir(parents=True, exist_ok=True)
    (A4 / "j8_report.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tab_j8.tex").write_text(table(res) + "\n", encoding="utf-8")

    print(f"{'scene':10s} {'keep':>5s} {'rate':>7s} {'prune':>8s} {'quant@rate':>11s} {'ratio':>6s}")
    for c in res["cells"]:
        q = "--" if c["loss_quant_at_same_rate_pp"] is None else f"{c['loss_quant_at_same_rate_pp']:.2f}"
        rr = "--" if c["ratio"] is None else f"{c['ratio']:.2f}"
        print(f"{c['scene']:10s} {c['keep']:5.1f} {c['rate']:7.1f} {c['loss_prune_pp']:8.2f} {q:>11s} {rr:>6s}")
    print(f"\nmedian ratio {res['ratio_median']}, min {res['ratio_min']}")
    print(res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
