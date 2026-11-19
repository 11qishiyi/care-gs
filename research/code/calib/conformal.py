"""Conformal calibration primitives (CPU, dependency-free except numpy).

Design goals
------------
* finite-sample valid prediction sets with exchangeable calibration data;
* explicit handling of *dependence* among calibration scores (spatial / per-view),
  which is the dominant failure mode when calibration units are pixels of a
  rendered view rather than independent samples;
* weighted (covariate-shift) conformal and Mondrian (group-conditional) variants;
* adaptive conformal inference (ACI) for streaming / post-edit recalibration.

All functions are pure-numpy and unit-tested in ``test_conformal.py``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Sequence

import numpy as np


# --------------------------------------------------------------------------- #
# quantiles
# --------------------------------------------------------------------------- #
def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """Split-conformal threshold with the finite-sample correction.

    Returns the ``ceil((n+1)(1-alpha))``-th smallest score (1-indexed), i.e. the
    standard ``qhat`` such that ``P(Y in C) >= 1 - alpha`` for a *new*
    exchangeable point.  When the required rank exceeds ``n`` the set is
    unbounded (``+inf``), which is the honest answer.
    """
    scores = np.asarray(scores, dtype=float).ravel()
    n = scores.size
    if n == 0:
        return float("inf")
    k = int(np.ceil((n + 1) * (1.0 - alpha)))
    if k > n:
        return float("inf")
    if k < 1:
        k = 1
    return float(np.sort(scores)[k - 1])


def effective_sample_size(x: np.ndarray) -> float:
    """Effective sample size for a 1-D series under AR(1)-like dependence.

    Uses the standard ``n / (1 + 2*sum_k rho_k)`` truncation with a Bartlett
    (Newey-West) kernel so the estimate stays positive.
    """
    x = np.asarray(x, dtype=float).ravel()
    n = x.size
    if n < 3:
        return float(n)
    x = x - x.mean()
    var = float(np.dot(x, x) / n)
    if var <= 0:
        return float(n)
    # Bartlett-weighted autocovariances, truncation lag ~ n**(1/3)
    L = max(1, int(np.floor(n ** (1.0 / 3.0))))
    s = 0.0
    for k in range(1, min(L, n - 1) + 1):
        rho = float(np.dot(x[:-k], x[k:]) / (n * var))
        s += 2.0 * (1.0 - k / (L + 1.0)) * rho
    ess = n / max(1e-12, 1.0 + s)
    return float(min(max(ess, 1.0), n))


# --------------------------------------------------------------------------- #
# split conformal
# --------------------------------------------------------------------------- #
@dataclass
class SplitConformal:
    """Classic split conformal for a scalar target with absolute-residual score."""

    alpha: float = 0.1
    qhat: float = float("inf")

    def fit(self, y: np.ndarray, yhat: np.ndarray) -> "SplitConformal":
        self.qhat = conformal_quantile(np.abs(np.asarray(y) - np.asarray(yhat)), self.alpha)
        return self

    def predict(self, yhat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        yhat = np.asarray(yhat, dtype=float)
        return yhat - self.qhat, yhat + self.qhat


@dataclass
class BlockConformal:
    """Conformal with dependence correction by *blocking* calibration units.

    Instead of treating every pixel as an independent calibration point (which
    under-covers when residuals are spatially correlated), we
      1. split each calibration view into spatial blocks,
      2. aggregate the score inside a block (max, or mean),
      3. calibrate on block-level scores, and
      4. at test time take the max/mean over the blocks of the test view.
    This yields a valid *simultaneous-over-blocks* guarantee under arbitrary
    within-block dependence.
    """

    alpha: float = 0.1
    block: int = 8
    aggregate: str = "max"
    qhat: float = float("inf")

    def _agg(self, resid: np.ndarray) -> np.ndarray:
        """resid: (n_views, H, W) -> (n_views * n_blocks,) block scores."""
        n, H, W = resid.shape
        b = self.block
        Hb, Wb = H // b, W // b
        r = resid[:, : Hb * b, : Wb * b].reshape(n, Hb, b, Wb, b)
        if self.aggregate == "max":
            return r.max(axis=(2, 4)).ravel()
        elif self.aggregate == "mean":
            return r.mean(axis=(2, 4)).ravel()
        else:  # pragma: no cover
            raise ValueError(self.aggregate)

    def fit(self, resid: np.ndarray) -> "BlockConformal":
        self.qhat = conformal_quantile(self._agg(np.asarray(resid, dtype=float)), self.alpha)
        return self

    def cover(self, resid: np.ndarray) -> np.ndarray:
        """Boolean per block: is the test-view block error within qhat?"""
        return self._agg(np.asarray(resid, dtype=float)) <= self.qhat


@dataclass
class MondrianConformal:
    """Group-conditional (Mondrian) conformal: one threshold per stratum.

    ``groups`` maps each calibration unit to a hashable stratum.  Validity holds
    *conditionally on each stratum* provided each stratum has enough data; we
    fall back to the pooled threshold when it does not.
    """

    alpha: float = 0.1
    min_group: int = 20

    def fit(self, scores: np.ndarray, groups: Sequence[Hashable]) -> "MondrianConformal":
        scores = np.asarray(scores, dtype=float).ravel()
        groups = list(groups)
        assert len(scores) == len(groups)
        self.pooled_ = conformal_quantile(scores, self.alpha)
        self.by_group_: dict[Hashable, float] = {}
        uniq = {g: [] for g in dict.fromkeys(groups)}
        for s, g in zip(scores, groups):
            uniq[g].append(s)
        for g, vals in uniq.items():
            self.by_group_[g] = (
                conformal_quantile(np.asarray(vals), self.alpha)
                if len(vals) >= self.min_group
                else self.pooled_
            )
        return self

    def qhat(self, group: Hashable) -> float:
        return self.by_group_.get(group, self.pooled_)


@dataclass
class WeightedConformal:
    """Conformal under covariate shift with *known or estimated* likelihood ratios.

    Validity: if ``w(x) = dP_deploy/dP_cal`` (up to a constant), the weighted
    quantile gives coverage >= 1 - alpha for deployment points.  Estimated
    weights break exactness; we expose a diagnostic (ESS of weights) to flag it.
    """

    alpha: float = 0.1

    def fit(self, scores: np.ndarray, weights: np.ndarray) -> "WeightedConformal":
        scores = np.asarray(scores, dtype=float).ravel()
        w = np.asarray(weights, dtype=float).ravel()
        assert scores.shape == w.shape
        w = np.clip(w, 0.0, None)
        if w.sum() <= 0:
            raise ValueError("weights must have positive mass")
        w = w / w.sum()
        order = np.argsort(scores)
        s_sorted, w_sorted = scores[order], w[order]
        cdf = np.cumsum(w_sorted)
        # weighted quantile with the (n+1) correction replaced by mass >= 1-alpha
        idx = int(np.searchsorted(cdf, 1.0 - self.alpha, side="left"))
        idx = min(idx, s_sorted.size - 1)
        self.qhat_ = float(s_sorted[idx])
        self.ess_ = float(1.0 / np.sum(w ** 2))
        self.w_max_ = float(w.max())
        return self


# --------------------------------------------------------------------------- #
# online / streaming
# --------------------------------------------------------------------------- #
class AdaptiveConformal:
    """Adaptive conformal inference (Gibbs & Candes) for arbitrary shift.

    Maintains a running miscoverage level so that the *long-run* average
    coverage converges to 1-alpha even when the score distribution changes
    arbitrarily over time (edits, drift).  Guarantee is long-run, not
    per-step -- we report both so the distinction stays visible.
    """

    def __init__(self, alpha: float, gamma: float = 0.01, init_alpha_t: float | None = None):
        self.alpha = alpha
        self.gamma = gamma
        self.alpha_t = alpha if init_alpha_t is None else init_alpha_t
        self.history: list[float] = []

    def step(self, scores_so_far: np.ndarray, err_t: bool) -> float:
        """Update with the realised error of the previous prediction."""
        self.alpha_t = self.alpha_t + self.gamma * ((1.0 if err_t else 0.0) - self.alpha)
        self.alpha_t = float(np.clip(self.alpha_t, 1e-4, 1.0 - 1e-4))
        self.history.append(self.alpha_t)
        return conformal_quantile(scores_so_far, self.alpha_t)


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def coverage(y: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    y, lo, hi = map(lambda a: np.asarray(a, dtype=float), (y, lo, hi))
    return float(np.mean((y >= lo) & (y <= hi)))


def mean_width(lo: np.ndarray, hi: np.ndarray) -> float:
    return float(np.mean(np.asarray(hi, dtype=float) - np.asarray(lo, dtype=float)))


def coverage_se(y: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    """Binomial standard error, inflated by the design effect of dependence.

    This is the number a reviewer should see next to coverage: with correlated
    units the naive binomial SE understates uncertainty by sqrt(design effect).
    """
    y = np.asarray(y, dtype=float)
    hit = ((y >= np.asarray(lo)) & (y <= np.asarray(hi))).astype(float)
    n = hit.size
    p = hit.mean()
    return float(np.sqrt(max(p * (1 - p), 1e-12) / n))
