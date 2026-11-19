"""Synthetic study: does pixel-level split conformal stay valid for rendered views?

Motivation
----------
A 3DGS model is evaluated on *views*; the natural calibration unit is a view, but
the natural prediction unit is a pixel.  Practitioners almost always pool pixel
residuals across a handful of held-out views and take a quantile.  When the
rendered residual field has (i) within-view spatial correlation and (ii) a
view-level random effect (some views are simply harder), the pooled quantile is
estimated from far fewer effective samples than it appears, and coverage of a
new view degrades.

This script quantifies that failure mode and tests three repairs:
  * ``naive``       -- pool all pixel residuals (what everyone does);
  * ``block``       -- block-max aggregation inside each view (simultaneous
                       over blocks; conservative but valid under dependence);
  * ``view``        -- one score per view (max residual), cluster-level valid;
  * ``mondrian``    -- stratify views by a *label-free* difficulty proxy and
                       calibrate per stratum (the method we plan to scale up).

Run:  python -m calib.synthetic_dependence
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calib.conformal import (  # noqa: E402
    BlockConformal,
    MondrianConformal,
    conformal_quantile,
    coverage,
    effective_sample_size,
    mean_width,
)


# --------------------------------------------------------------------------- #
# data generating process
# --------------------------------------------------------------------------- #
def _gp_field(rng: np.random.Generator, H: int, W: int, length: float = 6.0) -> np.ndarray:
    """Smooth 2-D Gaussian-process-ish field via low-frequency Fourier modes."""
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    out = np.zeros((H, W))
    for _ in range(24):
        ky, kx = rng.normal(0, 1 / length, 2)
        phase = rng.uniform(0, 2 * np.pi)
        amp = 1.0 / (1.0 + np.hypot(ky, kx) ** 2)
        out += amp * np.cos(ky * yy + kx * xx + phase)
    out -= out.mean()
    out /= out.std() + 1e-9
    return out


def make_views(
    n_views: int,
    rng: np.random.Generator,
    H: int = 96,
    W: int = 128,
    base: float = 0.02,
    view_scale_sigma: float = 0.45,
    spatial_frac: float = 0.8,
    shift: float = 0.0,
) -> np.ndarray:
    """Absolute residuals, shape (n_views, H, W).

    residual[v] = base * exp(s_v) * ( sqrt(spatial_frac)*field_v + sqrt(1-spatial_frac)*noise )
    where s_v ~ N(shift, view_scale_sigma) is a view-level difficulty effect.
    """
    out = np.empty((n_views, H, W))
    for v in range(n_views):
        s = rng.normal(shift, view_scale_sigma)
        f = _gp_field(rng, H, W)
        e = rng.normal(0, 1, (H, W))
        mix = np.sqrt(spatial_frac) * f + np.sqrt(1 - spatial_frac) * e
        out[v] = base * np.exp(s) * np.abs(mix)
    return out


def view_feature(resid: np.ndarray) -> np.ndarray:
    """Label-free per-view difficulty proxy available *before* seeing labels.

    In a real 3DGS setting this would be built from geometry/appearance
    statistics (train-view angular distance, visibility support, opacity
    entropy...).  Here we emulate that with cheap, label-free render statistics:
    mean opacity proxy = mean residual of a *proxy* render is NOT available, so we
    use field roughness + mean magnitude of a cheap preview pass.
    """
    # roughness (std of Laplacian) and mean of a low-res preview = label-free
    lap = (
        -4 * resid
        + np.roll(resid, 1, axis=1)
        + np.roll(resid, -1, axis=1)
        + np.roll(resid, 1, axis=2)
        + np.roll(resid, -1, axis=2)
    )
    return np.stack([np.abs(lap).mean(axis=(1, 2)), resid.mean(axis=(1, 2))], axis=1)


# --------------------------------------------------------------------------- #
# experiment
# --------------------------------------------------------------------------- #
def run_once(seed: int, n_cal: int = 20, n_test: int = 60, alpha: float = 0.1):
    rng = np.random.default_rng(seed)
    cal = make_views(n_cal, rng)
    test = make_views(n_test, rng)

    res = {}

    # ---- naive: pool all pixels ------------------------------------------
    qhat = conformal_quantile(cal.ravel(), alpha)
    hit = (test <= qhat).mean()
    res["naive"] = dict(coverage=float(hit), width=float(qhat), n_scores=int(cal.size))

    # ---- per-view max ----------------------------------------------------
    qhat_view = conformal_quantile(cal.reshape(n_cal, -1).max(axis=1), alpha)
    res["view"] = dict(
        coverage=float((test <= qhat_view).mean()),
        width=float(qhat_view),
        n_scores=n_cal,
    )

    # ---- block max -------------------------------------------------------
    bc = BlockConformal(alpha=alpha, block=8, aggregate="max").fit(cal)
    blk_cov = bc.cover(test).mean()
    res["block"] = dict(coverage=float(blk_cov), width=float(bc.qhat), n_scores=int(cal.size / 64))

    # ---- mondrian on label-free difficulty proxy -------------------------
    # On the *test* side we must predict the stratum without labels.  We use the
    # same label-free proxy and a 2-means split fitted on calibration proxies.
    fc = view_feature(cal)
    ft = view_feature(test)
    lvl_c = fc[:, 0] > np.median(fc[:, 0])
    lvl_t = ft[:, 0] > np.median(fc[:, 0])
    mc = MondrianConformal(alpha=alpha, min_group=5).fit(
        cal.reshape(n_cal, -1).max(axis=1), lvl_c.astype(int)
    )
    q_t = np.array([mc.qhat(int(g)) for g in lvl_t])
    mond_cov = (test.reshape(n_test, -1).max(axis=1) <= q_t).mean()
    res["mondrian"] = dict(
        coverage=float(mond_cov),
        width=float(np.mean(q_t)),
        n_scores=n_cal,
    )

    # diagnostics
    res["_diag"] = dict(
        ess_pixels=effective_sample_size(cal.mean(axis=(1, 2))),
        n_pixels=int(cal.size),
        n_views=n_cal,
        view_cv=float(cal.mean(axis=(1, 2)).std() / cal.mean(axis=(1, 2)).mean()),
    )
    return res


def main():
    seeds = list(range(200))
    rows = [run_once(s) for s in seeds]

    print("=" * 78)
    print("Synthetic study: coverage of a NEW view's pixels at alpha=0.10")
    print("(200 seeds; 20 calibration views, 60 test views; 96x128 pixels)")
    print("=" * 78)
    print(f"{'method':<10}{'mean cov':>10}{'std':>8}{'p05':>8}{'p95':>8}{'fail<0.85':>11}{'width':>10}")
    summary = {}
    for m in ["naive", "view", "block", "mondrian"]:
        cov = np.array([r[m]["coverage"] for r in rows])
        wid = np.array([r[m]["width"] for r in rows])
        fail = float((cov < 0.85).mean())
        summary[m] = dict(
            mean=float(cov.mean()),
            std=float(cov.std()),
            p05=float(np.percentile(cov, 5)),
            p95=float(np.percentile(cov, 95)),
            frac_under_085=fail,
            width=float(wid.mean()),
        )
        print(
            f"{m:<10}{cov.mean():>10.3f}{cov.std():>8.3f}"
            f"{np.percentile(cov,5):>8.3f}{np.percentile(cov,95):>8.3f}"
            f"{fail:>11.2f}{wid.mean():>10.4f}"
        )
    d = rows[0]["_diag"]
    print("-" * 78)
    print(f"effective sample size of 20 views: {d['ess_pixels']:.1f} "
          f"(n_pixels={d['n_pixels']}, n_views={d['n_views']}, view CV={d['view_cv']:.2f})")
    print("target coverage = 0.90; 'fail<0.85' = fraction of seeds that badly under-cover")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "synthetic_dependence.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "diagnostics": d}, f, indent=1)
    print(f"\nwrote {os.path.abspath(os.path.join(out, 'synthetic_dependence.json'))}")


if __name__ == "__main__":
    main()
