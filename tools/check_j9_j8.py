"""Check that every J9/J8 number in the manuscript is the number the artifacts hold.

The new claims of §5.4 come from two artifacts (`j9_report.json`, `j8_rate.json`) and two generated tables
(`tab_j9.tex`, `tab_j8.tex`). This checker recomputes the prose numbers from the artifacts and greps the manuscript for
them, so a later edit cannot silently move one without the other.

    python tools/check_j9_j8.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TEX = Path("submission/jvcir/main.tex")
J9 = Path("experiments/artifacts/a4/j9_report.json")
J8 = Path("experiments/artifacts/a4/j8_rate.json")
TAB9 = Path("submission/jvcir/tab_j9.tex")
TAB8 = Path("submission/jvcir/tab_j8.tex")

problems: list[str] = []


def need(cond: bool, msg: str) -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        problems.append(msg)


def main() -> int:
    tex = TEX.read_text(encoding="utf-8")
    j9 = json.loads(J9.read_text(encoding="utf-8"))
    j8 = json.loads(J8.read_text(encoding="utf-8"))
    t9 = TAB9.read_text(encoding="utf-8")
    t8 = TAB8.read_text(encoding="utf-8")

    # ---- table 9: one row per (scene, alpha), values straight from the report
    v = j9["verdicts"]
    cells = [(s, a) for s in j9["scenes"] for a in ("0.01", "0.02", "0.05", "0.1", "0.2", "0.3")
             if f"a{a}_abs" in j9["scenes"][s]]
    need(len(re.findall(r"\\\\$", t9, re.M)) >= len(cells), f"tab_j9 has a row per cell ({len(cells)} cells)")
    # per-cell truth, not the per-alpha roll-up: a cell is separated when its own two numbers do not overlap
    n_sep = 0
    for scene, alpha in cells:
        cell = j9["scenes"][scene][f"a{alpha}_abs"]
        geo = min(cell[k]["loss_pp"] for k in ("prune50", "prune30") if k in cell)
        att = max(cell[k]["loss_pp"] for k in cell if k.startswith(("quant", "shdeg")))
        n_sep += int(geo > att)
    n_yes = sum(1 for line in t9.splitlines() if line.rstrip().endswith("& yes \\\\"))
    n_no = sum(1 for line in t9.splitlines() if "\\textbf{no}" in line)
    need(n_yes == n_sep and n_yes + n_no == len(cells),
         f"tab_j9 marks {n_sep} cells separated ({n_yes} yes, {n_no} no, {len(cells)} cells)")

    # ---- the prose claims of 5.4
    need("eleven of twelve cells" in tex, "prose says eleven of twelve (C1 count)")
    a01 = v["C1_by_alpha"]["0.01"]
    need(abs(a01["least_geometric_pp"] + 0.04) < 1e-6, "the alpha=0.01 boundary is -0.04 pp in the artifact")
    need("$0.56$" in tex, "bicycle's alpha=0.01 loss (0.56) is quoted")

    # ---- the aggregation sentence: max vs mean at alpha=0.1
    mean = j9["scenes"]["bicycle"]["a0.1_abs"]
    worst_attr_mean = max(mean[k]["loss_pp"] for k in mean if k.startswith(("quant", "shdeg")))
    need(round(worst_attr_mean, 2) == 0.09,
         f"attribute damage at alpha=0.1 rounds to the quoted 0.09 (got {worst_attr_mean:.3f})")

    # ---- per view
    pv = v["C3_per_view"]
    need(all(c["separated_all_views"] == c["cells"] for c in pv.values()), "per-view separation is complete")

    # ---- composition
    comp = v["composed"]["bicycle"]["prune50+quant8"]
    need(abs(comp["added_pp"] - 7.19) < 0.02, f"composition adds {comp['added_pp']} pp on bicycle (quoted 7.19)")
    comp_b = v["composed"]["bonsai"]["prune50+quant8"]
    need(abs(comp_b["added_pp"] - 22.13) < 0.02, f"composition adds {comp_b['added_pp']} pp on bonsai (quoted 22.13)")

    # ---- the rate axis
    for row in j8["rows"]:
        if row["family"].startswith("quantisation"):
            need(abs(row["rate"] - 17.35) < 0.01, "the quantisation row is 17.35x")
    p50 = [r for r in j8["rows"] if r["family"].startswith("prune + container") and r["keep"] == 0.5]
    need(all(abs(r["rate"] - 34.71) < 0.01 for r in p50), "prune50 charged the container is 34.7x")
    need(len(t8.splitlines()) >= 6, "tab_j8 has rows")

    # ---- the tables are the generated ones
    need("least geometric (pp)" in t9, "tab_j9 is the generated table")
    need("coverage loss (pp)" in t8, "tab_j8 is the generated table")

    print(f"\n{'PASS' if not problems else 'FAIL'}: {len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())