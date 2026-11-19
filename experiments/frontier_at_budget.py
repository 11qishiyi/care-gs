"""Print the per-asset frontier entry at one budget, next to the paper's prune-30% row.

Both halves are copied from files, not from memory: coverage/PSNR from the rd tables, and the
baseline from ``submission/cviu/tab_fidelity.tex`` (parsed, so a typo in the paper surfaces here).
"""
import argparse
import json
import os
import re
import sys

import frontier as F

TEX = os.path.join("submission", "cviu", "tab_fidelity.tex")


def parse_tex(path=TEX):
    """``{asset: {'clean': (psnr, drop), 'prune30': (psnr, d_psnr, drop)}}``."""
    out, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("\\"):
            continue
        cells = [c.strip() for c in line.rstrip("\\").split("&")]
        cells = [c for c in cells if c != ""]
        if len(cells) >= 5:
            asset = cells[0].replace("\\_", "_")
            cur = asset
            out.setdefault(cur, {})
            kind = "clean" if cells[1] == "fresh" else None
            if kind:
                out[cur]["clean"] = (float(cells[2]), 0.0)
            continue
        if cur is None or len(cells) < 4:
            continue
        label = cells[0]
        if "prune 30" in label:
            out[cur]["prune30"] = (float(cells[1]), float(cells[2]), float(cells[3]))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join("experiments", "artifacts", "a4"))
    ap.add_argument("--budget", type=float, default=3.33)
    ap.add_argument("--reference", default=None,
                    help="per-asset budget = this variant's measured rate (e.g. p30), which is "
                         "the only apples-to-apples comparison against a paper edit")
    ap.add_argument("--exclude", default="prune",
                    help="families the challenger may not come from (default: prune)")
    a = ap.parse_args(argv)
    import glob
    paths = []
    for tag in F.SOURCES:
        paths += sorted(glob.glob(os.path.join(a.dir, f"{tag}.json")))
    rows = F.load_rows(paths)
    tex = parse_tex()
    if a.reference:
        print(f"budget = each asset's own `{a.reference}` rate\n")
    else:
        print(f"budget {a.budget:.2f}x\n")
    print(f"| asset | {a.reference or 'prune30'} (baseline) | challenger | gain |")
    print("|---|---|---|---|")
    for scene in sorted(rows):
        rs = rows[scene]
        if a.reference:
            ref = [r for r in rs if r["variant"] == a.reference]
            if not ref:
                print(f"| {scene} | — | (no {a.reference}) | — |")
                continue
            base = ref[0]
            budget = base["rate"]
        else:
            base = None
            budget = a.budget
        cand = [r for r in rs if r["rate"] <= budget * 1.05
                and a.exclude not in r["family"]]
        tex_row = tex.get(scene, {}).get("prune30")
        if base is not None:
            ref_txt = f"{base['drop_pp']:+.2f} pp @ {base['rate']:.2f}×"
            base_pp = base["drop_pp"]
        elif tex_row:
            ref_txt = f"{tex_row[2]:+.1f} pp / {tex_row[1]:+.2f} dB (paper)"
            base_pp = tex_row[2]
        else:
            ref_txt, base_pp = "—", None
        if not cand:
            print(f"| {scene} | {ref_txt} | — | — |")
            continue
        r = max(cand, key=lambda x: (x["drop_pp"], -x["rate"]))
        dps = r.get("d_psnr")
        dps_txt = f"{dps:+.2f} dB" if dps is not None else "?"
        gain = f"+{r['drop_pp'] - base_pp:.1f} pp" if base_pp is not None else "—"
        print(f"| {scene} | {ref_txt} | {r['drop_pp']:+.2f} pp / {dps_txt} @ "
              f"{r['rate']:.2f}× `{r['variant']}` | {gain} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
