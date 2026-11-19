"""Bjontegaard delta-rate / delta-PSNR between two measured rate-distortion curves.

Compression papers report BD-rate, not a single point per arm, so the same-model baseline table needs this.  The
implementation is the standard one, done the simplest defensible way: piecewise-linear interpolation of PSNR against
log10(bytes) on the overlap of the two curves' quality ranges, then integrate the rate difference and divide by the
reference's mean rate.

    python3 tools/bd_rate.py --ref rows_control.txt --test rows.csv --out table.md
    python3 tools/bd_rate.py --selftest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def parse_rows(path: Path) -> list[dict]:
    """Rows are `arm budget bytes psnr [ssim] [lpips]`, one per line; comments and blanks are ignored."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) < 4:
            continue
        try:
            rows.append({"arm": p[0], "budget": p[1], "bytes": float(p[2]), "psnr": float(p[3]),
                         "ssim": float(p[4]) if len(p) > 4 and p[4] != "NA" else None,
                         "lpips": float(p[5]) if len(p) > 5 and p[5] != "NA" else None})
        except ValueError:
            continue
    return rows


def curve(rows: list[dict], arm: str):
    """(psnr ascending, log10 bytes) for one arm, sorted by quality."""
    pts = [(r["psnr"], np.log10(r["bytes"])) for r in rows if r["arm"] == arm]
    pts.sort()
    if len(pts) < 2:
        return None
    psnr = np.array([p[0] for p in pts])
    logr = np.array([p[1] for p in pts])
    return psnr, logr


def bd_rate(ref, test) -> tuple[float, float] | None:
    """(BD-rate %, BD-PSNR dB) of `test` against `ref`, over the overlapping PSNR range.

    Negative BD-rate means the test curve needs fewer bytes for the same quality (better).
    """
    if ref is None or test is None:
        return None
    rp, rl = ref
    tp, tl = test
    lo = max(rp.min(), tp.min())
    hi = min(rp.max(), tp.max())
    if not (hi > lo):
        return None
    grid = np.linspace(lo, hi, 200)
    r_rate = np.interp(grid, rp, rl)
    t_rate = np.interp(grid, tp, tl)
    mean_ref = r_rate.mean()
    bd = float((10 ** (t_rate - r_rate) - 1.0).mean() * 100.0)   # exponential of the mean log-ratio
    # BD-PSNR: average PSNR gap at equal log-rate, over the overlapping rate range
    rlo = max(rl.min(), tl.min())
    rhi = min(rl.max(), tl.max())
    if rhi > rlo:
        rgrid = np.linspace(rlo, rhi, 200)
        bd_psnr = float(np.interp(rgrid, tl, tp).mean() - np.interp(rgrid, rl, rp).mean())
    else:
        bd_psnr = float("nan")
    return bd, bd_psnr


def _selftest() -> int:
    # a curve shifted by a constant factor in rate must come out at that factor
    base = [(20.0, 1e6), (22.0, 2e6), (24.0, 4e6), (26.0, 8e6)]
    ref = (np.array([p[0] for p in base]), np.log10(np.array([p[1] for p in base])))
    same = bd_rate(ref, ref)
    assert abs(same[0]) < 1e-9, same
    half = (ref[0], ref[1] - np.log10(2.0))
    bd, _ = bd_rate(ref, half)
    assert abs(bd + 50.0) < 1e-6, bd
    worse = (ref[0], ref[1] + np.log10(1.25))
    bd2, _ = bd_rate(ref, worse)
    assert abs(bd2 - 25.0) < 1e-6, bd2
    print("bd_rate selftest: OK (identity, -50 %, +25 %)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", help="rows file containing the reference arm")
    ap.add_argument("--ref-arm", default="control")
    ap.add_argument("--test", help="rows file with the arms to compare")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not (a.ref and a.test):
        return _selftest()
    ref_rows = parse_rows(Path(a.ref))
    test_rows = parse_rows(Path(a.test))
    ref = curve(ref_rows, a.ref_arm)
    if ref is None:
        print(f"no usable reference curve for arm {a.ref_arm}", file=sys.stderr)
        return 2
    arms = sorted({r["arm"] for r in test_rows})
    lines = ["| arm | BD-rate vs control | BD-PSNR (dB) | points |", "|---|---|---|---|"]
    for arm in arms:
        res = bd_rate(ref, curve(test_rows, arm))
        n = sum(1 for r in test_rows if r["arm"] == arm)
        if res is None:
            lines.append(f"| {arm} | n/a (no overlap) | n/a | {n} |")
        else:
            lines.append(f"| {arm} | **{res[0]:+.2f} %** | {res[1]:+.2f} | {n} |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
