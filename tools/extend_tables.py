"""Turn the extension runs into paper-ready LaTeX rows (CPU, no GPU).

Inputs: the per-scene `region_<scene>.json` files written on the GPU node by
`experiments/region_coverage.py` (pixel + 64x64 block, 400 splits, archive-GT
convention), for ten scene entries:

    bicycle flowers stump treehill            (published 40k checkpoints)
    *_i7k                                     (same scenes, iteration_7000)
    bonsai bonsai_i7k                          (fifth asset, 30k / 7k)

Outputs (stdout + `results_v110/extend_tables.json`):
  1. a self-check that the four published 30%-prune degradations reproduce the
     numbers in the paper (bicycle -22.1, flowers -10.8, stump -27.7, treehill -15.2);
  2. `T_bitdepth`: SH quantisation at 8/6/4 bits, per asset;
  3. `T_depth`: 40k vs 7k checkpoints of the same scene, 30% prune;
  4. `T_bonsai`: the fifth asset, 50%/30% prune and quant8.

Usage:
    python tools/extend_tables.py --json-dir results_v110/region --out results_v110/extend_tables.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

PUB = {"bicycle": 22.1, "flowers": 10.8, "stump": 27.7, "treehill": 15.2}
SCENES40 = ["bicycle", "flowers", "stump", "treehill"]


def load(json_dir: str) -> dict:
    """scene -> {(variant, gran): row}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(json_dir, "region_*.json"))):
        blob = json.load(open(f, encoding="utf-8"))
        rows = blob["rows"] if isinstance(blob, dict) and "rows" in blob else blob
        for r in rows:
            scene = r.get("scene")
            if not scene:
                continue
            out.setdefault(scene, {})[(r.get("variant"), r.get("gran") or r.get("granularity"))] = r
    return out


def row(data: dict, scene: str, variant: str, gran: str = "pixel"):
    return data.get(scene, {}).get((variant, gran))


def fmt(r, digits: int = 1) -> str:
    if r is None or r.get("degradation_pp") is None:
        return "--"
    d = r["degradation_pp"]
    lo = r.get("drop_hi")   # drop is negative when coverage falls: hi = shallower
    hi = r.get("drop_lo")
    if lo is None or hi is None:
        return f"{d:.{digits}f}"
    return f"{d:.{digits}f}\\,[{100 * hi:.{digits}f},{100 * lo:.{digits}f}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="results_v110/region")
    ap.add_argument("--out", default="results_v110/extend_tables.json")
    args = ap.parse_args()

    data = load(args.json_dir)
    if not data:
        print(f"no region_*.json under {args.json_dir}", file=sys.stderr)
        return 2

    print(f"loaded {len(data)} scenes: {', '.join(sorted(data))}\n")

    # --- 1. reproduction check against the published table -------------------
    print("== reproduction of the published 30 % prune (pixel, degradation in pp)")
    ok = True
    for s in SCENES40:
        r = row(data, s, "prune30")
        got = None if r is None else r.get("degradation_pp")
        exp = PUB[s]
        flag = "OK " if got is not None and abs(got - exp) <= 0.15 else "DIFF"
        if flag != "OK ":
            ok = False
        print(f"  {flag} {s:10s} got {got if got is None else round(got, 2):>7}  paper {exp:>6}")
    print(f"  => {'all four reproduce' if ok else 'MISMATCH: do not integrate before checking the dump'}\n")

    # --- 2. bit depth --------------------------------------------------------
    print("== SH quantisation: degradation pp at 8 / 6 / 4 bits (pixel; 64x64 in brackets)")
    bit = {}
    for s in SCENES40:
        rowout = {}
        cells = []
        for v in ("quant8", "quant6", "quant4"):
            px, blk = row(data, s, v), row(data, s, v, "block64")
            rowout[v] = dict(pixel=fmt(px), block=fmt(blk))
            cells.append(f"{fmt(px)} ({fmt(blk)})")
        bit[s] = rowout
        print(f"  {s:10s} " + "  ".join(cells))

    # --- 3. optimisation depth ----------------------------------------------
    print("\n== optimisation depth: 30 % prune drop at 40k vs 7k (pixel [2.5,97.5])")
    depth = {}
    for s in SCENES40:
        a, b = row(data, s, "prune30"), row(data, s + "_i7k", "prune30")
        depth[s] = dict(k40=fmt(a), k7=fmt(b))
        print(f"  {s:10s} 40k {fmt(a):>18s}   7k {fmt(b):>18s}")

    # --- 4. fifth asset ------------------------------------------------------
    print("\n== fifth asset (bonsai): degradation pp")
    bonsai = {}
    for s in ("bonsai", "bonsai_i7k"):
        if s not in data:
            print(f"  {s}: missing")
            continue
        d = {}
        for v in ("prune50", "prune30", "quant8", "quant4"):
            d[v] = dict(pixel=fmt(row(data, s, v)), block=fmt(row(data, s, v, "block64")))
            print(f"  {s:12s} {v:8s} pixel {fmt(row(data, s, v)):>18s}  block {fmt(row(data, s, v, 'block64')):>18s}")
        bonsai[s] = d

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(dict(published_reproduction=ok, bitdepth=bit, depth=depth, bonsai=bonsai),
              open(args.out, "w", encoding="utf-8"), indent=1)
    print(f"\nwrote {args.out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
