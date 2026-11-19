"""Drop degenerate variant rows (default: any name containing ``sh1``) from a manifest.

Why: the published per-block min-max SH quantiser has ``qmax = 2**(b-1) - 1``, which
is 0 at b=1, so a 1-bit SH grid divides by zero and every coefficient becomes NaN.
The row is useless for the tables and NaN is not valid JSON for downstream readers,
so it is removed before analysis.  A raw backup is kept next to the original.

Usage:  python _drop_sh1.py <path to m1_manifest.json> [--pat sh1]
"""
from __future__ import annotations

import json
import os
import shutil
import sys


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: _drop_sh1.py <manifest.json> [--pat sh1]")
        return 2
    path = argv[0]
    pat = "sh1"
    if "--pat" in argv:
        pat = argv[argv.index("--pat") + 1]

    doc = json.load(open(path, encoding="utf-8"))
    raw = path.replace(".json", "_raw.json")
    if not os.path.exists(raw):
        shutil.copy2(path, raw)

    dropped = []
    for scene in doc.get("scenes", []):
        vs = scene.get("variants") or {}
        for name in [k for k in list(vs) if pat in k]:
            vs.pop(name)
            dropped.append((scene.get("scene"), name))
    json.dump(doc, open(path, "w", encoding="utf-8"))
    print("dropped %d row(s): %s" % (len(dropped), dropped))
    print("backup at %s" % raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
