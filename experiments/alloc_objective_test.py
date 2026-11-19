"""Does a coverage-aware bit allocation differ from an MSE-aware one?  (pre-test for direction B)

Direction B = allocate bits to minimise *coverage* loss at a fixed byte budget instead of minimising MSE. That is
only worth building if the two objectives price the codable fields differently. This script settles it from data we
already have (`m5_rd_v2`), before any allocator is written.

Byte convention: `rate` is the compression ratio against fp32, so bytes ~ 1/rate and
    dbytes% = 100 * (rate_base / rate_arm - 1)      (negative = the arm is smaller)
    dB/%   = |dPSNR| / |dbytes%|                   (the MSE-aware price of a field)
    pp/%   = |dcoverage loss| / |dbytes%|          (the coverage-aware price of the same field)

The pairs below hold everything fixed except one field, so the price belongs to that field.

    python experiments/alloc_objective_test.py
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np

M5 = Path("experiments/artifacts/a4/m5_rd_v2.json")
OUT = Path("experiments/artifacts/a4/alloc_objective_test.json")

# (label, arm A, arm B) with exactly one field different between A and B
PAIRS = [
    ("colour 4->3 bit", "m16_o8_sh4", "m16_o8_sh3"),
    ("colour 4->2 bit", "m16_o8_sh4", "m16_o8_sh2"),
    ("colour 8->4 bit", "m16_o8_sh8", "m16_o8_sh4"),
    ("opacity 8->6 bit", "m16_o8_sh3", "m16_o6_sh3"),
    ("positions 16->18 bit", "m16_o6_sh3", "m18_o6_sh3"),
]


def spearman(a: list[float], b: list[float]) -> float:
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean()
    rb -= rb.mean()
    den = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / den) if den else float("nan")


def main() -> None:
    grid = json.loads(M5.read_text(encoding="utf-8"))
    rows = []
    for sc in grid["scenes"]:
        by = {r["variant"]: r for r in sc["rows"]}
        for label, a_name, b_name in PAIRS:
            if a_name not in by or b_name not in by:
                continue
            a, b = by[a_name], by[b_name]          # a = reference, b = the arm that spends fewer bytes
            dbytes = 100.0 * (a["rate"] / b["rate"] - 1.0)   # negative: b is smaller than a
            if abs(dbytes) < 0.5:
                continue
            d_db = b["psnr"] - a["psnr"]
            d_loss = -(b["drop_pp"] - a["drop_pp"])          # positive: b loses more coverage
            rows.append(dict(
                scene=sc["scene"], field=label, arm=a_name, vs=b_name,
                d_bytes_pct=round(dbytes, 1), d_db=round(d_db, 3), d_loss_pp=round(d_loss, 3),
                db_per_pct=round(abs(d_db / dbytes), 4),
                pp_per_pct=round(abs(d_loss / dbytes), 4),
                db_per_pp=(round(abs(d_db / d_loss), 2) if abs(d_loss) > 1e-6 else None),
            ))

    # per scene: rank the fields by each objective and count disagreements
    verdicts = []
    for scene in sorted({r["scene"] for r in rows}):
        rs = [r for r in rows if r["scene"] == scene]
        if len(rs) < 3:
            continue
        db = [r["db_per_pct"] for r in rs]
        pp = [r["pp_per_pct"] for r in rs]
        flips = sum(1 for i, j in combinations(range(len(rs)), 2)
                    if (db[i] - db[j]) * (pp[i] - pp[j]) < 0)
        verdicts.append(dict(scene=scene, n_fields=len(rs), spearman=round(spearman(db, pp), 3),
                             pairs=int(len(list(combinations(range(len(rs)), 2)))), flips=flips,
                             cheapest_by_db=rs[int(np.argmin(db))]["field"],
                             cheapest_by_coverage=rs[int(np.argmin(pp))]["field"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"rows": rows, "verdicts": verdicts}, indent=1), encoding="utf-8")

    print(f"{'scene':12s} {'field':22s} {'dbytes%':>8s} {'d_dB':>6s} {'d_loss_pp':>9s} "
          f"{'dB/%':>7s} {'pp/%':>7s}")
    for r in rows:
        print(f"{r['scene']:12s} {r['field']:22s} {r['d_bytes_pct']:8.1f} {r['d_db']:6.2f} "
              f"{r['d_loss_pp']:9.2f} {r['db_per_pct']:7.4f} {r['pp_per_pct']:7.4f}")
    print()
    for v in verdicts:
        print(f"{v['scene']:12s} rho={v['spearman']:+.2f}  flips={v['flips']}/{v['pairs']}  "
              f"cheapest by dB: {v['cheapest_by_db']:22s} | by coverage: {v['cheapest_by_coverage']}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
