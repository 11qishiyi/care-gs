#!/usr/bin/env python3
"""M5 report: the M3 verdicts side by side on the model axis and the measured axis.

Usage:
  python experiments/m5_report.py --model experiments/artifacts/a4/m3_rd.json \
                                  --measured experiments/artifacts/a4/m5_rd.json \
                                  [--out m5_tables.md]
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys


def _load(path: str) -> dict:
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _rates(doc: dict) -> list:
    return [float(r) for r in doc["summary"]["rates"]]


def e1_side_by_side(model: dict, meas: dict, rates: list) -> list:
    cm = model["summary"]["criteria"]["E1_universal_dominance"]
    cd = meas["summary"]["criteria"]["E1_universal_dominance"]
    lines = ["| rate | model axis (mean / min / assets) | measured axis (mean / min / assets) | shift |",
             "|---|---|---|---|"]
    for r in rates:
        k = f"{r:.1f}"
        a = cm["per_rate"].get(k) or {}
        b = cd["per_rate"].get(k) or {}
        if not a.get("n_scenes") and not b.get("n_scenes"):
            lines.append(f"| {r:g}× | no pair | no pair | — |")
            continue

        def cell(v):
            if not v.get("n_scenes"):
                return "no pair"
            return (f"{v['mean_pp']:+.2f} pp / {v['min_scene_pp']:+.2f} / "
                    f"{v['n_positive']}/{v['n_scenes']}")

        shift = "—"
        if a.get("n_scenes") and b.get("n_scenes"):
            shift = f"{b['mean_pp'] - a['mean_pp']:+.2f} pp"
        lines.append(f"| {r:g}× | {cell(a)} | {cell(b)} | {shift} |")
    lines.append("")
    lines.append(f"model verdict **{cm['verdict']}** ({cm['rates_passing']}/"
                 f"{cm['rates_total']}, need {cm['threshold_rates_needed']}); "
                 f"measured verdict **{cd['verdict']}** ({cd['rates_passing']}/"
                 f"{cd['rates_total']}, need {cd['threshold_rates_needed']})")
    return lines


def frontier_table(model: dict, meas: dict) -> list:
    em = model["summary"]["criteria"]["E3_frontier_above_8x"]
    ed = meas["summary"]["criteria"]["E3_frontier_above_8x"]
    lines = ["| asset | model-axis frontier | measured-axis frontier | members ≥8× (measured) |",
             "|---|---|---|---|"]
    for name in em["per_scene"]:
        a = em["per_scene"][name]
        b = ed["per_scene"].get(name) or {}
        mem = ", ".join(f"{m['variant']} ({m['rate']:.2f}×)" for m in b.get("members", [])) or "none"
        lines.append(f"| {name} | {a['frontier_rate']:.2f}× | "
                     f"{b.get('frontier_rate', float('nan')):.2f}× | {mem} |")
    lines.append("")
    lines.append(f"model: {em['assets_with_member']}/{model['summary']['n_scenes']} assets, "
                 f"verdict **{em['verdict']}**; measured: "
                 f"{ed['assets_with_member']}/{meas['summary']['n_scenes']} assets, "
                 f"verdict **{ed['verdict']}**")
    return lines


def rate_shift_table(model: dict, meas: dict) -> list:
    """Per-asset rate of the same variant on both axes (the axis is a relabelling)."""
    mm = {}
    for sc in model["scenes"]:
        for row in sc["rows"]:
            mm[(sc["scene"], row["variant"])] = row["rate"]
    lines = ["| asset | variant | model rate | measured rate | measured/model |",
             "|---|---|---|---|---|"]
    for sc in meas["scenes"]:
        for row in sc["rows"]:
            a = mm.get((sc["scene"], row["variant"]))
            b = row["rate"]
            if a is None or b is None:
                continue
            lines.append(f"| {sc['scene']} | {row['variant']} | {a:.2f}× | {b:.2f}× | "
                         f"{b / a:.2f} |")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M5 model vs measured axis")
    ap.add_argument("--model", required=True)
    ap.add_argument("--measured", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--rates", default=None, help="override, e.g. 5,7,9,12")
    ap.add_argument("--shift-table", action="store_true", help="also print per-variant rates")
    args = ap.parse_args(argv)
    model, meas = _load(args.model), _load(args.measured)
    rates = [float(x) for x in args.rates.split(",")] if args.rates else _rates(meas)
    out = [f"outcome model `{model['summary']['outcome']}` → measured "
           f"`{meas['summary']['outcome']}`", "", "### E1 on both axes", ""]
    out += e1_side_by_side(model, meas, rates)
    out += ["", "### Near-lossless frontier on both axes", ""]
    out += frontier_table(model, meas)
    if args.shift_table:
        out += ["", "### Axis shift per variant", ""] + rate_shift_table(model, meas)
    text = "\n".join(out) + "\n"
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"WROTE {args.out} ({len(text)} chars)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
