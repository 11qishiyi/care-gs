"""Read the M34 damage logs and print the frame-size sweep as the table the criteria need.

    python tools/m34_collect.py --dir /workspace/res/m34

Each ``damage_<scene>_<frame>.log`` holds the intact control's PSNR followed by one line per burst
condition (``damage_0010`` = 0.10 %, ``damage_0100`` = 1.0 %, ``damage_0500`` = 5.0 %).  The log's
PSNR lines are the only measurement here; the file sizes come from ``sizes_<scene>_<frame>.txt``.
"""

from __future__ import annotations

import argparse
import glob
import os
import re

CONDS = (("damage_0010", 0.10), ("damage_0100", 1.00), ("damage_0500", 5.00))
FRAME_ORDER = {"f4096k": 4 << 20, "f1024k": 1 << 20, "f0256k": 256 << 10}
PSNR = re.compile(r"PSNR\s+([0-9.]+)")
PENALTY = re.compile(r"(\d+)\s*frames?")
COND_LINE = re.compile(r"^(control|damage_\d{4}|trunc_\d{2})\s+([0-9.]+) MB")


def parse_block(text: str) -> dict:
    """Map condition name -> {psnr, penalty, bytes}.  A condition line starts a block; the next PSNR
    line belongs to it (the control is printed first and must not be credited to the last burst)."""
    out, cur = {}, None
    for line in text.splitlines():
        m = COND_LINE.match(line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, {})["bytes"] = float(m.group(2))
            pen = PENALTY.search(line)
            out[cur]["penalty"] = int(pen.group(1)) if pen else None
            continue
        p = PSNR.search(line)
        if p is not None and cur is not None:
            out[cur]["psnr"] = float(p.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="/workspace/res/m34")
    a = ap.parse_args()

    rows = []
    for log in sorted(glob.glob(os.path.join(a.dir, "damage_*.log"))):
        base = os.path.basename(log)[len("damage_"):-len(".log")]
        scene, _, frame = base.rpartition("_")
        if frame not in FRAME_ORDER:
            continue
        rec = parse_block(open(log, encoding="utf-8", errors="replace").read())
        size = None
        sp = os.path.join(a.dir, f"sizes_{base}.txt")
        if os.path.exists(sp):
            m = re.search(r"([0-9.]+)\s*$", open(sp, encoding="utf-8").read().strip().splitlines()[-1])
        rows.append({"scene": scene, "frame": frame, "frame_bytes": FRAME_ORDER[frame],
                     "size_line": size, "cond": rec})

    scenes = sorted({r["scene"] for r in rows})
    for scene in scenes:
        rs = sorted([r for r in rows if r["scene"] == scene], key=lambda r: -r["frame_bytes"])
        ctrl = next((r for r in rs if r["frame"] == "f4096k"), rs[0])
        cbas = ctrl["cond"].get("control", {}).get("psnr")
        print(f"\n== {scene}"
              + (f"   control (4 MB) {cbas:.2f} dB" if cbas else ""))
        print(f"{'frame':>8} {'file MB':>9} {'0.10%':>16} {'1.0%':>16} {'5.0%':>16}")
        for r in rs:
            cells = []
            for name, _pct in CONDS:
                c = r["cond"].get(name, {})
                ps = c.get("psnr")
                if ps is None:
                    cells.append(f"{'--':>16}")
                else:
                    d = f" ({ps - cbas:+.2f})" if cbas else ""
                    pen = c.get("penalty")
                    cells.append(f"{ps:6.2f}{d}{'' if pen is None else f' [{pen}f]':>0}"[:16].rjust(16))
            mb = r["cond"].get("damage_0010", {}).get("bytes") or 0.0
            print(f"{r['frame']:>8} {mb:9.2f} " + " ".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
