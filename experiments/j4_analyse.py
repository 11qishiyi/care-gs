"""J4 analysis — turns the sweep's per-view residuals into a coverage–rate table.

Runs wherever the npz files are (the node, typically) and prints/writes a small JSON:
for every (scene, configuration) it reports the rate, PSNR, the *shipped-quantile*
coverage of held-out pixels, the view-level coverage (fraction of views whose pixels are
at least 90 % covered), and the error of a k = 2 view audit.

The shipped quantile is calibrated once per scene on the **clean** model's calibration
views, which is what "the certificate that travelled with the asset" means; every
compressed row is then scored against that unchanged q, so a row's coverage is the
coverage a recipient would actually experience.

Usage on the node:
    python j4_analyse.py --npz /root/res/j4 --out /root/res/j4/j4_coverage.json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

ALPHA = 0.10
VIEW_COVER_TARGET = 0.90
AUDIT_K = 2
SEED = 0


def split_views(n_views: int, cal_frac: float, rng: np.random.Generator):
    idx = rng.permutation(n_views)
    n_cal = max(1, int(round(cal_frac * n_views)))
    n_cal = min(n_cal, n_views - 1)
    return np.sort(idx[:n_cal]), np.sort(idx[n_cal:])


def analyse_scene(path: Path, n_splits: int = 200) -> dict:
    z = np.load(path, allow_pickle=True)
    meta = json.loads(str(z["meta"]))
    variants = [str(v) for v in z["variant_names"]]
    resid = np.asarray(z["resid"], np.float32)          # (n_var, n_view, H, W)
    gray = np.asarray(z["gray_render"], np.float32)
    gt = np.asarray(z["gray_gt"], np.float32)
    n_var, n_view = resid.shape[0], resid.shape[1]
    cal_frac = float(meta.get("cal_frac", 0.5))

    # ---- per-variant PSNR on all held-out views (10*log10(1/ mse) on [0,1] grayscale)
    psnr = []
    for v in range(n_var):
        mse = float(np.mean((np.clip(gray[v], 0, 1) - np.clip(gt, 0, 1)) ** 2))
        psnr.append(float(10.0 * np.log10(1.0 / max(mse, 1e-12))))

    # ---- the shipped quantile: calibrated on the clean model's calibration views
    rng0 = np.random.default_rng(SEED)
    cal0, dep0 = split_views(n_view, cal_frac, rng0)
    q = float(np.quantile(resid[0][cal0].reshape(-1), 1.0 - ALPHA))

    rows = []
    for v in range(n_var):
        cov_pix, cov_view, audit_err = [], [], []
        for s in range(n_splits):
            rng = np.random.default_rng(SEED + 1000 + s)
            cal, dep = split_views(n_view, cal_frac, rng)
            ok_dep = resid[v][dep] <= q                       # (n_dep, H, W)
            cov_pix.append(float(ok_dep.mean()))
            per_view = ok_dep.reshape(ok_dep.shape[0], -1).mean(axis=1)
            cov_view.append(float(np.mean(per_view >= VIEW_COVER_TARGET)))
            pick = rng.choice(cal, size=min(AUDIT_K, len(cal)), replace=False)
            est = float(np.mean(resid[v][pick] <= q))
            audit_err.append(abs(est - cov_pix[-1]))
        rows.append({
            "variant": variants[v],
            "psnr": round(psnr[v], 2),
            "coverage_pixel": round(float(np.mean(cov_pix)), 4),
            "coverage_view": round(float(np.mean(cov_view)), 4),
            "pixel_minus_view_pp": round(100 * (float(np.mean(cov_pix)) - float(np.mean(cov_view))), 2),
            "audit_k2_mae_pp": round(100 * float(np.mean(audit_err)), 2),
        })
    return {"scene": meta.get("scene", path.stem), "n_views": n_view, "q": round(q, 5),
            "alpha": ALPHA, "view_target": VIEW_COVER_TARGET, "rows": rows,
            "n_splits": n_splits}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", default="/root/res/j4")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-splits", type=int, default=200)
    args = ap.parse_args()

    out = {"alpha": ALPHA, "view_target": VIEW_COVER_TARGET, "audit_k": AUDIT_K,
           "splits": args.n_splits, "scenes": []}
    for f in sorted(Path(args.npz).glob("*.npz")):
        r = analyse_scene(f, args.n_splits)
        out["scenes"].append(r)
        print(f"{r['scene']}: q={r['q']:.4f} views={r['n_views']}", flush=True)
        for row in r["rows"]:
            print(f"  {row['variant']:20s} psnr={row['psnr']:6.2f} pix={row['coverage_pixel']:.3f} "
                  f"view={row['coverage_view']:.3f} gap={row['pixel_minus_view_pp']:+6.2f}pp "
                  f"audit={row['audit_k2_mae_pp']:5.2f}pp", flush=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
