"""Place our measured variants on the published axes: absolute size (MB), PSNR, SSIM, LPIPS.

Papers report a model size in MB and a fidelity number per scene, so a comparison table has to
start from the same units.  Everything here comes from artifacts we already have:

* ``--bytes``  a measured-bytes json (``m*_bytes.json``): scene -> n_primitives.
  Absolute size = ``bytes_per_prim * n_primitives``; that is the shipped file, not a model.
* ``--rd``     an analysed rd json (``m*_rd.json``): per variant ``bytes_per_prim``, ``psnr``,
  ``ssim``, ``lpips``.  Rows with ``bytes_per_prim is None`` are skipped (analytic rows).

Usage::

    python experiments/cmp_points.py --bytes experiments/artifacts/a4/m15_bytes.json \
        --rd experiments/artifacts/a4/m5_rd_v2.json

    # one line per (scene, budget): the cheapest member within the budget
    python experiments/cmp_points.py --bytes ... --rd ... --budgets 2,5,9,12,20
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: fp32 bytes per primitive for an INRIA PLY at SH degree 3:
#: 3 means + 3 scales + 4 quats + 1 opacity + 3 sh0 + 45 shN, all float32.
FP32_B_PER_PRIM = 236.0


def load_sizes(path: str) -> dict:
    """scene -> (n_primitives, {variant: bytes_per_prim}) from a measured-bytes json."""
    d = json.load(open(path, encoding="utf-8"))
    out = {}
    for s in d["scenes"]:
        prims = {}
        for r in s["rows"]:
            bpp = r.get("zstd_morton_bytes_per_prim")
            if bpp is None:
                bpp = r.get("packed_bytes_per_prim")
            prims[r["spec"]] = float(bpp)
        out[s["scene"]] = (int(s["n"]), prims)
    return out


def collect(bytes_json: str, rd_json: str) -> list:
    """One record per (scene, variant) with absolute size and fidelity.

    ``bytes_per_prim`` in an rd json is per *stored* primitive, so for a prune row it is the
    fp32 size of the survivors and the file size needs the keep fraction.  ``rate`` is already
    the total-file ratio (``fp32_bytes_per_prim / (bytes_per_prim * keep)``), so the absolute
    size comes from ``rate`` and is independent of that bookkeeping::

        MB = 236 B/prim * n_primitives / rate / 1e6
    """
    sizes = load_sizes(bytes_json)
    rd = json.load(open(rd_json, encoding="utf-8"))
    rows = []
    for sc in rd["scenes"]:
        name = sc["scene"]
        if name not in sizes:
            continue
        n, per = sizes[name]
        seen_clean = False
        for r in sc["rows"]:
            bpp = r.get("bytes_per_prim")
            rate = r.get("rate")
            if r["variant"] == "clean":
                # The clean row needs no byte measurement: it *is* the PLY, so its size is
                # n * 236 B and its rate is 1.0.  Same convention as the published tables,
                # whose "Size (MB)" column is the PLY file.
                rows.append({
                    "scene": name, "variant": "clean", "family": "clean", "n": n,
                    "mb": FP32_B_PER_PRIM * n / 1e6, "bytes_per_prim": FP32_B_PER_PRIM,
                    "rate": 1.0, "psnr": r.get("psnr"), "ssim": r.get("ssim"),
                    "lpips": r.get("lpips"), "drop_pp": r.get("drop_pp"),
                })
                seen_clean = True
                continue
            if bpp is None or not rate:
                continue
            mb = FP32_B_PER_PRIM * n / (float(rate) * 1e6)
            rows.append({
                "scene": name,
                "variant": r["variant"],
                "family": r.get("family"),
                "n": n,
                "mb": mb,
                "bytes_per_prim": float(bpp),
                "rate": float(rate),
                "psnr": r.get("psnr"),
                "ssim": r.get("ssim"),
                "lpips": r.get("lpips"),
                "drop_pp": r.get("drop_pp"),
            })
        if not seen_clean and sc.get("clean_psnr") is not None:
            # m1_analyse keeps the clean render at scene level (it is the reference, not a
            # row), so the reference point has to be reconstructed here.
            rows.append({
                "scene": name, "variant": "clean", "family": "clean", "n": n,
                "mb": FP32_B_PER_PRIM * n / 1e6, "bytes_per_prim": FP32_B_PER_PRIM,
                "rate": 1.0, "psnr": sc.get("clean_psnr"),
                "ssim": sc.get("clean_ssim"), "lpips": sc.get("clean_lpips"),
                "drop_pp": 0.0,
            })
    return rows


def best_within(rows: list, budgets) -> list:
    """Per (scene, budget): the member with the smallest drop_pp under ``budget`` x.

    This is the M13 reading -- measured points only, no interpolation, and the byte
    axis is ours (``rate`` = 236 B / bytes_per_prim), not the budget itself.
    """
    out = []
    for budget in budgets:
        for scene in sorted({r["scene"] for r in rows}):
            cand = [r for r in rows if r["scene"] == scene
                    and r["rate"] is not None and r["rate"] <= budget * 1.05]
            if not cand:
                out.append({"scene": scene, "budget": budget, "variant": None})
                continue
            pick = min(cand, key=lambda r: (r["drop_pp"] if r["drop_pp"] is not None else 9e9))
            out.append({"scene": scene, "budget": budget, **{k: pick[k] for k in
                        ("variant", "family", "mb", "rate", "psnr", "ssim", "lpips", "drop_pp", "n")}})
    return out


def _fmt(v, nd: int) -> str:
    """Format with a dash for None.  Kept as a function because the node runs Python 3.11,
    which does not allow an f-string nested inside another with the same quote character."""
    return "-" if v is None else f"{v:.{nd}f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bytes", default="experiments/artifacts/a4/m15_bytes.json")
    ap.add_argument("--rd", default="experiments/artifacts/a4/m5_rd_v2.json")
    ap.add_argument("--budgets", default="")
    ap.add_argument("--variants", default="")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    rows = collect(args.bytes, args.rd)
    if args.budgets:
        budgets = [float(x) for x in args.budgets.split(",") if x.strip()]
        sel = best_within(rows, budgets)
        print("| scene | budget | variant | MB | rate | PSNR | SSIM | LPIPS | drop pp |")
        print("|---|---|---|---|---|---|---|---|---|")
        for r in sel:
            if r["variant"] is None:
                print(f"| {r['scene']} | {r['budget']:.2f}x | - | - | - | - | - | - | - |")
                continue
            print(f"| {r['scene']} | {r['budget']:.2f}x | `{r['variant']}` | {r['mb']:.1f} | "
                  f"{r['rate']:.2f}x | {r['psnr']:.2f} | "
                  f"{_fmt(r['ssim'], 3)} | {_fmt(r['lpips'], 4)} | {r['drop_pp']:+.2f} |")
    else:
        want = [v.strip() for v in args.variants.split(",") if v.strip()] or None
        print("| scene | variant | MB | rate | PSNR | SSIM | LPIPS | drop pp |")
        print("|---|---|---|---|---|---|---|---|")
        for r in rows:
            if want and r["variant"] not in want:
                continue
            print(f"| {r['scene']} | `{r['variant']}` | {r['mb']:.1f} | {r['rate']:.2f}x | "
                  f"{r['psnr']:.2f} | {_fmt(r['ssim'], 3)} | {_fmt(r['lpips'], 4)} | "
                  f"{r['drop_pp']:+.2f} |")
    if args.json:
        json.dump(rows, open(args.json, "w", encoding="utf-8"), indent=1)
        print(f"\nWROTE {args.json} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
