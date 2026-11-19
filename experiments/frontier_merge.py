"""Merge the per-asset ``m4_bytes`` documents into one ``frontier_bytes.json``.

``m4_bytes`` writes ``{"scenes": [{scene, n, sh_degree, rows: [...]}], "criteria": {...}}``,
so the merge has to concatenate ``scenes`` (the shell one-liner that produced an empty file
was reading a top-level ``rows`` key that does not exist).
"""
import glob
import json
import os
import sys

import common as C

SRC = os.path.join("experiments", "artifacts", "a4", "frontier_raw")
OUT = os.path.join("experiments", "artifacts", "a4", "frontier_bytes.json")


def merge(paths):
    scenes, meta, crit = [], None, {}
    for p in sorted(paths):
        doc = json.load(open(p, encoding="utf-8"))
        meta = meta or doc.get("meta", {})
        for k, v in (doc.get("criteria") or {}).items():
            crit.setdefault(k, []).extend(v if isinstance(v, list) else [v])
        for sc in doc.get("scenes", []):
            scenes.append(sc)
    return {"meta": meta or {}, "criteria": crit, "scenes": scenes}


def main(argv=None) -> int:
    paths = [p for p in sorted(glob.glob(os.path.join(SRC, "bytes_*.json")))]
    if not paths:
        raise SystemExit(f"no bytes_*.json under {SRC}")
    doc = merge(paths)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
    rows = sum(len(sc["rows"]) for sc in doc["scenes"])
    C.log(f"WROTE {OUT} scenes={len(doc['scenes'])} rows={rows}")
    for sc in doc["scenes"]:
        for r in sc["rows"]:
            C.log(f"  {sc['scene']:10s} {r['spec']:12s} "
                  f"model {r['model_bytes_per_prim']:7.2f} "
                  f"zstd+morton {r['zstd_morton_bytes_per_prim']:7.2f} B/stored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
