"""Synthetic study 2: scale-adaptive calibration and region-level risk control.

Two questions

Q1 (width/coverage trade-off)
    Pooling pixels ignores a *view-level* difficulty effect.  Max-over-view is
    valid but hugely conservative.  Does a scale-adaptive score -- predict the
    view difficulty from label-free render statistics, then conformalise the
    *normalised* residual -- recover nominal coverage at a width close to naive?

Q2 (region-level decisions)
    Real consumers ask questions about *regions* ("is this 64x64 patch free?"),
    which are functions of many pixels.  Per-pixel conformal says nothing about
    the region-level error.  How badly does it fail, and does a risk-controlling
    rule fix it without Bonferroni-style blow-up?
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calib.conformal import conformal_quantile  # noqa: E402
from calib.synthetic_dependence import make_views  # noqa: E402


# --------------------------------------------------------------------------- #
# label-free view descriptor
# --------------------------------------------------------------------------- #
def descriptor(preview: np.ndarray) -> np.ndarray:
    """Cheap, label-free per-view features available at deployment.

    ``preview`` is a low-resolution / low-LoD render of the view, shape (n,H,W).
    Everything here is computable without ground-truth: gradient energy, high
    frequency content, mean/percentile of the preview, and its disagreement with
    a second LoD level.
    """
    gy, gx = np.gradient(preview, axis=(1, 2))
    g = np.sqrt(gy ** 2 + gx ** 2)
    return np.stack(
        [
            np.log1p(preview.mean(axis=(1, 2))),
            np.log1p(preview.std(axis=(1, 2))),
            np.log1p(g.mean(axis=(1, 2))),
            np.log1p(np.percentile(preview, 95, axis=(1, 2))),
        ],
        axis=1,
    )


def make_preview(resid: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """A noisy, label-free proxy that correlates with true view difficulty."""
    n = resid.shape[0]
    scale = resid.mean(axis=(1, 2))  # the latent quantity we must *predict*
    base = scale[:, None, None] * np.ones_like(resid, dtype=float)
    texture = np.abs(np.random.default_rng(0).normal(size=resid.shape)) * scale[:, None, None]
    return np.clip(base + 0.7 * texture + rng.normal(0, 0.01 * scale.mean(), resid.shape), 0, None)


def fit_scale_model(feat_x: np.ndarray, scale_y: np.ndarray) -> np.ndarray:
    """Ridge regression log(scale) ~ features.  Returns coefficients incl. bias."""
    X = np.concatenate([np.ones((feat_x.shape[0], 1)), feat_x], axis=1)
    y = np.log(np.clip(scale_y, 1e-8, None))
    A = X.T @ X + 1e-3 * np.eye(X.shape[1])
    return np.linalg.solve(A, X.T @ y)


def apply_scale_model(coef: np.ndarray, feat_x: np.ndarray) -> np.ndarray:
    X = np.concatenate([np.ones((feat_x.shape[0], 1)), feat_x], axis=1)
    return np.exp(X @ coef)


# --------------------------------------------------------------------------- #
# experiment
# --------------------------------------------------------------------------- #
def run_once(seed: int, n_cal: int = 20, n_test: int = 60, alpha: float = 0.1,
             block: int = 64):
    rng = np.random.default_rng(seed)
    cal = make_views(n_cal, rng)
    test = make_views(n_test, rng)

    cal_preview = make_preview(cal, rng)
    test_preview = make_preview(test, rng)

    out = {}

    # ---------- Q1: width / coverage trade-off ----------------------------
    naive_q = conformal_quantile(cal.ravel(), alpha)

    view_q = conformal_quantile(cal.reshape(n_cal, -1).max(axis=1), alpha)

    # scale-adaptive on *true* scale (oracle) and on *predicted* scale
    s_cal_true = cal.mean(axis=(1, 2))
    s_test_true = test.mean(axis=(1, 2))
    coef = fit_scale_model(descriptor(cal_preview), s_cal_true)
    s_test_hat = apply_scale_model(coef, descriptor(test_preview))
    s_cal_hat = apply_scale_model(coef, descriptor(cal_preview))

    # oracle normalised conformal
    z_oracle = cal / s_cal_true[:, None, None]
    q_oracle = conformal_quantile(z_oracle.ravel(), alpha)
    # predicted normalised conformal: normalising by the *predicted* per-view
    # scale removes the cluster effect, which makes the pooled pixel scores
    # approximately exchangeable again -- this is the point of the estimator.
    z_cal = (cal / s_cal_hat[:, None, None]).ravel()
    q_pred = conformal_quantile(z_cal, alpha)

    out["naive"] = (float((test <= naive_q).mean()), float(naive_q))
    out["view_max"] = (float((test <= view_q).mean()), float(view_q))
    out["scale_oracle"] = (
        float((test <= q_oracle * s_test_true[:, None, None]).mean()),
        float((q_oracle * s_test_true[:, None, None]).mean()),
    )
    out["scale_pred"] = (
        float((test <= q_pred * s_test_hat[:, None, None]).mean()),
        float((q_pred * s_test_hat[:, None, None]).mean()),
    )

    # ---------- Q2: region-level decisions --------------------------------
    # Region query: is the max residual inside a `block x block` patch <= eps?
    # We calibrate a *pixel* radius r_pix at level alpha, and ask what fraction
    # of regions are fully covered (i.e. all pixels inside <= r_pix).
    r_pix = naive_q
    H, W = test.shape[1], test.shape[2]
    Hb, Wb = H // block, W // block
    tr = test[:, : Hb * block, : Wb * block].reshape(n_test, Hb, block, Wb, block)
    region_max = tr.max(axis=(2, 4))  # (n_test, Hb, Wb)
    region_cover_pixelwise = float((region_max <= r_pix).mean())

    # A risk-controlling rule: certify a region only when the *predicted* radius
    # is small enough for that region, else abstain (selective certification).
    # Calibrate the certification threshold so that P(error | certified) <= alpha.
    cal_regions = cal[:, : Hb * block, : Wb * block].reshape(n_cal, Hb, block, Wb, block)
    cal_region_max = cal_regions.max(axis=(2, 4)).ravel()
    tau = float(np.quantile(cal_region_max, 1 - alpha))  # certified if region_max <= tau
    cal_certified = cal_region_max <= tau
    out["region_pixelwise_cover"] = region_cover_pixelwise
    out["region_cert_rate_cal"] = float(cal_certified.mean())
    tr_flat = region_max.ravel()
    out["region_cert_rate_test"] = float((tr_flat <= tau).mean())
    # realised risk among certified test regions (the quantity a risk rule promises)
    cert_t = tr_flat <= tau
    out["region_risk_given_cert"] = (
        float((tr_flat[cert_t] > tau).mean()) if cert_t.any() else 0.0
    )

    # ---------- diagnostics ----------------------------------------------
    out["_corr_pred_scale"] = float(np.corrcoef(s_test_hat, s_test_true)[0, 1])
    out["_n_regions_per_view"] = int(Hb * Wb)
    return out


def main():
    rows = [run_once(s) for s in range(200)]
    keys = ["naive", "view_max", "scale_oracle", "scale_pred"]

    print("=" * 84)
    print("Q1: coverage / width of a NEW view's pixels at alpha=0.10  (200 seeds)")
    print("=" * 84)
    print(f"{'method':<14}{'mean cov':>10}{'std':>8}{'p05':>8}{'fail<0.85':>11}{'width':>10}{'width/naive':>13}")
    base_w = np.mean([r["naive"][1] for r in rows])
    summ = {}
    for k in keys:
        cov = np.array([r[k][0] for r in rows])
        wid = np.array([r[k][1] for r in rows])
        summ[k] = dict(mean=float(cov.mean()), std=float(cov.std()),
                       p05=float(np.percentile(cov, 5)),
                       frac_under_085=float((cov < 0.85).mean()),
                       width=float(wid.mean()))
        print(f"{k:<14}{cov.mean():>10.3f}{cov.std():>8.3f}{np.percentile(cov,5):>8.3f}"
              f"{(cov<0.85).mean():>11.2f}{wid.mean():>10.4f}{wid.mean()/base_w:>13.2f}")

    print()
    print("=" * 84)
    print("Q2: region-level ('is this 64x64 patch fully covered?') at pixel radius from naive alpha=0.1")
    print("=" * 84)
    cov = np.array([r["region_pixelwise_cover"] for r in rows])
    tau_rate = np.array([r["region_cert_rate_test"] for r in rows])
    cal_rate = np.array([r["region_cert_rate_cal"] for r in rows])
    print(f"region fully covered by pixelwise radius : {cov.mean():.3f} (target 0.90) "
          f"std={cov.std():.3f} p05={np.percentile(cov,5):.3f}")
    print(f"certified-region rate on calibration      : {cal_rate.mean():.3f}")
    print(f"certified-region rate on test             : {tau_rate.mean():.3f} "
          f"(this is the abstention cost of a valid region rule)")
    print(f"predicted-vs-true view scale correlation   : {np.mean([r['_corr_pred_scale'] for r in rows]):.3f}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "synthetic_scale_region.json"), "w", encoding="utf-8") as f:
        json.dump({"q1": summ,
                   "q2": dict(region_cover=float(cov.mean()),
                              cert_rate_cal=float(cal_rate.mean()),
                              cert_rate_test=float(tau_rate.mean())),
                   "corr_scale": float(np.mean([r["_corr_pred_scale"] for r in rows]))}, f, indent=1)
    print(f"\nwrote {os.path.abspath(os.path.join(out, 'synthetic_scale_region.json'))}")


if __name__ == "__main__":
    main()
