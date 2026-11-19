"""Collect the M33 damage table from the per-scene logs.

    python tools/m33_collect.py --dir /workspace/res/m33

Reads ``damage_<scene>.log`` (one block per condition: a mechanical line then an indented render line)
and prints per-scene and pooled tables: condition, file size, lost MB, PSNR.
"""

from __future__ import annotations

import argparse
import glob
import os
import re


def parse(path: str) -> list:
    rows, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^(control|damage_\d+|trunc_\d+)\s+([\d.]+) MB\s+lost\s+([\d.]+) MB\s+streams\s+(.+)$",
                     line.strip())
        if m:
            cur = {"cond": m.group(1), "mb": float(m.group(2)), "lost_mb": float(m.group(3)),
                   "streams": m.group(4).strip(), "psnr": None}
            rows.append(cur)
            continue
        if cur is not None and "PSNR" in line:
            mm = re.search(r"PSNR=?\s*([\d.]+)", line)
            if mm:
                cur["psnr"] = float(mm.group(1))
    return rows


def fmt(rows: list, title: str) -> str:
    out = [f"## {title}", "", "| condition | file MB | lost MB | streams with lost frames | PSNR |",
           "|---|---|---|---|---|"]
    for r in rows:
        s = r["streams"] if len(r["streams"]) <= 46 else r["streams"][:43] + "..."
        p = "—" if r["psnr"] is None else f"{r['psnr']:.2f}"
        out.append(f"| {r['cond']} | {r['mb']:.2f} | {r['lost_mb']:.2f} | {s} | {p} |")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="/workspace/res/m33")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    blocks = []
    for log in sorted(glob.glob(os.path.join(a.dir, "damage_*.log"))):
        scene = os.path.basename(log)[len("damage_"):-len(".log")]
        blocks.append(fmt(parse(log), scene))
    text = "\n\n".join(blocks)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
