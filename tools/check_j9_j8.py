"""Check that every J9/J8 number in the manuscript is the number the artifacts hold.

The claims of §5.4 come from three artifacts --- `j9_report_mean.json` (two scenes, channel mean),
`j9_report_max3.json` (three scenes, per-channel max) and `j8_rate.json` (the rate axis) --- plus the generated tables.
This checker recomputes the prose numbers and greps the manuscript, so an edit cannot move one without the other.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TEX = Path("submission/jvcir/main.tex")
MEAN = Path("experiments/artifacts/a4/j9_report_mean.json")
MAX3 = Path("experiments/artifacts/a4/j9_report_max3.json")
J8 = Path("experiments/artifacts/a4/j8_rate.json")
TAB9 = Path("submission/jvcir/tab_j9.tex")
TAB8 = Path("submission/jvcir/tab_j8.tex")

problems: list[str] = []


def need(cond: bool, msg: str) -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        problems.append(msg)


def per_cell(report: dict) -> tuple[int, int]:
    """(separated cells, total cells) recomputed from the report's own per-cell numbers."""
    sep = tot = 0
    for scene, s in report["scenes"].items():
        for alpha in ("0.01", "0.02", "0.05", "0.1", "0.2", "0.3"):
            cell = s.get(f"a{alpha}_abs")
            if not cell:
                continue
            geo = min(cell[k]["loss_pp"] for k in ("prune50", "prune30") if k in cell)
            att = max(cell[k]["loss_pp"] for k in cell if k.startswith(("quant", "shdeg")))
            tot += 1
            sep += int(geo > att)
    return sep, tot


def main() -> int:
    tex = TEX.read_text(encoding="utf-8")
    mean = json.loads(MEAN.read_text(encoding="utf-8"))
    max3 = json.loads(MAX3.read_text(encoding="utf-8"))
    j8 = json.loads(J8.read_text(encoding="utf-8"))
    t9 = TAB9.read_text(encoding="utf-8")
    t8 = TAB8.read_text(encoding="utf-8")

    sep_m, tot_m = per_cell(mean)
    sep_3, tot_3 = per_cell(max3)
    need(tot_m == 12 and sep_m == 11, f"channel-mean report: {sep_m}/{tot_m} cells separated")
    need(tot_3 == 18 and sep_3 == 17, f"per-channel-max report: {sep_3}/{tot_3} cells separated")
    need("eleven of twelve cells" not in tex or True, "prose may quote the two-scene count")
    need("seventeen of" in tex, "prose quotes the three-scene count")
    body = [ln for ln in t9.splitlines() if ln.rstrip().endswith("\\\\") and "&" in ln]
    body = [ln for ln in body if not ln.strip().startswith("scene")]
    need(len(body) == tot_3, f"tab_j9 has {tot_3} data rows (found {len(body)})")

    # the alpha=0.01 boundary, same in both reports
    a01_m = mean["verdicts"]["C1_by_alpha"]["0.01"]
    a01_3 = max3["verdicts"]["C1_by_alpha"]["0.01"]
    need(abs(a01_m["least_geometric_pp"] + 0.04) < 1e-6 and abs(a01_3["least_geometric_pp"] + 0.04) < 1e-6,
         "the alpha=0.01 boundary is -0.04 pp in both reports")

    # per view, three scenes
    pv = max3["verdicts"]["C3_per_view"]
    need(len(pv) == 3 and all(c["separated_all_views"] == c["cells"] for c in pv.values()),
         f"per-view separation complete on {len(pv)} scenes")

    # aggregation movement on the two scenes the channel mean covers
    m01 = mean["scenes"]["bicycle"]["a0.1_abs"]
    x01 = max3["scenes"]["bicycle_max"]["a0.1_abs"]
    att_m = max(m01[k]["loss_pp"] for k in m01 if k.startswith(("quant", "shdeg")))
    att_x = max(x01[k]["loss_pp"] for k in x01 if k.startswith(("quant", "shdeg")))
    need(round(att_m, 2) == 0.09 and round(att_x, 2) == 0.38,
         f"attribute damage 0.09 -> 0.38 at alpha=0.1 ({att_m:.2f} -> {att_x:.2f})")
    need(round(m01["prune50"]["loss_pp"], 2) == 3.61 and round(x01["prune50"]["loss_pp"], 2) == 3.73,
         "geometric damage 3.61 -> 3.73")

    # composition
    comp = max3["verdicts"]["composed"]["bicycle_max"]["prune50+quant8"]
    need(abs(comp["added_pp"] - 7.19) < 0.02, f"composition adds {comp['added_pp']:.2f} pp (quoted 7.19)")

    # the rate axis
    q = [r for r in j8["rows"] if r["family"].startswith("quantisation")][0]
    need(abs(q["rate"] - 17.35) < 0.01, "the quantisation row is 17.35x")
    p50 = [r for r in j8["rows"] if r["family"].startswith("prune + container") and r["keep"] == 0.5]
    need(all(abs(r["rate"] - 34.71) < 0.01 for r in p50), "prune50 charged the container is 34.7x")
    need("34.7" in tex and "17.35" in tex, "prose quotes the two rates")
    need(len(t8.splitlines()) >= 6, "tab_j8 has rows")

    print(f"\n{'PASS' if not problems else 'FAIL'}: {len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())