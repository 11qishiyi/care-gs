"""One table for the paper: every competitor's operating point on the same scene, with our best
measured row that fits inside it.

The three comparison rounds (M16 C2, M17 C5, M18 C6/C7) each answered this for one budget.  This
tool answers it for all of them at once, from artifacts, so the numbers in the paper and the numbers
in the round reports cannot drift apart.

    python tools/sota_table.py                       # every scene that has artifacts
    python tools/sota_table.py --scenes bicycle      # one scene
    python tools/sota_table.py --out docs/sota.md

Published sizes and PSNRs come from `experiments/published_3dgs.json` (transcribed from the papers);
our rows come from the measured-bytes json plus the analysed rd json, so every "our" number is a
measured file size, not an interpolated rate.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "experiments"))

import cmp_points as CP  # noqa: E402

#: C1 measured our protocol 0.55 dB below the published one on bicycle (M16); the same bias is
#: assumed wherever a published number is quoted, and it is applied to *their* bar, not to ours.
PROTOCOL_BIAS_DB = 0.55
#: Artifact pairs, newest last, so a later round's row wins when two rounds measure the same point.
SOURCES = [
    ("m16", "m16_rd.json", "m16_bytes.json"),
    ("m17", "m17_rd.json", "m17_bytes.json"),
    ("m18", "m18_rd.json", "m18_bytes.json"),
]


def _slug(scene: str) -> str:
    """`bicycle_k35s30_ft` -> `bicycle`: artifacts name entries, papers name scenes."""
    m = re.match(r"^([a-z]+)", scene)
    return m.group(1) if m else scene


def collect_all(artdir: str) -> list:
    rows = []
    for tag, rd, by in SOURCES:
        rdp, byp = os.path.join(artdir, rd), os.path.join(artdir, by)
        if not (os.path.exists(rdp) and os.path.exists(byp)):
            continue
        for r in CP.collect(byp, rdp):
            r["round"] = tag
            r["scene_key"] = _slug(r["scene"])
            rows.append(r)
    return rows


def best_within(rows: list, scene_key: str, mb: float, slack: float = 1.0):
    """Our highest-PSNR compressed row for ``scene_key`` whose file is at most ``mb * slack``."""
    cand = [r for r in rows
            if r["scene_key"] == scene_key and r["variant"] != "clean"
            and r.get("mb") is not None and r["mb"] <= mb * slack
            and r.get("psnr") is not None]
    if not cand:
        return None
    return max(cand, key=lambda r: r["psnr"])


def render(scenes, pub, rows) -> str:
    L = ["# Our measured rows against the published operating points", ""]
    L.append("Published numbers are transcribed from the papers (`experiments/published_3dgs.json`);")
    L.append("ours are measured file sizes (`zstd -12` + Morton order) and PSNR on the held-out")
    L.append("views.  The gap column is *theirs minus ours*, so a **positive number means we are")
    L.append("behind** at that size and a negative one means we lead.  The 0.55 dB protocol bias that")
    L.append("C1 measured is not folded into the gap; it is stated once, here.")
    L.append("")
    for scene in scenes:
        if scene not in pub.get("3dgs", {}):
            continue
        L.append(f"## {scene}")
        L.append("")
        L.append("| published | its MB | its PSNR | our best ≤ its size | our MB | our PSNR | gap dB |")
        L.append("|---|---|---|---|---|---|---|")
        for name in ("3dgs", "hac", "pcgs"):
            p = pub.get(name, {}).get(scene)
            if not p:
                continue
            hit = best_within(rows, scene, p["mb"], slack=1.05)
            if hit is None:
                L.append(f"| {name.upper()} | {p['mb']:.2f} | {p['psnr']:.2f} | "
                         f"*nothing fits* | — | — | — |")
                continue
            L.append(f"| {name.upper()} | {p['mb']:.2f} | {p['psnr']:.2f} | "
                     f"`{hit['variant']}` ({hit['scene']}, {hit['round']}) | {hit['mb']:.2f} | "
                     f"{hit['psnr']:.2f} | **{p['psnr'] - hit['psnr']:+.2f}** |")
        L.append("")
        #: Our own shelf on the same scene, base model only: that is the like-for-like high-rate
        #: comparison, and it is where the near-lossless claim lives.  Mid-rate rows are already
        #: in the budget table above (they come from pruned entries, which are not comparable to a
        #: published 30 k model at 1x).
        shelf = [r for r in rows if r["scene"] == scene and r["variant"] != "clean"
                 and r.get("mb") is not None]
        if shelf:
            L.append("Our shelf on the base model of this scene (every coded variant, priced):")
            L.append("")
            L.append("| variant | MB | rate × | PSNR | drop vs clean |")
            L.append("|---|---|---|---|---|")
            for r in sorted(shelf, key=lambda r: r["psnr"], reverse=True):
                L.append(f"| `{r['variant']}` | {r['mb']:.2f} | {r['rate']:.2f} | {r['psnr']:.2f} | "
                         f"{r.get('drop_pp') or 0.0:+.2f} pp |")
            L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts", default=os.path.join(ROOT, "experiments", "artifacts", "a4"))
    ap.add_argument("--published", default=os.path.join(ROOT, "experiments", "published_3dgs.json"))
    ap.add_argument("--scenes", default="bicycle,stump")
    ap.add_argument("--out")
    a = ap.parse_args()
    pub = json.load(open(a.published, encoding="utf-8"))["methods"]
    rows = collect_all(a.artifacts)
    if not rows:
        print("no artifacts found under", a.artifacts, file=sys.stderr)
        return 1
    scenes = [s.strip() for s in a.scenes.split(",") if s.strip()]
    txt = render(scenes, pub, rows)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(txt)
        print("WROTE", a.out)
    else:
        print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
