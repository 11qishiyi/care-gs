#!/usr/bin/env python3
"""Render ``m1_rd.json`` as the markdown tables that go into M1_RESULTS.md.

The analysis file is the single source of truth; this script only reshapes it, so
no number here is computed twice.  Everything is read-only.

    python experiments/m1_report.py --json /workspace/res/m1/m1_rd.json
    python experiments/m1_report.py --json ... --rates 2,3,5,7,9 --out report.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def _fmt(x, nd=2, dash="—"):
    if x is None:
        return dash
    if isinstance(x, str):
        return x
    return f"{x:+.{nd}f}" if nd and isinstance(x, float) else f"{x:.{nd}f}"


def _cell(entry, key="drop_pp", nd=2):
    if not entry:
        return "—"
    v = entry.get(key)
    if v is None:
        return "—"
    s = f"{v:.{nd}f}"
    if entry.get("covered") is False:
        s += "\\*"
    return s


def free_factor(rows, max_drop=1.0, max_dpsnr=0.15):
    """Largest compression ratio whose coverage loss and PSNR drop stay in budget.

    This is the headline number of the round: how far a checkpoint can be shrunk
    while the certificate (almost) does not notice.  Both budgets are checked
    against the member's own measured values, never against an interpolation.
    """
    best = None
    for r in rows:
        if r.get("rate") is None or r.get("drop_pp") is None:
            continue
        if r.get("d_psnr") is None:
            continue
        if r["drop_pp"] >= -max_drop and r["d_psnr"] <= max_dpsnr:
            if best is None or r["rate"] > best["rate"]:
                best = r
    return best


def md_report(res, rates):
    scenes = res["scenes"]
    out = []
    A = out.append

    crit = res["summary"]["criteria"]
    A(f"### Verdict ({res['summary']['outcome']})\n")
    for name, c in crit.items():
        st = "PASS" if c.get("verdict") else "FAIL"
        A(f"- **{name}** — {st}")
        for k, v in (c.get("rates") or {}).items():
            A(f"  - {k}×: {v}")
    A("")

    # 1) matched-byte coverage: QFP vs prune vs joint
    hdr = "| asset | clean cov | " + " | ".join(f"{r}× QFP | {r}× prune | Δ" for r in rates) + " |"
    A(hdr)
    A("|" + "---|" * (2 + 3 * len(rates)))
    for sc in scenes:
        line = [f"{sc['scene']}", f"{100 * sc['clean_coverage']:.1f}%"]
        for r in rates:
            m = (sc.get("matched") or {}).get(str(r)) or {}
            cmp_ = (sc.get("comparisons") or {}).get(str(r)) or {}
            q, p = m.get("qfp"), m.get("prune")
            d = (cmp_.get("coverage") or {}).get("mean_pp")
            line += [_cell(q), _cell(p), "—" if d is None else f"{d:+.2f}"]
        A("| " + " | ".join(line) + " |")
    A("\n*Δ = QFP minus prune (positive is better for QFP); `*` marks an extrapolated "
      "value, which the criteria refuse to use.*\n")

    # 2) fidelity at matched bytes
    A("| asset | rate | QFP PSNR | prune PSNR | ΔPSNR | QFP SSIM | prune SSIM | QFP LPIPS | prune LPIPS |")
    A("|---|---|---|---|---|---|---|---|---|")
    for sc in scenes:
        for r in rates:
            cmp_ = (sc.get("comparisons") or {}).get(str(r)) or {}
            if not cmp_:
                continue
            f = {k: cmp_.get(k) for k in ("psnr", "ssim", "lpips")}
            A(f"| {sc['scene']} | {r}× | {_fmt((f['psnr'] or {}).get('qfp'), 3)} | "
              f"{_fmt((f['psnr'] or {}).get('prune'), 3)} | {_fmt((f['psnr'] or {}).get('diff'), 3)} | "
              f"{_fmt((f['ssim'] or {}).get('qfp'), 4)} | {_fmt((f['ssim'] or {}).get('prune'), 4)} | "
              f"{_fmt((f['lpips'] or {}).get('qfp'), 4)} | {_fmt((f['lpips'] or {}).get('prune'), 4)} |")
    A("")

    # 3) byte model per variant (identical across scenes)
    if scenes:
        A("| variant | family | bytes/prim | rate vs fp32 | coverage loss (pp) | PSNR loss (dB) |")
        A("|---|---|---|---|---|---|")
        for row in sorted(scenes[0]["rows"], key=lambda r: (r["family"], r.get("rate") or 0)):
            bpp = "-" if row["bytes_per_prim"] is None else "%.2f" % row["bytes_per_prim"]
            rate = "-" if row["rate"] is None else "%.2fx" % row["rate"]
            A("| `%s` | %s | %s | %s | %.2f | %s |" % (row["variant"], row["family"], bpp, rate,
                                                 row["drop_pp"], _fmt(row["d_psnr"], 3)))
        A("\n*Both diagnostic columns are losses relative to the unmodified checkpoint of "
          "scene `%s`: negative coverage and positive PSNR loss are both worse.*\n"
          % scenes[0]["scene"])

    # 4) free-compression shelf per asset
    A("| asset | free factor (≤1.0 pp, ≤0.15 dB) | at bytes/prim | variant |")
    A("|---|---|---|---|")
    for sc in scenes:
        b = free_factor(sc["rows"])
        if b is None:
            A(f"| {sc['scene']} | none | — | — |")
        else:
            A(f"| {sc['scene']} | {b['rate']:.2f}× | {b['bytes_per_prim']:.2f} | `{b['variant']}` |")
    A("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True, help="m1_rd.json written by m1_analyse.py")
    ap.add_argument("--rates", default=None, help="comma list, default: the file's own rates")
    ap.add_argument("--out", default=None, help="write markdown here instead of stdout")
    args = ap.parse_args(argv)

    with open(args.json, encoding="utf-8") as fh:
        res = json.load(fh)
    if args.rates:
        rates = [float(x) for x in args.rates.split(",")]
    else:
        rates = sorted({float(r) for sc in res["scenes"]
                        for r in (sc.get("comparisons") or {})}) or [2.0, 3.0, 5.0]
    md = md_report(res, rates)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md + "\n")
        print(f"wrote {args.out} ({len(md)} chars)")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
