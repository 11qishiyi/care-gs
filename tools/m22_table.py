"""The M22 table, generated from artifacts so the report and the paper cannot drift apart.

Reads the encode json (measured file sizes) and the render log (held-out PSNR) of each scene, prints
the rate-quality curve of the shared colour basis next to the shelf row it replaces.

    python tools/m22_table.py                       # bicycle and stump
    python tools/m22_table.py --out experiments/artifacts/a4/m22_table.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: the shelf row each scene is measured against (M20/M21 container path, zstd-12 + Morton)
SHELF = {
    "bicycle": {"name": "c10_o8_sh3", "mb": 144.55, "bps": 23.57, "psnr": 24.33, "n": 6131954},
    "stump": {"name": "c10_o8_sh3", "mb": 118.88, "bps": 24.42, "psnr": 25.81, "n": 4961797},
}
LINE = re.compile(r"^\s+(\w+?)_(r\d+_b\d+)_(?:[a-z]+_)?b\s+clean\s+.*?PSNR=\s*([\d.]+)")


def load(scene: str, artdir: str) -> list:
    enc = os.path.join(artdir, f"m22_encode{'' if scene == 'bicycle' else '_' + scene}.json")
    ren = os.path.join(artdir, f"m22_render{'' if scene == 'bicycle' else '_' + scene}.log")
    if not (os.path.exists(enc) and os.path.exists(ren)):
        return []
    psnr = {}
    for ln in open(ren, encoding="utf-8"):
        m = LINE.match(ln)
        if m and m.group(1) == scene:
            psnr[m.group(2)] = float(m.group(3))
    out = []
    for r in json.load(open(enc, encoding="utf-8")):
        tag = f"r{r['rank']:02d}_b{r['bits']:03d}"
        if tag not in psnr:
            continue
        base = 236.0 * r["n"] / 1e6
        out.append({"tag": tag, "rank": r["rank"], "bits": r["bits"], "mb": r["bytes"] / 1e6,
                    "bps": r["bytes"] / r["n"], "psnr": psnr[tag], "ratio": base / (r["bytes"] / 1e6),
                    "enc": r["encode_s"], "dec": r["decode_s"]})
    #: rows whose encode json was overwritten on the node before it could be fetched
    extra = os.path.join(artdir, f"m22_encode_extra{'' if scene == 'bicycle' else '_' + scene}.json")
    if os.path.exists(extra):
        doc = json.load(open(extra, encoding="utf-8"))
        seen = {(r["rank"], r["bits"]) for r in out}
        for r in doc.get("rows", []):
            tag = f"r{r['rank']:02d}_b{r['bits']:03d}"
            if tag not in psnr or (r["rank"], r["bits"]) in seen:
                continue
            base = 236.0 * r["n"] / 1e6
            out.append({"tag": tag, "rank": r["rank"], "bits": r["bits"], "mb": r["bytes"] / 1e6,
                        "bps": r["bytes"] / r["n"], "psnr": psnr[tag],
                        "ratio": base / (r["bytes"] / 1e6), "enc": r["encode_s"],
                        "dec": r["decode_s"]})
    return out


def render(scenes, artdir) -> str:
    L = ["# M22: one colour basis for six million Gaussians", ""]
    L.append("Measured file sizes (`zstd -12` + Morton, container path) and PSNR on the held-out views.")
    L.append("The shelf row is the 45-independently-coded-coefficients variant the basis replaces;")
    L.append("`bits` is the colour block's budget per primitive, i.e. the number the round turns.")
    L.append("")
    for scene in scenes:
        rows = load(scene, artdir)
        if not rows:
            continue
        sh = SHELF[scene]
        L.append(f"## {scene}")
        L.append("")
        L.append("| plan | colour bits | file | B/primitive | PSNR | ratio | vs shelf |")
        L.append("|---|---|---|---|---|---|---|")
        for r in sorted(rows, key=lambda r: -r["bits"]):
            L.append(f"| r={r['rank']} | {r['bits']} | {r['mb']:.2f} MB | {r['bps']:.2f} | "
                     f"{r['psnr']:.2f} | {r['ratio']:.2f}x | {r['psnr'] - sh['psnr']:+.2f} dB |")
        L.append(f"| shelf `{sh['name']}` (45 x 3 bit) | 165 | {sh['mb']:.2f} MB | {sh['bps']:.2f} | "
                 f"{sh['psnr']:.2f} | {236.0 * sh['n'] / 1e6 / sh['mb']:.2f}x | -- |")
        L.append("")
        best = [r for r in rows if r["psnr"] >= sh["psnr"] - 0.35]
        if best:
            b = max(best, key=lambda r: r["ratio"])
            L.append(f"Pre-registered L1 window (within 0.35 dB of the shelf): best point "
                     f"**r={b['rank']}, {b['bits']} bits -> {b['mb']:.2f} MB, {b['ratio']:.2f}x, "
                     f"{b['psnr'] - sh['psnr']:+.2f} dB**.")
            L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts", default=os.path.join(ROOT, "experiments", "artifacts", "a4"))
    ap.add_argument("--scenes", default="bicycle,stump")
    ap.add_argument("--out")
    a = ap.parse_args()
    txt = render([s.strip() for s in a.scenes.split(",") if s.strip()], a.artifacts)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(txt)
        print("WROTE", a.out)
    else:
        print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
