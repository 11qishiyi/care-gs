#!/usr/bin/env python3
"""Fold the A4 artifacts into one small summary the workstation can consume.

The full manifest (``dump/rd_manifest.json``) carries every per-variant stat on
the node; this script keeps only what the write-up quotes, so the round trip is
a few KB instead of a few hundred.

Usage::

    python experiments/a4_summarize.py --dump /workspace/res/a4/dump \
        --rd /workspace/res/a4/rd.json --exposure /workspace/res/a4/exposure.json \
        --out /workspace/res/a4/a4_summary.json
"""
import argparse
import json

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiments import common as C  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default="/workspace/res/a4/dump")
    ap.add_argument("--rd", default="/workspace/res/a4/rd.json")
    ap.add_argument("--exposure", default="/workspace/res/a4/exposure.json")
    ap.add_argument("--out", default="/workspace/res/a4/a4_summary.json")
    args = ap.parse_args(argv)

    rd = json.load(open(args.rd))
    man = json.load(open(os.path.join(args.dump, "rd_manifest.json")))
    # The manifest is {"scenes": [{scene, variants: {name: {psnr, n_primitives, ...,
    # per_view: [...]}}}, ...]}; ``per_view`` is what makes the file large, so only
    # the per-variant scalars are kept here.
    man_scenes = {m["scene"]: m for m in man.get("scenes", [])}
    expo = json.load(open(args.exposure)) if os.path.exists(args.exposure) else {"scenes": []}

    out = {"scenes": {}, "criteria": rd["summary"]["criteria"], "meta": rd.get("meta", {})}
    for s in rd["scenes"]:
        name = s["scene"]
        entry = {
            "sh_degree": s["sh_degree"],
            "n_views": s["n_views"],
            "clean_coverage": s["clean_coverage"],
            "q_mean": s["q_mean"],
            "variants": {},
        }
        for r in s["rows"]:
            entry["variants"][r["variant"]] = {
                "family": r["family"],
                "rate": r["rate"],
                "bytes_per_prim": r["bytes_per_prim"],
                "drop_pp": r["drop_pp"],
                "drop_lo_pp": r["drop_lo"] * 100.0,
                "drop_hi_pp": r["drop_hi"] * 100.0,
                "psnr": r["psnr"],
            }
        blk = man_scenes.get(name, {})
        stats = blk.get("variants", {})
        scal = ("psnr", "n_primitives", "mean_alpha", "resid_median", "resid_mean")
        entry["stats"] = {v: {k: s.get(k) for k in scal if k in s}
                          for v, s in stats.items()}
        if "clean" in stats:
            entry["clean"] = entry["stats"]["clean"]
        ex = next((e for e in expo.get("scenes", []) if e["scene"] == name), None)
        if ex:
            entry["exposure"] = {k: ex[k] for k in
                                 ("psnr_raw_mean", "psnr_affine_mean", "gain_needed_median",
                                  "gain_needed_min", "gain_needed_max")}
        out["scenes"][name] = entry

    C.json_dump(args.out, out)
    print(f"WROTE {args.out}")
    for name, e in out["scenes"].items():
        c = e.get("clean", {})
        print(f"  {name:<10} clean psnr {c.get('psnr')}  prims {c.get('n_primitives')}  "
              f"variants {len(e['variants'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
