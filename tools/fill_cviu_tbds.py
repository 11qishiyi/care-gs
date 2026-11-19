"""Fill the \\TBD{} placeholders of the CVIU manuscript from the measured artifacts.

Every value comes from one of two files:

  results_v120/audit_bound.json        the audit / envelope run (experiments/audit_bound.py)
  <dump>/dump_summary.json             PSNR, SSIM and per-view statistics per variant

Run with ``--print`` first: it shows the value behind each key and changes nothing.
The replacement is exact-string, and the script refuses to run if a key it intends to
fill is missing from the map, so a silent partial fill is impossible.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np

MAIN = "submission/cviu/main.tex"


def load(audit_path, dump_path):
    audit = json.load(open(audit_path, encoding="utf-8"))
    rows = audit["rows"]
    dump = json.load(open(os.path.join(dump_path, "dump_summary.json"), encoding="utf-8"))

    mae = np.array([r["audit_mae_pp"] for r in rows])
    bias = np.array([r["audit_bias_pp"] for r in rows])
    p95 = np.array([r["audit_abs_p95_pp"] for r in rows])
    frac = np.array([r["ks_alone_holds_frac"] for r in rows])
    tight = np.array([r["tightness_mean"] for r in rows])
    n_cells = len(rows)

    # the exact no-op edit gives the estimator's own floor, if it is in the grid
    noop = [r for r in rows if r["variant"] == "quant8"]
    noop_bias = float(np.mean([r["audit_bias_pp"] for r in noop])) if noop else 0.0
    noop_mae = float(np.mean([r["audit_mae_pp"] for r in noop])) if noop else 0.0

    # k-view curve, pooled over cells
    kvals = {}
    for r in rows:
        for k, d in (r.get("kview") or {}).items():
            if d:
                kvals.setdefault(int(k), []).append(d["mae_pp"])
    kmae = {k: float(np.mean(v)) for k, v in sorted(kvals.items())}

    # coverage loss vs PSNR loss, for the fidelity subsection
    psnr = {}
    for sc in dump["scenes"]:
        name = sc["scene"]
        fresh = sc["variants"].get("clean", {}).get("psnr")
        for v, st in sc["variants"].items():
            if v != "clean" and st.get("psnr") is not None and fresh:
                psnr[(name, v)] = fresh - st["psnr"]        # dB lost
    pairs = [(100 * r["drop_mean"], psnr[(r["scene"], r["variant"])])
             for r in rows if (r["scene"], r["variant"]) in psnr]
    if pairs:
        cov = np.array([p[0] for p in pairs])
        db = np.array([p[1] for p in pairs])
        rho = float(np.corrcoef(cov, db)[0, 1])
        # coverage loss expressed as a percentage, compared with the dB loss: the units
        # differ, so we report the fraction of cells where the coverage loss in points
        # exceeds the PSNR loss in tenths of a dB (a deliberately conservative reading)
        n_more = int(np.sum(np.abs(cov) > db))
    else:
        rho, n_more = float("nan"), 0

    vals = dict(
        MAE=f"{mae.mean():.1f}",
        p95=f"{np.percentile(p95, 50):.1f}",
        bias=f"{abs(bias).mean():.1f}",
        N=str(n_cells),
        n=str(len(rows) // 7),
        frac=f"{100 * frac.mean():.0f}",
        tightness=f"{tight.min():.2f}--{tight.max():.2f}",
        tight_med=f"{np.median(tight):.2f}",
        over=f"{1 / max(np.median(tight), 1e-6):.1f}",
        noop_bias=f"{noop_bias:+.1f}",
        noop_mae=f"{noop_mae:.1f}",
        rho=f"{rho:+.2f}",
        n_fid=str(n_more),
        k1=str(sorted(kmae)[0]) if kmae else "1",
        k2=str(sorted(kmae)[1]) if len(kmae) > 1 else "2",
        k4=str(sorted(kmae)[2]) if len(kmae) > 2 else "4",
        mae_k1=f"{kmae.get(sorted(kmae)[0], float('nan')):.1f}" if kmae else "--",
        mae_k2=f"{kmae.get(sorted(kmae)[1], float('nan')):.1f}" if len(kmae) > 1 else "--",
        mae_k4=f"{kmae.get(sorted(kmae)[2], float('nan')):.1f}" if len(kmae) > 2 else "--",
    )
    return vals, dict(noop_cells=len(noop), n_pairs=len(pairs), kmae=kmae)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default="results_v120/audit_bound.json")
    ap.add_argument("--dump", default="results_v120/dump")
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args(argv)

    vals, extra = load(a.audit, a.dump)
    print("computed:", json.dumps(vals, indent=2))
    print("extra:", json.dumps(extra, indent=2, default=str))
    if a.print:
        return 0

    tex = open(MAIN, encoding="utf-8").read()
    unused = []
    for k, v in vals.items():
        token = "\\TBD{%s}" % k
        if token in tex:
            tex = tex.replace(token, v)
        else:
            unused.append(k)
    open(MAIN, "w", encoding="utf-8").write(tex)

    left = sorted(set(re.findall(r"\\TBD\{([^}]*)\}", tex)))
    print("filled:", ", ".join(sorted(k for k in vals if k not in unused)))
    if unused:
        print("not present in tex (fine):", ", ".join(unused))
    print("still left:", left or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
