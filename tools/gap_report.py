"""How far behind the published frontier are we, in dB at matched bytes and in bytes at matched PSNR?

The number has been quoted three ways in conversation (2.5 dB, "4x", "70x"); this script makes it one number,
computed the way a compression paper computes it, from measured points only:

  * our points are the Pareto front of the shipping container on each scene, each with the round it came from;
  * the published points are HAC/PCGS/3DGS as transcribed in `published_3dgs.json`;
  * our PSNR at a published file size comes from **linear interpolation between adjacent measured points**, and is
    refused (reported as `no row`) when the size falls outside our measured range — no extrapolation;
  * the rate at a published PSNR is only reported when our curve reaches it, otherwise `unreachable`.

The 0.55 dB protocol bias M16 measured is reported next to every gap and never folded in silently.

    python3 tools/gap_report.py                 # table on stdout
    python3 tools/gap_report.py --md out.md     # plus a markdown report
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path = None

#: Measured Pareto rows: (MB, PSNR, where it comes from).  MB is decimal, as the container writes it.
OURS = {
    "bicycle": [
        (7.24, 19.02, "M39 p10-b"),
        (10.82, 20.12, "M39 p15-b"),
        (18.35, 21.94, "M49 b32"),
        (19.47, 22.63, "M49 b40"),
        (20.56, 22.87, "M49 b48"),
        (22.91, 23.01, "M49 b64"),
        (30.78, 23.04, "M49 b96"),
        (74.80, 23.95, "M51 opacity-4"),
        (76.60, 24.06, "M51 control"),
        (1447.10, 24.52, "uncompressed published model (M16)"),
    ],
    "stump": [
        (15.12, 23.52, "M48 saliency 32-bit"),
        (16.98, 24.27, "M48 saliency 48-bit"),
        (62.65, 25.52, "M51 control"),
        (1170.98, 26.15, "uncompressed published model (M16)"),
    ],
}

PROTOCOL_BIAS_DB = 0.55  # M16, measured on bicycle and stump
MAX_SPAN = 1.5  # a segment wider than this is not interpolated, it is a different operating point


def pareto(points):
    """Keep only points that no other point beats on both axes."""
    out = []
    for p in points:
        mb, psnr = p[0], p[1]
        dominated = any((q[0] <= mb and q[1] >= psnr and (q[0] < mb or q[1] > psnr)) for q in points)
        if not dominated:
            out.append(p)
    return sorted(out)


def psnr_at(points, mb):
    """Linear interpolation in (MB, PSNR) between adjacent measured rows.

    Refused outside the measured range and refused across a segment that spans more than MAX_SPAN in size:
    interpolating between a 76 MB row and the 1447 MB uncompressed model would invent a point the pipeline never
    produced (the "3DGS row" that appeared at +0.63 dB before this guard).
    """
    pts = pareto(points)
    if not pts or mb < pts[0][0] or mb > pts[-1][0]:
        return None
    for (m0, p0, _), (m1, p1, _) in zip(pts, pts[1:]):
        if m0 <= mb <= m1:
            if m1 == m0:
                return p1
            if m1 / m0 > MAX_SPAN:
                return None
            t = (mb - m0) / (m1 - m0)
            return p0 + t * (p1 - p0)
    return None


def rate_at(points, psnr):
    """Bytes needed to reach `psnr`, or None when our curve never gets there (or only via a huge segment)."""
    pts = pareto(points)
    if not pts or psnr > pts[-1][1]:
        return None
    for (m0, p0, _), (m1, p1, _) in zip(pts, pts[1:]):
        if p0 <= psnr <= p1:
            if m1 / m0 > MAX_SPAN:
                return None
            t = 0.0 if p1 == p0 else (psnr - p0) / (p1 - p0)
            return m0 + t * (m1 - m0)
    return None




def psnr_span(points, mb):
    """Like `psnr_at`, but also returns the size ratio of the bracketing segment (None when out of range).

    A wide segment does not become a measurement by being interpolated; the report marks it instead of hiding it.
    """
    pts = pareto(points)
    if not pts or mb < pts[0][0] or mb > pts[-1][0]:
        return None, None
    for (m0, p0, _), (m1, p1, _) in zip(pts, pts[1:]):
        if m0 <= mb <= m1:
            if m1 == m0:
                return p1, 1.0
            t = (mb - m0) / (m1 - m0)
            return p0 + t * (p1 - p0), m1 / m0
    return None, None

def build_report() -> dict:
    pub = json.loads((ROOT / "experiments/published_3dgs.json").read_text(encoding="utf-8"))["methods"]
    rows = []
    for scene, ours in OURS.items():
        for method in ("3dgs", "hac", "pcgs"):
            if method not in pub or scene not in pub[method]:
                continue
            e = pub[method][scene]
            their_mb, their_psnr = float(e["mb"]), float(e["psnr"])
            our_psnr, span = psnr_span(ours, their_mb)
            our_rate = rate_at(ours, their_psnr)
            rows.append({
                "scene": scene, "method": method.upper(), "their_mb": their_mb, "their_psnr": their_psnr,
                "our_psnr_at_their_size": our_psnr,
                "span": span,
                "wide": bool(span is not None and span > MAX_SPAN),
                "gap_db": None if our_psnr is None else round(their_psnr - our_psnr, 2),
                "our_rate_at_their_psnr": our_rate,
                "rate_ratio": None if our_rate is None else round(our_rate / their_mb, 1),
            })
    return {"rows": rows, "bias_db": PROTOCOL_BIAS_DB}


def render_md(rep: dict) -> str:
    lines = ["# Gap to the published frontier, computed from measured points", "",
             "Our rows are the Pareto front of the shipping container (see `OURS` in `tools/gap_report.py` for the",
             "round each point comes from); published rows are the transcribed paper numbers. Interpolation is linear",
             "between adjacent measured points and is refused outside our measured range. The M16 protocol bias",
             f"({rep['bias_db']} dB, our renders read low) is stated, not folded in.", "",
             "| scene | method | their MB | their PSNR | our PSNR @their MB | gap (dB) | gap, bias-corrected | our MB @their PSNR | rate ratio |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        our = "no row" if r["our_psnr_at_their_size"] is None else (
            f"{r['our_psnr_at_their_size']:.2f}" + ("*" if r.get("wide") else ""))
        gap = "n/a" if r["gap_db"] is None else f"**{r['gap_db']:+.2f}**"
        corr = "n/a" if r["gap_db"] is None else f"{r['gap_db'] - rep['bias_db']:+.2f}"
        rate = "unreachable" if r["our_rate_at_their_psnr"] is None else f"{r['our_rate_at_their_psnr']:.1f}"
        ratio = "n/a" if r["rate_ratio"] is None else f"{r['rate_ratio']}x"
        lines.append(f"| {r['scene']} | {r['method']} | {r['their_mb']:.2f} | {r['their_psnr']:.2f} | {our} | {gap} | "
                     f"{corr} | {rate} | {ratio} |")
    best = {}
    for scene, pts in OURS.items():
        top = max(pts, key=lambda p: p[1])
        best[scene] = top
    if any(r.get("wide") for r in rep["rows"]):
        lines += ["", "* interpolated across a segment wider than " + str(MAX_SPAN) + "x in file size - indicative, not a",
                  "measurement. The measured rows bracketing it are listed in `OURS`."]
    lines += ["", "## Reading", ""]
    for scene, (mb, psnr, src) in best.items():
        lines.append(f"* **{scene}**: our curve tops out at **{psnr:.2f} dB / {mb:.2f} MB** ({src}). "
                     f"Every published method on this scene is above that PSNR, so the rate at matched quality is "
                     f"*undefined*, not large: they reach a quality we never reach at any size.")
    lines += ["", "At matched bytes the gap is +2.0 to +2.7 dB raw, +1.5 to +2.2 dB after the protocol bias. The `unreachable` "
              "column is literal on the raw scale; correcting the bias does not create a row either, it just moves the ",
              "statement to `our uncompressed model (1447.1 MB / 24.52 dB, i.e. 25.07 corrected) is the published quality, ",
              "at 76x the bytes`. Both forms belong in the paper; neither is an interpolation."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md")
    a = ap.parse_args()
    rep = build_report()
    print(render_md(rep))
    if a.md:
        Path(a.md).write_text(render_md(rep), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
