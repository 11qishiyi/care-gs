#!/usr/bin/env python3
"""Render the M3 verdicts (E1/E2/E3) as markdown tables from ``m3_rd.json``.

Usage:  python experiments/m3_report.py --json art.json [--out out.md] [--rates 5,7,9,12]
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def _load(path: str) -> dict:
    if path.endswith(".gz"):
        import gzip
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _f(v, fmt: str = "{:+.2f}", dash: str = "—") -> str:
    return dash if v is None else fmt.format(v)


def e1_table(doc: dict, rates) -> list:
    lines = ["| asset | " + " | ".join(f"{r:g}× (QFP / prune / Δ)" for r in rates) + " |",
             "|---|" + "---|" * len(rates)]
    for sc in doc["scenes"]:
        cells = []
        for r in rates:
            # the JSON keys are the ``str(float)`` of the rate ("5.0"), not "5"
            key = f"{float(r):.1f}"
            c = (sc["comparisons"] or {}).get(key)
            m = (sc["matched"] or {}).get(key)
            if not c or not m:
                cells.append("—")
                continue
            cells.append(f"{m['qfp']['drop_pp']:+.2f} / {m['prune']['drop_pp']:+.2f} / "
                         f"**{c['coverage']['mean_pp']:+.2f}**")
        lines.append(f"| {sc['scene']} | " + " | ".join(cells) + " |")
    e1 = doc["summary"]["criteria"]["E1_universal_dominance"]
    lines.append("")
    lines.append(f"pooled mean Δ by rate: " + ", ".join(
        f"{k}× {v['mean_pp']:+.2f} pp (min {v['min_scene_pp']:+.2f}, "
        f"{v['n_positive']}/{v['n_scenes']} assets)"
        for k, v in e1["per_rate"].items() if v.get("n_scenes")))
    return lines


def e2_table(doc: dict) -> list:
    e2 = doc["summary"]["criteria"]["E2_degree_vs_bits"]
    lines = ["| asset | degree-truncated | bits-truncated | Δ (deg − bits) | winner |",
             "|---|---|---|---|---|"]
    for name, v in e2["per_scene"].items():
        dg, bt = v["degree"], v["bits"]
        lines.append(f"| {name} | {dg['variant']} {dg['drop_pp']:+.2f} pp | "
                     f"{bt['variant']} {bt['drop_pp']:+.2f} pp | "
                     f"{v['diff_pp']:+.2f} pp | "
                     f"{'degree' if v['diff_pp'] > 0 else 'bits'} |")
    lines.append("")
    lines.append(f"winner **{e2['winner']}**, mean Δ {e2['mean_pp']:+.3f} pp, "
                 f"agreement {e2['n_agree']}/{e2['n_scenes_with_both']}, "
                 f"window {e2['window_bytes'][0]:g}–{e2['window_bytes'][1]:g} B, "
                 f"verdict **{e2['verdict']}**")
    return lines


def e3_table(doc: dict) -> list:
    e3 = doc["summary"]["criteria"]["E3_frontier_above_8x"]
    lines = ["| asset | members ≥8× (≤1.0 pp, ≤0.3 dB) | best near-lossless rate |",
             "|---|---|---|"]
    for name, v in e3["per_scene"].items():
        mem = ", ".join(f"{m['variant']} ({m['rate']:.2f}×, {m['drop_pp']:+.2f} pp)"
                        for m in v["members"]) or "none"
        lines.append(f"| {name} | {mem} | {v['frontier_rate']:.2f}× |")
    lines.append("")
    lines.append(f"assets with a member **{e3['assets_with_member']}/{doc['summary']['n_scenes']}** "
                 f"(need {e3['threshold_assets']}), verdict **{e3['verdict']}**")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M3 verdict tables")
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--rates", default="5,7,9,12")
    args = ap.parse_args(argv)
    rates = [float(x) for x in args.rates.split(",") if x.strip()]
    doc = _load(args.json)
    s = doc["summary"]
    out = [f"outcome `{s['outcome']}` over {s['n_scenes']} assets", "",
           "### E1 — dominance at matched bytes", ""]
    out += e1_table(doc, rates) + ["", "### E2 — degree truncation vs. bit truncation", ""]
    out += e2_table(doc) + ["", "### E3 — near-lossless shelf above 8×", ""]
    out += e3_table(doc)
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
