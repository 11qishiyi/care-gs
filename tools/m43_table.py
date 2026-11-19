"""M43 -- read the three-variant A/B rows and decide the round.

    python -m tools.m43_table --dir /workspace/res/m43

Writes ``m43_table.json`` and prints one line per scene. The verdict is same-node only: every row comes from the
same host and the same session, so the ratio between variants is the measurement and the absolute seconds are not.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "experiments")):
    if p not in sys.path:
        sys.path.insert(0, p)

ORDER = ("legacy", "m42", "m43")


def rows(d):
    out = {}
    for path in sorted(glob.glob(os.path.join(d, "enc_*.json"))):
        with open(path, encoding="utf-8") as fh:
            row = json.load(fh)
        out.setdefault(row["scene"], {})[row["variant"]] = row
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/workspace/res/m43")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    table = rows(args.dir)
    print(f"{'scene':8s} {'variant':7s} {'build':>7s} {'peak':>7s} {'total':>7s}  md5")
    verdict = {}
    for scene in ("bicycle", "stump", "bonsai"):
        if scene not in table:
            continue
        r = table[scene]
        for v in ORDER:
            if v not in r:
                continue
            x = r[v]
            print(f"{scene:8s} {v:7s} {x['build_s']:7.1f} {x['peak_rss_gb']:7.2f} {x['total_s']:7.1f}  {x['md5'][:12]}")
        if {"m42", "m43"} <= set(r):
            verdict[scene] = {
                "peak_m42": r["m42"]["peak_rss_gb"], "peak_m43": r["m43"]["peak_rss_gb"],
                "peak_ratio": round(r["m43"]["peak_rss_gb"] / r["m42"]["peak_rss_gb"], 3),
                "build_m42": r["m42"]["build_s"], "build_m43": r["m43"]["build_s"],
                "build_ratio": round(r["m43"]["build_s"] / r["m42"]["build_s"], 3),
                "same_md5": r["m42"]["md5"] == r["m43"]["md5"] == r.get("legacy", r["m43"])["md5"],
            }
    out = args.out or os.path.join(args.dir, "m43_table.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(verdict, fh, indent=1)
    for scene, v in verdict.items():
        print(f"VERDICT {scene}: peak {v['peak_ratio']:.3f}x  build {v['build_ratio']:.3f}x  same_md5={v['same_md5']}")


if __name__ == "__main__":
    main()
