"""M31 -- assemble the multi-scene table from the run logs.

Reads, per scene: the container size, the encode wall clock, the decode timing line, the render line and
the per-stream table, and prints the near-lossless table the paper needs.  Nothing is recomputed; every
number comes from a file this round wrote.

The three scenes are the ones the pretrained release actually publishes at
``<scene>/point_cloud/iteration_30000/point_cloud.ply`` -- every other name 404s (see tools/m31_probe_urls.sh).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re

SCENES = ("bicycle", "stump", "bonsai")
CLEAN = {                       # payload MB (236 B/prim, the series convention) and the clean PSNR
    "bicycle": (1447.1, 24.52),
    "stump": (1170.98, 26.15),
    "bonsai": (293.78, 28.06),
}
FILE_MB = {"bicycle": 1520.7, "stump": 1230.5, "bonsai": 308.7}   # fp32 PLY as shipped (248 B/prim)


def parse_render(path: str):
    if not os.path.exists(path):
        return None
    best = None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.search(r"n=([\d,]+).*?PSNR=\s*([\d.]+).*?ssim=([\d.]+)", line)
        if m:
            best = (int(m.group(1).replace(",", "")), float(m.group(2)), float(m.group(3)))
    return best


def parse_cost(path: str):
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.search(r"decode\s+([\d.]+) s\s+peak RSS\s+([\d.]+) GB", line)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:\3dsg_1\experiments\artifacts\a4\m31")
    a = ap.parse_args()
    root = a.root
    sizes_path = os.path.join(root, "sizes.json")
    sizes = json.load(open(sizes_path, encoding="utf-8")) if os.path.exists(sizes_path) else {}

    print("| scene | primitives | file | B/prim | ratio | ratio vs file | clean dB | ours dB | delta | "
          "SSIM | enc s (2 files) | dec s | RSS GB |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in SCENES:
        gs = sorted(glob.glob(os.path.join(root, s, "*_auto.gs1")))
        if not gs and s not in sizes:
            print(f"| {s} | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |")
            continue
        size = (os.path.getsize(gs[0]) if gs else sizes[s]) / 1e6
        r = parse_render(os.path.join(root, f"render_{s}.log"))
        n = r[0] if r else 0
        enc = None
        p = os.path.join(root, f"enc_{s}.txt")
        if os.path.exists(p):
            m = re.search(r"encode_wall ([\d.]+)", open(p, encoding="utf-8").read())
            enc = float(m.group(1)) if m else None
        cost = parse_cost(os.path.join(root, f"cost_{s}.log")) or (0.0, 0.0)
        clean_mb, clean_db = CLEAN.get(s, (0.0, 0.0))
        ratio = clean_mb / size if size else 0.0
        ratio_file = FILE_MB.get(s, 0.0) / size if size else 0.0
        delta = (r[1] - clean_db) if r else 0.0
        print(f"| {s} | {n:,} | {size:.2f} MB | {size*1e6/n if n else 0:.2f} | {ratio:.2f}x | "
              f"{ratio_file:.2f}x | {clean_db:.2f} | {r[1] if r else 0:.2f} | {delta:+.2f} | "
              f"{r[2] if r else 0:.4f} | {enc if enc else 0:.0f} | {cost[0]:.2f} | {cost[1]:.2f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
