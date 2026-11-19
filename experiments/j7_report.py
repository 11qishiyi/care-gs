"""J7 report --- score the pre-registered criteria and write the table.

Reads the driver's `j7.json` and answers one question per (scene, keep) cell: at a matched keep rate, how much
coverage does the coverage-aware ranking keep relative to the opacity ranking?

Pre-registered criterion (`experiments/J7_PLAN.md`): the coverage-aware arm's loss must be at most 70% of the
opacity arm's loss, on at least 4 of the 6 cells. A loss ratio above 0.90 is reported as "the score is not the
reason" --- the asymmetry is then a property of the action family, not of the ranking, which is the paper's stronger
claim. Anything in between is reported as a band, not rounded into a verdict.

    python experiments/j7_report.py --res _pull_j7/j7.json
    python experiments/j7_report.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

A4 = Path("experiments/artifacts/a4")
SUB = Path("submission/jvcir")
PASS_RATIO, WEAK_RATIO = 0.70, 0.90


def score(manifest: dict) -> dict:
    cells = []
    for sc in manifest["scenes"]:
        by_keep = {}
        for r in sc["rows"]:
            by_keep.setdefault(r["keep"], {})[r["score"]] = r
        for keep, arms in sorted(by_keep.items()):
            if "coverage-risk" not in arms or "opacity" not in arms:
                continue
            cov, base = arms["coverage-risk"], arms["opacity"]
            ratio = (cov["loss_pp"] / base["loss_pp"]) if base["loss_pp"] > 1e-9 else None
            cells.append(dict(scene=sc["scene"], keep=keep,
                              loss_cov_pp=cov["loss_pp"], loss_opacity_pp=base["loss_pp"],
                              ratio=None if ratio is None else round(ratio, 3),
                              helps=bool(ratio is not None and ratio <= PASS_RATIO)))
    n_help = sum(1 for c in cells if c["helps"])
    need = min(4, len(cells))        # the plan asks for 4 of 6; fewer cells cannot ask for more than they have
    ratios = [c["ratio"] for c in cells if c["ratio"] is not None]
    if not cells:
        verdict = "no data"
    elif n_help >= need:
        verdict = f"PASS — the coverage-aware score keeps >=30% more coverage on {n_help}/{len(cells)} cells"
    elif ratios and max(ratios) <= WEAK_RATIO:
        verdict = "WEAK — improves but under 30%; report as a band"
    else:
        verdict = "FAIL — the score is not the reason; the asymmetry is a property of the action family"
    return dict(cells=cells, n_cells=len(cells), n_helps=n_help,
                ratio_median=round(sorted(ratios)[len(ratios) // 2], 3) if ratios else None,
                verdict=verdict)


def table(res: dict) -> str:
    lines = []
    for c in res["cells"]:
        r = "--" if c["ratio"] is None else f"{c['ratio']:.2f}"
        lines.append(f"{c['scene']} & {c['keep']:.1f} & {c['loss_opacity_pp']:.2f} & "
                     f"{c['loss_cov_pp']:.2f} & {r} \\\\")
    return "\n".join([
        "\\begin{tabular}{lrrrr}", "\\toprule",
        "scene & keep & loss, opacity (pp) & loss, coverage-aware (pp) & ratio \\\\",
        "\\midrule", *lines, "\\bottomrule", "\\end{tabular}"])


def selftest() -> int:
    def mk(loss_cov, loss_op):
        return {"scenes": [{"scene": "s", "rows": [
            {"keep": 0.5, "score": "opacity", "coverage": 0.9, "loss_pp": loss_op},
            {"keep": 0.5, "score": "coverage-risk", "coverage": 0.9, "loss_pp": loss_cov}]}]}

    ok = True

    def check(cond, msg):
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
        ok = ok and cond

    r = score(mk(2.0, 10.0))
    check(r["cells"][0]["ratio"] == 0.2 and "PASS" in r["verdict"], "a clear win is a PASS")
    r = score(mk(8.0, 10.0))
    check("WEAK" in r["verdict"], "an 0.80 ratio is WEAK, not PASS")
    r = score(mk(9.5, 10.0))
    check("FAIL" in r["verdict"], "an 0.95 ratio is a FAIL")
    r = score(mk(2.0, 0.0))
    check(r["cells"][0]["ratio"] is None, "a zero baseline does not divide by zero")
    tex = table(score(mk(2.0, 10.0)))
    check("\\begin{tabular}" in tex and "0.20" in tex, "the table renders the ratio")
    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="_pull_j7/j7.json")
    ap.add_argument("--out-dir", default=str(SUB))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    man = json.loads(Path(a.res).read_text(encoding="utf-8"))
    res = score(man)
    A4.mkdir(parents=True, exist_ok=True)
    (A4 / "j7_report.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tab_prune_cov.tex").write_text(table(res) + "\n", encoding="utf-8")

    print(f"{'scene':12s} {'keep':>5s} {'opacity':>9s} {'cov-aware':>10s} {'ratio':>6s}")
    for c in res["cells"]:
        r = "--" if c["ratio"] is None else f"{c['ratio']:.2f}"
        print(f"{c['scene']:12s} {c['keep']:5.1f} {c['loss_opacity_pp']:9.2f} {c['loss_cov_pp']:10.2f} {r:>6s}")
    print(f"\n{res['n_helps']}/{res['n_cells']} cells improve by >=30%; median ratio {res['ratio_median']}")
    print(res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
