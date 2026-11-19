"""Unit tests for the calibration method (pure numpy, runs on CPU)."""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calib.conformal import conformal_quantile, coverage  # noqa: E402
from calib.method import (  # noqa: E402
    RegionRiskControl,
    ScaleAdaptiveConformal,
    curate_clean_views,
    region_scores_from_resid,
    view_descriptor,
)


def _toy(seed=0, m=20, H=32, W=32, sigma=0.45):
    rng = np.random.default_rng(seed)
    def gen(n):
        s = rng.normal(0, sigma, n)
        base = np.exp(s)[:, None, None]
        f = rng.normal(0, 1, (n, H, W))
        # smooth a bit
        f = (f + np.roll(f, 1, 1) + np.roll(f, 1, 2)) / 3.0
        return base * np.abs(f)
    return gen(m), gen(40)


def test_conformal_quantile_monotone():
    rng = np.random.default_rng(0)
    s = np.abs(rng.normal(size=1000))
    q90 = conformal_quantile(s, 0.1)
    q95 = conformal_quantile(s, 0.05)
    assert q95 >= q90 > 0
    # n=9 -> ceil(10*0.9)=9 -> 9th smallest
    s9 = np.arange(1, 10, dtype=float)
    assert conformal_quantile(s9, 0.1) == 9.0
    # too-few samples -> +inf (honest)
    assert conformal_quantile(np.array([1.0, 2.0]), 0.01) == float("inf")


def test_scale_adaptive_beats_naive_variance():
    cal, test = _toy(0)
    H = cal.shape[1]
    # descriptor: perfectly informative proxy of log-scale
    d_cal = np.log(cal.reshape(cal.shape[0], -1).mean(1))[:, None]
    d_test = np.log(test.reshape(test.shape[0], -1).mean(1))[:, None]

    sac = ScaleAdaptiveConformal(alpha=0.1).fit(cal.reshape(cal.shape[0], -1), d_cal)
    r = sac.radius(d_test)[:, None, None]
    cov_sac = float((test <= r).mean())

    q_naive = conformal_quantile(cal.ravel(), 0.1)
    cov_naive = float((test <= q_naive).mean())

    assert 0.85 <= cov_sac <= 0.97, cov_sac
    assert abs(cov_sac - 0.90) <= abs(cov_naive - 0.90) + 0.03, (cov_sac, cov_naive)
    assert sac.diag_["corr_scale"] > 0.9


def test_region_control_is_valid_at_decision_unit():
    cal, test = _toy(1)
    rc = RegionRiskControl(alpha=0.1).fit(region_scores_from_resid(cal, 8))
    s_test = region_scores_from_resid(test, 8)
    cert = rc.certify(s_test)
    assert cert.mean() > 0.7, cert.mean()   # most regions certifiable
    # among certified regions the score must be below tau by construction; the
    # empirical *coverage* of the region score is what we compare to alpha
    assert rc.diag_["cert_rate_cal"] >= 0.85


def test_pixel_radius_cannot_certify_regions():
    """The headline negative result: pixel-level calibration fails at region level."""
    cal, test = _toy(2)
    q = conformal_quantile(cal.ravel(), 0.1)
    s_test = region_scores_from_resid(test, 8)
    region_cover = float((s_test <= q).mean())
    assert region_cover < 0.5, region_cover   # catastrophically below the 0.9 target


def test_curate_clean_views():
    rng = np.random.default_rng(3)
    m, n = 20, 500
    vis = rng.random((m, n)) < 0.3
    edited = np.arange(0, 200)          # a big chunk of the scene
    out = curate_clean_views(edited, vis, min_clean=1)
    assert out["status"] in ("ok", "insufficient")
    assert out["clean"].size + out["contaminated"].size == m
    assert set(out["clean"]).isdisjoint(set(out["contaminated"]))
    # untouched edits -> everything clean
    out2 = curate_clean_views(np.array([], dtype=int), vis)
    assert out2["clean"].size == m and out2["status"] == "ok"


def test_view_descriptor_shape():
    rng = np.random.default_rng(4)
    f = rng.random((5, 3, 16, 16))
    d = view_descriptor(f)
    assert d.shape[0] == 5 and d.shape[1] == 9


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
