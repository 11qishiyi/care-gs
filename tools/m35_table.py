"""Assemble the M35 rate-distortion map from the round's own logs.

Reads what `experiments/run_m35.sh render` wrote (one line per ladder point:
``<spec> <bytes> <seconds> <probe_render output>``) and prints the table plus the
log-bytes -> dB fit that criterion Q1 asks for.

    python tools/m35_table.py --dir experiments/artifacts/a4/m35 [--json out.json]

The fit is a straight line in (log2 bytes, dB) fitted over the points that survive the
"drop the later of two points within 5 % in bytes" rule in ``tools/m35_spec.md``.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re

#: held-out view counts and the clean models' own PSNR, measured on this project's protocol
SCENES = {
    "bicycle": dict(prims=6131954, views=25, clean=24.52, payload=1447.1),
    "stump": dict(prims=4961797, views=16, clean=26.15, payload=1170.98),
    "bonsai": dict(prims=1244819, views=16, clean=28.06, payload=293.78),
}

#: published points this round is plotted against, quoted with their byte budgets
SOTA = [
    ("HAC", 27.54, 25.05),
    ("PCGS", 19.09, 25.12),
    ("3DGS (published model, no compression)", 1447.1, 24.52),
]

LINE = re.compile(r"^(?P<spec>\S+)\s+(?P<bytes>\d+)\s+(?P<sec>\d+)s\s+.*?"
                  r"psnr[=:\s]+(?P<psnr>\d+\.\d+)", re.IGNORECASE)


def parse_log(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = LINE.search(line)
            if not m:
                continue
            rows.append(dict(spec=m.group("spec"), bytes=int(m.group("bytes")),
                             seconds=int(m.group("sec")), psnr=float(m.group("psnr"))))
    return rows


def dedupe(rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Drop the later of two points that are within 5 % in bytes *and* within 0.05 dB.

    The first version dropped on bytes alone, which threw away the most interesting row of the round:
    `gp5-5-5_c7_sh3` (69.34 MB, 23.80 dB) and `gp6-6-6_c6_sh2` (69.30 MB, 22.82 dB) are 0.06 % apart in
    bytes and 1 dB apart in quality -- that is not a duplicate, it is a dominated point, and it is the
    finding.  Two points count as the same measurement only if they are the same in both axes.
    """
    kept, notes = [], []
    for r in sorted(rows, key=lambda r: -r["bytes"]):
        if kept and abs(r["bytes"] - kept[-1]["bytes"]) / kept[-1]["bytes"] < 0.05 \
                and abs(r["psnr"] - kept[-1]["psnr"]) < 0.05:
            notes.append(f"dropped {r['spec']} ({r['bytes']} B, {r['psnr']:.2f} dB) -- "
                         f"same bytes and same dB as {kept[-1]['spec']}")
            continue
        kept.append(r)
    #: a point is dominated when a *smaller* file already renders better
    best = -1e9
    for r in sorted(kept, key=lambda r: r["bytes"]):
        r["dominated_by"] = "" if r["psnr"] >= best else "yes"
        best = max(best, r["psnr"])
    return kept, notes


def fit(points: list[dict]) -> dict:
    """Least squares of dB on log2(bytes); returns slope, intercept, R^2 and the crossings."""
    xs = [math.log2(p["bytes"]) for p in points]
    ys = [p["psnr"] for p in points]
    n = len(xs)
    if n < 2:
        return {}
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    inter = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + inter)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    crossings = {}
    for target in (23.0, 24.0):
        if slope == 0:
            continue
        x = (target - inter) / slope
        crossings[target] = 2 ** x / 1e6 if x == x else None
    return dict(slope_db_per_bit=slope, intercept=inter, r2=r2, crossings_MB=crossings)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="experiments/artifacts/a4/m35")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    out = {"scenes": {}, "sota": [dict(name=n, MB=b, psnr=p) for n, b, p in SOTA]}
    for scene, meta in SCENES.items():
        log = os.path.join(args.dir, f"render_{scene}.log")
        if not os.path.exists(log):
            continue
        rows = parse_log(log)
        if not rows:
            print(f"{scene}: no parsed rows in {log}")
            continue
        kept, notes = dedupe(rows)
        for r in kept:
            r["MB"] = r["bytes"] / 1e6
            r["bytes_per_prim"] = r["bytes"] / meta["prims"]
            r["ratio"] = meta["payload"] * 1e6 / r["bytes"]
            r["delta_db"] = r["psnr"] - meta["clean"]
        f = fit(kept)
        out["scenes"][scene] = dict(meta=meta, points=kept, fit=f, notes=notes)

        print(f"\n## {scene} -- {meta['prims']:,} primitives, {meta['views']} views, "
              f"clean {meta['clean']:.2f} dB, payload {meta['payload']:.1f} MB\n")
        print("| spec | file | B/prim | ratio | PSNR | vs clean | dominated |")
        print("|---|---|---|---|---|---|---|")
        for r in kept:
            print(f"| `{r['spec']}` | {r['MB']:.2f} MB | {r['bytes_per_prim']:.2f} | "
                  f"{r['ratio']:.2f}x | {r['psnr']:.2f} | {r['delta_db']:+.2f} | "
                  f"{r.get('dominated_by', '')} |")
        if f:
            print(f"\nfit: {f['slope_db_per_bit']:+.3f} dB per bit of file size, R^2 = {f['r2']:.3f}")
            for t, mb in f["crossings_MB"].items():
                print(f"  crosses {t:.1f} dB at {mb:.2f} MB" if mb else f"  {t:.1f} dB not reached")
        for n in notes:
            print(f"  note: {n}")
        mono = all(kept[i]["psnr"] >= kept[i + 1]["psnr"] - 1e-9 for i in range(len(kept) - 1))
        span = (max(r["MB"] for r in kept) - min(r["MB"] for r in kept)) if kept else 0
        print(f"  Q1 on this scene: {len(kept)} points, span {span:.1f} MB, monotone {mono}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
        print("\nwrote", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
