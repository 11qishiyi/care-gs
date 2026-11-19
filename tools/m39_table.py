"""M39 -- read render.txt / m39_time.txt and judge N1-N3 against our measured frontier.

    python tools/m39_table.py --dir /workspace/res/m39 [--json out.json]

Two readings, because the pre-registered N2 text asked for interpolation:

* **Pareto** (the definition of a frontier): a new point is on the frontier if no measured point has both
  fewer bytes and more dB. This is the reading that means something outside the measured byte range.
* **Interpolation**: only defined *inside* the measured range [min bytes, max bytes]. Outside it the tool
  says ``extrapolated`` rather than clamping to the end-point -- clamping would declare every cheaper
  point dominated by the cheapest measured one, which is not a property of the data but of the clamp.
"""
import argparse
import json
import os

# Measured points of this format's rate-distortion curve (bytes, PSNR), bicycle, 25 held-out views.
# M35 ladder + M36 pruned-25 % arm b (17.96 MB / 21.24 dB).
FRONTIER = [
    (17_959_298, 21.24),
    (55_180_000, 21.82),
    (57_230_000, 22.53),
    (66_240_000, 23.60),
    (69_340_000, 23.80),
    (76_560_000, 24.06),
]

FLOOR = 0.02  # dB; a point within this of the interpolation counts as on the frontier


def interp_psnr(nbytes):
    """Linear interpolation of the frontier in bytes; None outside the measured range."""
    pts = sorted(FRONTIER)
    if nbytes < pts[0][0] or nbytes > pts[-1][0]:
        return None
    for (b0, p0), (b1, p1) in zip(pts, pts[1:]):
        if b0 <= nbytes <= b1:
            t = (nbytes - b0) / (b1 - b0) if b1 != b0 else 0.0
            return p0 + t * (p1 - p0)
    return pts[-1][1]


def pareto_dominator(nbytes, psnr, extra=()):
    """The measured point that dominates (nbytes, psnr), if any.

    Dominance needs strictly fewer bytes and at least as many dB: a point with more bytes and more dB is a
    different trade-off, not a dominator.
    """
    best = None
    for b, p in list(FRONTIER) + list(extra):
        if b < nbytes and p >= psnr - 1e-9:
            if best is None or b < best[0]:
                best = (b, p)
    return best


def parse_render(path):
    """`<tag> <arm> <bytes> <probe_render line>` -> dict."""
    rows = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            tag, arm, nbytes = parts[0], parts[1], parts[2]
            psnr = ssim = None
            for i, tok in enumerate(parts):
                if tok == "PSNR=" and i + 1 < len(parts):
                    psnr = float(parts[i + 1])
                elif tok.startswith("PSNR="):
                    psnr = float(tok.split("=", 1)[1])
                if tok == "SSIM=" and i + 1 < len(parts):
                    ssim = float(parts[i + 1])
                elif tok.startswith("ssim="):
                    ssim = float(tok.split("=", 1)[1])
                elif tok.startswith("SSIM="):
                    ssim = float(tok.split("=", 1)[1])
            rows.append({"tag": tag, "arm": arm, "bytes": int(nbytes), "psnr": psnr, "ssim": ssim})
    return rows


def parse_time(path):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 3 and parts[0].startswith("wall_"):
                out[parts[0][5:]] = int(parts[1])
    return out


def judge(rows, times):
    by = {(r["tag"], r["arm"]): r for r in rows}
    tags = sorted({r["tag"] for r in rows})
    per_prefix = []
    for tag in tags:
        a, b = by.get((tag, "a")), by.get((tag, "b"))
        if a and b and a["psnr"] is not None and b["psnr"] is not None:
            ratio = b["bytes"] / a["bytes"]
            d_psnr = b["psnr"] - a["psnr"]
            n1 = (ratio <= 0.97 and d_psnr >= -0.05) or (d_psnr >= 0.10 and ratio <= 1.02)
            per_prefix.append(
                {"tag": tag, "byte_ratio": round(ratio, 4), "d_psnr": round(d_psnr, 3), "N1": bool(n1)}
            )

    measured = [(r["bytes"], r["psnr"]) for r in rows if r["psnr"] is not None]
    on_frontier = []
    for r in rows:
        if r["psnr"] is None:
            continue
        ref = interp_psnr(r["bytes"])
        r["frontier_ref"] = None if ref is None else round(ref, 2)
        r["vs_frontier"] = None if ref is None else round(r["psnr"] - ref, 2)
        dom = pareto_dominator(r["bytes"], r["psnr"], extra=[m for m in measured if m != (r["bytes"], r["psnr"])])
        r["dominated_by"] = None if dom is None else {"bytes": dom[0], "psnr": dom[1]}
        if dom is None:
            on_frontier.append(f'{r["tag"]}-{r["arm"]}')

    budget = []
    for tag in tags:
        ta, tb = times.get(f"{tag}_a"), times.get(f"{tag}_b")
        if ta and tb:
            budget.append({"tag": tag, "wall_ratio": round(tb / ta, 3), "N3": bool(tb / ta <= 1.5)})
    return {"per_prefix": per_prefix, "on_frontier": on_frontier, "budget": budget}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/workspace/res/m39")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    rows = parse_render(os.path.join(args.dir, "render.txt"))
    times = parse_time(os.path.join(args.dir, "m39_time.txt"))
    res = judge(rows, times)

    print(f'{"prefix":8} {"arm":3} {"bytes":>12} {"MB":>7} {"PSNR":>6} {"SSIM":>7} {"interp":>6} {"vs":>6}')
    for r in rows:
        ps = f'{r["psnr"]:6.2f}' if r["psnr"] is not None else "   nan"
        ss = f'{r["ssim"]:7.4f}' if r["ssim"] is not None else "    nan"
        ref = "   n/a" if r["frontier_ref"] is None else f'{r["frontier_ref"]:6.2f}'
        vs = "   n/a" if r["vs_frontier"] is None else f'{r["vs_frontier"]:+6.2f}'
        print(f'{r["tag"]:8} {r["arm"]:3} {r["bytes"]:12,} {r["bytes"]/1e6:7.2f} {ps} {ss} {ref} {vs}')
    print()
    for v in res["per_prefix"]:
        print(
            f'[{v["tag"]}] b/a = {v["byte_ratio"]:.4f}x, dPSNR {v["d_psnr"]:+.3f} dB -> N1 '
            f'{"PASS" if v["N1"] else "FAIL"}'
        )
    for v in res["budget"]:
        print(f'[{v["tag"]}] wall b/a = {v["wall_ratio"]:.3f}x -> N3 {"PASS" if v["N3"] else "FAIL"}')
    print(f'N2 Pareto: on-frontier = {", ".join(res["on_frontier"]) or "none"}')
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"rows": rows, "judgement": res}, fh, indent=1)


if __name__ == "__main__":
    main()
