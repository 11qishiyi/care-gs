"""Print the M16 measured rows as a markdown table, one block per archive.

    python tools/m16_table.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))

import cmp_points as CP  # noqa: E402

A4 = os.path.join("experiments", "artifacts", "a4")


def main() -> int:
    rows = CP.collect(os.path.join(A4, "m16_bytes.json"), os.path.join(A4, "m16_rd.json"))
    scenes = []
    for r in rows:
        if r["scene"] not in scenes:
            scenes.append(r["scene"])
    for sc in scenes:
        print(f"\n### {sc}\n")
        print("| variant | MB | rate x | PSNR | SSIM | drop pp |")
        print("|---|---|---|---|---|---|")
        sel = [r for r in rows if r["scene"] == sc]
        sel.sort(key=lambda r: -(r["psnr"] or 0))
        for r in sel:
            print(f"| `{r['variant']}` | {r['mb']:.2f} | {r['rate']:.2f} | {r['psnr']:.2f} | "
                  f"{(r['ssim'] or 0):.4f} | {r['drop_pp']:+.2f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
