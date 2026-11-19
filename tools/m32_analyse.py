"""M32 -- the verdict: is the colour residual rank, bits, or neither, and can the choice be made offline?

Reads the three json/log files the round produced (`m32_sizes.json`, `coef_<scene>.json`,
`render_<scene>.log`) and prints:

* the per-scene table of every plan (bytes, B/primitive, ratio, PSNR, delta vs the shipping point);
* J1/J2 (does any iso-byte plan recover 0.3 dB on bonsai; does the rate control do it);
* J4 (does the coefficient error rank plans the way the render does -- Spearman per scene);
* the branch the spec defines.

    python tools/m32_analyse.py --root experiments/artifacts/a4/m32
"""

from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import re

SCENES = ("bicycle", "stump", "bonsai")
CLEAN_DB = {"bicycle": 24.52, "stump": 26.15, "bonsai": 28.06}
PAYLOAD_MB = {"bicycle": 1447.1, "stump": 1170.98, "bonsai": 293.78}
SHIPPING = "r16_b48"


def spearman(a, b) -> float:
    """Rank correlation without scipy: average ranks, then Pearson on the ranks."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    ra, rb = ranks(a), ranks(b)
    n = len(ra)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=os.path.join("experiments", "artifacts", "a4", "m32"))
    a = ap.parse_args()

    sizes_path = os.path.join(a.root, "m32_sizes.json")
    if not os.path.exists(sizes_path):
        print(f"missing {sizes_path}")
        return 2
    sizes = json.load(open(sizes_path, encoding="utf-8"))

    tables = {}
    for scene in SCENES:
        e = sizes.get(scene)
        if not e:
            continue
        coef_path = os.path.join(a.root, f"coef2_{scene}.json")
        if not os.path.exists(coef_path):
            coef_path = os.path.join(a.root, f"coef_{scene}.json")
        coef, coef_naive = {}, {}
        if os.path.exists(coef_path):
            for r in json.load(open(coef_path, encoding="utf-8")):
                coef[r["plan"]] = r["rel_rmse_full"] if "rel_rmse_full" in r else r["rel_rmse"]
                coef_naive[r["plan"]] = r["rel_rmse"]
        rows = []
        base_bytes = e["containers"].get(SHIPPING)
        for plan, nbytes in sorted(e["containers"].items()):
            psnr = e["psnr"].get(plan)
            rows.append({"plan": plan, "mb": nbytes / 1e6,
                         "ratio": PAYLOAD_MB[scene] / (nbytes / 1e6),
                         "psnr": psnr,
                         "delta_vs_ship": (psnr - e["psnr"][SHIPPING]) if psnr and SHIPPING in e["psnr"] else None,
                         "rel_bytes": (nbytes / base_bytes - 1.0) if base_bytes else None,
                         "coef": coef.get(plan), "coef_naive": coef_naive.get(plan)})
        tables[scene] = rows

        print(f"\n== {scene}  (clean {CLEAN_DB[scene]:.2f} dB, shipping file {base_bytes/1e6:.2f} MB) ==")
        print("| plan | file | ratio | PSNR | delta vs ship | bytes vs ship | coef err (full) | "
              "coef err (in subspace) |")
        print("|---|---|---|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['plan']} | {r['mb']:.2f} MB | {r['ratio']:.2f}x | "
                  f"{r['psnr'] if r['psnr'] is not None else '--'} | "
                  f"{('%+.2f' % r['delta_vs_ship']) if r['delta_vs_ship'] is not None else '--'} | "
                  f"{('%+.1f%%' % (100*r['rel_bytes'])) if r['rel_bytes'] is not None else '--'} | "
                  f"{('%.2f%%' % (100*r['coef'])) if r['coef'] is not None else '--'} | "
                  f"{('%.2f%%' % (100*r['coef_naive'])) if r['coef_naive'] is not None else '--'} |")

        #: J4: does coefficient error rank plans the way the render does?  (lower error == higher PSNR)
        both = [(r["coef"], r["psnr"]) for r in rows if r["coef"] is not None and r["psnr"] is not None]
        if len(both) >= 3:
            err = [b[0] for b in both]
            ps = [b[1] for b in both]
            print(f"   J4 Spearman(coef error full, PSNR) = {spearman(err, ps):+.3f}  (want -1.000)")
        naive = [(r["coef_naive"], r["psnr"]) for r in rows
                 if r["coef_naive"] is not None and r["psnr"] is not None]
        if len(naive) >= 3:
            print(f"   J4 Spearman(in-subspace error, PSNR) = "
                  f"{spearman([n[0] for n in naive], [n[1] for n in naive]):+.3f}  (the naive metric)")

    # J1 / J2 on bonsai
    print("\n== verdict ==")
    if "bonsai" in tables:
        rows = tables["bonsai"]
        ship = next((r for r in rows if r["plan"] == SHIPPING), None)
        iso = [r for r in rows if r["plan"] != SHIPPING and r["rel_bytes"] is not None
               and r["rel_bytes"] <= 0.05 and r["delta_vs_ship"] is not None]
        best_iso = max(iso, key=lambda r: r["delta_vs_ship"]) if iso else None
        rate = next((r for r in rows if r["plan"] == "r16_b64"), None)
        print(f"shipping bonsai PSNR {ship['psnr'] if ship else '--'}")
        if best_iso:
            print(f"best iso-byte plan {best_iso['plan']}: {best_iso['delta_vs_ship']:+.2f} dB "
                  f"at {100*best_iso['rel_bytes']:+.1f}% bytes")
        if rate and ship:
            print(f"rate control r16_b64: {rate['delta_vs_ship']:+.2f} dB at "
                  f"{100*rate['rel_bytes']:+.1f}% bytes")
        j1 = bool(best_iso and best_iso["delta_vs_ship"] >= 0.30)
        j2 = bool(not j1 and rate and ship and rate["delta_vs_ship"] >= 0.30)
        branch = ("colour_residual_is_rank" if j1 else
                  "colour_residual_is_bits" if j2 else "colour_residual_is_the_basis")
        print(f"J1 {'PASS' if j1 else 'FAIL'}   J2 {'PASS' if j2 else 'FAIL'}   -> {branch}")
        for scene, rows in tables.items():
            ship = next((r for r in rows if r["plan"] == SHIPPING), None)
            if ship and ship["psnr"]:
                print(f"   {scene}: delta vs clean {ship['psnr'] - CLEAN_DB[scene]:+.2f} dB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
