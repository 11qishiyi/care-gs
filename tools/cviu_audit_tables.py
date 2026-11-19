"""Turn the audit / fidelity JSON into the three LaTeX tables the revision adds.

Inputs
------
``--dump``   the directory holding ``dump_summary.json`` written by
             ``experiments/dump_artifacts.py --fidelity`` (PSNR, SSIM, LPIPS per
             variant, plus the per-view lists).
``--audit``  ``audit_bound.json`` written by ``experiments/audit_bound.py``.

Outputs (written into ``--out-dir``)
------------------------------------
``tab_audit.tex``     every asset x edit cell: true post-edit coverage, the audit
                      estimate, its error, the Kolmogorov distance and the ratio
                      loss/KS.
``tab_kview.tex``     mean absolute audit error as a function of how many shipped
                      views are re-rendered.
``tab_fidelity.tex``  PSNR / SSIM / LPIPS against the coverage change, which is the
                      table that answers "why not just use LPIPS".

Every number is printed from the JSON; nothing is hard-coded.  ``--check`` re-reads
the generated files and asserts the row counts, so a silent schema change fails
loudly instead of printing an empty table.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

VAR_ORDER = ["prune50", "prune30", "pup30", "shdeg1", "quant8", "quant6", "quant4"]
VAR_LABEL = {
    "prune50": "prune 50\\%", "prune30": "prune 30\\%", "pup30": "Fisher 30\\%",
    "shdeg1": "SH 3$\\to$1", "quant8": "SH 8-bit", "quant6": "SH 6-bit",
    "quant4": "SH 4-bit",
}


def load_audit(path):
    d = json.load(open(path, encoding="utf-8"))
    rows = {}
    for r in d["rows"]:
        rows.setdefault(r["scene"], {})[r["variant"]] = r
    return d, rows


def load_dump(path):
    p = os.path.join(path, "dump_summary.json")
    d = json.load(open(p, encoding="utf-8"))
    scenes = {}
    rows = d.get("scenes", [])
    if isinstance(rows, dict):                 # tolerant of an older schema
        rows = [dict(scene=k, variants=v) for k, v in rows.items()]
    for row in rows:
        scenes[row["scene"]] = row["variants"]
    return scenes


def tex_name(s):
    """Escape the characters a scene name can contain that are special in text mode."""
    return str(s).replace("_", "\\_").replace("&", "\\&").replace("%", "\\%")


def _emit(out_dir, name, tex):
    """Write only the ``tabular`` block.

    The float, the caption and the label live in ``main.tex`` next to the prose that
    discusses them; generating them twice would nest two ``table`` environments.
    """
    a = tex.index("\\begin{tabular}")
    b = tex.index("\\end{tabular}") + len("\\end{tabular}")
    open(os.path.join(out_dir, name), "w", encoding="utf-8").write(tex[a:b] + "\n")


def fmt_pp(x, nd=1):
    return f"${100 * x:+.{nd}f}$" if isinstance(x, (int, float)) else "--"


def table_audit(audit, out_dir):
    lines = []
    for scene in sorted(audit):
        per = audit[scene]
        first = True
        for v in VAR_ORDER:
            r = per.get(v)
            if r is None:
                continue
            name = tex_name(scene) if first else ""
            first = False
            lines.append(
                f"{name} & {VAR_LABEL.get(v, v)} & {100 * r['stale_mean']:.1f} & "
                f"{100 * r['audit_mean']:.1f} & {r['audit_bias_pp']:+.1f} & "
                f"{100 * r['ks_cal_mean']:.1f} & {r['tightness_mean']:.2f} \\\\")
        if not first:
            lines.append("\\midrule")
    if lines and lines[-1] == "\\midrule":
        lines.pop()
    body = "\n".join(lines)
    tex = r"""\begin{table}[t]
\centering
\scriptsize
\caption{The audit on every asset$\times$edit cell. ``cov.'' is the true post-edit deployment
coverage under the shipped $q$ (\%); ``audit'' is equation~\eqref{eq:audit} evaluated on the
shipped calibration views (\%); ``err'' is audit minus coverage in points; $\mathrm{KS}$ is the
Kolmogorov distance between the pre- and post-edit residual distributions on the calibration
views (points); the last column is the coverage loss divided by $\mathrm{KS}$, so a value below
one means the envelope is conservative for that cell. Ground truth as captured, $\alpha=0.10$.}
\label{tab:audit}
\begin{tabular}{llrrrrr}
\toprule
Asset & edit & cov. & audit & err & KS & loss/KS \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    _emit(out_dir, "tab_audit.tex", tex)
    return len(lines)


