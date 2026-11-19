"""Summarise the M34 damage JSONs: what each condition changed, and what it cost.

    python tools/m34_summary.py --dir /workspace/res/m34/bonsai
"""

from __future__ import annotations

import argparse
import glob
import json
import os


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()

    rows = []
    for p in sorted(glob.glob(os.path.join(a.dir, "dmg_*", "damage_damage_*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        tag = os.path.basename(os.path.dirname(p)).replace("dmg_", "")
        cond = d.get("condition") or os.path.basename(p)[len("damage_"):-len(".json")]
        ch = d.get("changed", {})
        rows.append({"frame": tag, "cond": cond, "bytes": d.get("bytes"),
                     "lost": ch.get("lost_bytes"), "streams": ch.get("streams_with_lost_frames"),
                     "prim_some": ch.get("prim_changed_frac"), "means": ch.get("means_changed_frac"),
                     "dc": ch.get("dc_changed_frac"), "rest": ch.get("rest_changed_frac")})
    print(f"{'frame':>8} {'cond':>16} {'bytes':>10} {'lost':>9} {'prim':>7} {'means':>7} {'dc':>7} {'rest':>7}")
    for r in rows:
        f = lambda v: "-" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))
        print(f"{r['frame']:>8} {r['cond']:>16} {r['bytes']:>10} {f(r['lost']):>9} "
              f"{f(r['prim_some']):>7} {f(r['means']):>7} {f(r['dc']):>7} {f(r['rest']):>7} "
              f"{'' if not r['streams'] else r['streams']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
