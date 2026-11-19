#!/usr/bin/env python3
"""Print the markdown tables that ``M5_RESULTS.md`` quotes.

Reads the measured-byte analysis (``m5_rd.json``) plus, optionally, the older
analysis (``--prev``) so the effect of the truncation-slice fix can be reported
spec-by-spec.

    python experiments/m5_tables.py \
        --json experiments/artifacts/a4/m5_rd.json \
        --prev experiments/artifacts/a4/m5_rd_v1.json
"""
from __future__ import annotations

import argparse
import gzip
import json
import os


def _load(path: str):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verdicts(doc):
    s = doc["summary"]
    print("| 判据 | 结果 |")
    print("|---|---|")
    for key, val in s["criteria"].items():
        if "verdict" in val:
            passing = val.get("rates_passing")
            total = val.get("rates_total")
            extra = ""
            if passing is not None and total is not None:
                extra = f"，{passing}/{total} 个码率点"
            print(f"| `{key}` | **{val['verdict']}**{extra} |")
    print(f"\noutcome = `{s['outcome']}`  rate_source = `{doc['meta'].get('rate_source')}`  "
          f"n_measured = {doc['meta'].get('n_measured')}")


def e1_table(doc, rates):
    print("\n### E1 逐资产（QFP 覆盖损失 / prune 覆盖损失 / 差值，pp）\n")
    head = "| 资产 | clean cov | clean PSNR | " + " | ".join(f"{r}×" for r in rates) + " |"
    print(head)
    print("|" + "---|" * (3 + len(rates)))
    for sc in doc["scenes"]:
        cells = []
        for r in rates:
            m = sc["matched"].get(str(r)) or {}
            q, p = m.get("qfp"), m.get("prune")
            if q and p and q.get("covered") and p.get("covered"):
                cells.append(f"{q['drop_pp']:+.2f} / {p['drop_pp']:+.2f} / "
                             f"**{q['drop_pp'] - p['drop_pp']:+.2f}**")
            else:
                cells.append("—")
        cov = sc.get("clean_coverage")
        cov = f"{100.0 * cov:.2f}%" if cov is not None and cov <= 1.0 else f"{cov}"
        print(f"| {sc['scene']} | {cov} | {sc['clean_psnr']:.2f} | " + " | ".join(cells) + " |")


def fidelity_table(doc, rates):
    print("\n### 保真（QFP − prune）\n")
    print("| 码率 | ΔPSNR 均值 | ΔPSNR 最小 | ΔSSIM 最小 | ΔLPIPS 最大 | 资产数 |")
    print("|---|---|---|---|---|---|")
    d2 = doc["summary"]["criteria"]["D2_fidelity_not_worse"]["per_rate"]
    for r in rates:
        row = d2.get(str(r))
        if not row or not row.get("n_scenes"):
            continue
        print(f"| {r}× | {row['mean_dPSNR']:+.2f} dB | {row['min_dPSNR']:+.2f} dB | "
              f"{row['min_dSSIM']:+.4f} | {row['max_dLPIPS']:+.4f} | {row['n_scenes']} |")


def e3_table(doc):
    print("\n### E3 近无损前沿\n")
    print("| 资产 | frontier | 成员 |")
    print("|---|---|---|")
    for name, row in doc["summary"]["criteria"]["E3_frontier_above_8x"]["per_scene"].items():
        mem = row.get("members", [])
        best = max(mem, key=lambda m: m["rate"]) if mem else None
        cells = ", ".join(f"`{m['variant']}`@{m['rate']:.2f}× ({m['drop_pp']:+.2f}pp, "
                          f"{m['d_psnr']:+.2f}dB)" for m in mem[:3])
        if len(mem) > 3:
            cells += f", … (共 {len(mem)})"
        print(f"| {name} | {row['frontier_rate']:.2f}× | {cells} |")


def shift_table(doc, prev, scenes=("bicycle", "flowers")):
    if not prev:
        return
    print("\n### 修复前后（d* 变体）\n")
    print("| 资产 | 变体 | 旧 axis 码率 | 新 axis 码率 | 旧 drop | 新 drop |")
    print("|---|---|---|---|---|---|")
    pv = {s["scene"]: {r["variant"]: r for r in s["rows"]} for s in prev["scenes"]}
    for sc in doc["scenes"]:
        old = pv.get(sc["scene"], {})
        for row in sc["rows"]:
            v = row["variant"]
            if not v.startswith("d") or v not in old:
                continue
            o = old[v]
            print(f"| {sc['scene']} | `{v}` | {o['rate']:.2f}× | {row['rate']:.2f}× | "
                  f"{o['drop_pp']:+.2f} | {row['drop_pp']:+.2f} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--prev", default=None)
    ap.add_argument("--rates", default="5,7,9,12")
    args = ap.parse_args()
    doc = _load(args.json)
    prev = _load(args.prev) if args.prev and os.path.exists(args.prev) else None
    rates = [float(x) for x in args.rates.split(",") if x.strip()]
    E1_KEYS = ("5.0", "7.0", "9.0", "12.0")
    print(f"# {os.path.basename(args.json)}\n")
    verdicts(doc)
    for r, row in doc["summary"]["criteria"]["E1_universal_dominance"]["per_rate"].items():
        if row.get("n_scenes"):
            print(f"E1 {r}×: mean {row['mean_pp']:+.2f} pp, min {row['min_scene_pp']:+.2f} pp, "
                  f"{row['n_positive']}/{row['n_scenes']} 同向")
    e1_table(doc, E1_KEYS)
    fidelity_table(doc, E1_KEYS)
    e3_table(doc)
    e2 = doc["summary"]["criteria"]["E2_degree_vs_bits"]
    print(f"\nE2: winner={e2.get('winner')} mean={e2.get('mean_pp'):+.3f} pp "
          f"agree={e2.get('n_agree')}/{e2.get('n_scenes')}")
    shift_table(doc, prev)


if __name__ == "__main__":
    main()