def table_kview(audit, out_dir):
    ks = []
    for scene in audit:
        for v, r in audit[scene].items():
            kv = r.get("kview") or {}
            ks.append({k: d["mae_pp"] for k, d in kv.items() if d})
    if not ks:
        raise SystemExit("no kview data in audit_bound.json (rerun with --kviews)")
    keys = sorted({k for d in ks for k in d}, key=int)
    rows = []
    for k in keys:
        vals = [d[k] for d in ks if k in d]
        rows.append(f"{k} & {len(vals)} & ${np.mean(vals):.1f}$ & ${np.max(vals):.1f}$ \\\\")
    tex = r"""\begin{table}[t]
\centering
\scriptsize
\caption{Cost of an audit in shipped views: mean absolute error of
equation~\eqref{eq:audit} against the true post-edit coverage, when only $k$ of the available
calibration views are re-rendered. Cells are pooled over the asset$\times$edit grid.}
\label{tab:kview}
\begin{tabular}{rrrr}
\toprule
$k$ & cells & mean MAE (pp) & max MAE (pp) \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    _emit(out_dir, "tab_kview.tex", tex)
    return len(rows)


def table_fidelity(dump, audit, out_dir):
    lines = []
    for scene in sorted(dump):
        vs = dump[scene]
        clean = vs.get("clean", {})
        base_lp = clean.get("lpips")
        first = True
        for v in [None] + VAR_ORDER:
            key = "clean" if v is None else v
            st = vs.get(key)
            if st is None or st.get("psnr") is None:
                continue
            name = tex_name(scene) if first else ""
            first = False
            aud = audit.get(scene, {}).get(v) if v else None
            dpp = f"{100 * aud['drop_mean']:.1f}" if aud else "--"
            lp = st.get("lpips")
            dlp = (f"{lp - base_lp:+.3f}" if (lp is not None and base_lp is not None)
                   else "--")
            dpsnr = (f"{st['psnr'] - clean['psnr']:+.2f}"
                     if clean.get("psnr") is not None else "--")
            lines.append(f"{name} & {VAR_LABEL.get(v, 'fresh') if v else 'fresh'} & "
                         f"{st['psnr']:.2f} & {dpsnr} & {dpp} \\\\")
        lines.append("\\midrule")
    if lines and lines[-1] == "\\midrule":
        lines.pop()
    tex = r"""\begin{table}[t]
\centering
\scriptsize
\caption{Fidelity against the certificate on the very same renders. PSNR (dB) is the mean over
the held-out views of each asset; $\Delta$PSNR is against the fresh asset, so a negative value is a
fidelity loss; ``cov.\ drop'' is the per-pixel paired coverage drop of Table~\ref{tab:main}, in
points.}
\label{tab:fidelity}
\begin{tabular}{llrrr}
\toprule
Asset & edit & PSNR & $\Delta$PSNR & cov.\ drop \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    _emit(out_dir, "tab_fidelity.tex", tex)
    return len(lines)


def check(out_dir, min_rows=0):
    ok = True
    for name, must_have in [("tab_audit.tex", max(6, min_rows)),
                            ("tab_kview.tex", 2),
                            ("tab_fidelity.tex", max(6, min_rows))]:
        p = os.path.join(out_dir, name)
        if not os.path.exists(p):
            print(f"MISSING {name}")
            ok = False
            continue
        txt = open(p, encoding="utf-8").read()
        n = sum(1 for ln in txt.splitlines()
                if ln.rstrip().endswith("\\\\") and "&" in ln)
        print(f"{name}: {len(txt)} bytes, {n} data rows -> "
              f"{'OK' if n >= must_have else 'TOO FEW'}")
        ok &= n >= must_have
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--exclude", default="",
                    help="comma list of scenes to drop (e.g. a broken export)")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    if a.check:
        return check(a.out_dir)
    _, audit = load_audit(a.audit)
    dump = load_dump(a.dump)
    for s in [x.strip() for x in a.exclude.split(',') if x.strip()]:
        audit.pop(s, None)
        dump.pop(s, None)
    n1 = table_audit(audit, a.out_dir)
    n2 = table_kview(audit, a.out_dir)
    n3 = table_fidelity(dump, audit, a.out_dir)
    print(f"wrote tab_audit.tex ({n1} rows), tab_kview.tex ({n2}), "
          f"tab_fidelity.tex ({n3}) into {a.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
