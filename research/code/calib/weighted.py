"""Weighted conformal certificate for 3DGS assets.

Problem found empirically: a split-conformal certificate calibrated on our
calibration views over-covers the deployment views (0.944-0.988 against a nominal
0.90).  The cause is a covariate shift at the *view* level: calibration and
deployment views are not exchangeable, so the pooled quantile is systematically too
large, and that conservatism hides the degradation an edit causes.

Fix (Tibshirani et al. 2019, weighted conformal): reweight calibration scores by
the likelihood ratio between the deployment and calibration covariate
distributions, then take a weighted quantile.

The covariate must be computable *without labels* on both sets.  We use the
renderer's own escape mass, ``1 - T_final`` (the accumulated alpha), which says how
much of each ray the model fails to explain.  It is available for any view, needs
no ground truth, and correlates with how hard the view is.
"""
from __future__ import annotations

import numpy as np
import torch


@torch.no_grad()
def view_covariates(splats, c2w, K, idx, W, H, device):
    """Label-free per-view difficulty proxy: mean accumulated alpha (escape mass)."""
    from calib.gsrender import render
    it = torch.as_tensor(idx, device=device)
    out = render(splats, c2w[it], K[it], W, H)
    a = out["alphas"]                      # (m,H,W) accumulated alpha = 1 - T_final
    if a.dim() == 4:
        a = a[..., 0] if a.shape[-1] == 1 else a.mean(-1)
    return a.reshape(a.shape[0], -1).mean(dim=1).cpu().numpy()


def density_ratios(c_cal: np.ndarray, c_dep: np.ndarray) -> np.ndarray:
    """Estimate p_dep(x)/p_cal(x) on a 1-D covariate by logistic regression."""
    x = np.concatenate([c_cal, c_dep]).reshape(-1, 1)
    y = np.concatenate([np.zeros(len(c_cal)), np.ones(len(c_dep))])
    if len(np.unique(y)) < 2:
        return np.ones(len(c_cal))
    try:
        from sklearn.linear_model import LogisticRegression
        clf = LogisticRegression().fit(x, y)
        p_dep = clf.predict_proba(c_cal.reshape(-1, 1))[:, 1]
        p_cal = 1.0 - p_dep
        w = (p_dep / np.clip(p_cal, 1e-6, None)).astype(np.float64)
    except Exception:
        # fall back to a monotone reweighting by rank distance
        w = np.ones(len(c_cal), dtype=np.float64)
    w = np.clip(w, 0.05, 20.0)
    return w / w.mean()


def weighted_quantile(scores: np.ndarray, view_of: np.ndarray, w_view: np.ndarray,
                      alpha: float) -> float:
    """Weighted conformal quantile: smallest q with weighted mass >= 1-alpha."""
    w = w_view[view_of]
    order = np.argsort(scores)
    s, ww = scores[order], w[order]
    cw = np.cumsum(ww) / ww.sum()
    k = np.searchsorted(cw, 1 - alpha)
    k = min(k, len(s) - 1)
    return float(s[k])
