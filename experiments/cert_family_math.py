"""Feasibility arithmetic for the "certificate for an edit family" construction (exploration item 3).

No data needed: this asks, for plausible residual shapes, how much tightness the *constructive* route costs
compared with the empirical envelope the paper already ships.

Two objects are compared, for residuals e (clean per-pixel error), an edit-induced per-pixel change delta, and a
threshold q at the (1-alpha) conformal quantile of e:

  V1 (threshold re-issue, valid by a union bound)
      Pr(e + delta <= q + Delta_beta) >= 1 - alpha - beta,  Delta_beta = (1-beta) quantile of |delta|.
      Cost: the certified threshold moves from q to q + Delta_beta.

  V2 (loss at the *unchanged* q, what the paper actually ships)
      coverage(q) >= F_cal(q - Delta_beta) - KS - eps.
      Cost: F_cal(q - Delta) falls exponentially in Delta for light tails, so the bound can be several times the
      true loss. This script measures that factor.

Reported: Delta/q, the inflated threshold, the true loss, the V2 bound, and bound/true.

    python experiments/cert_family_math.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

RNG = np.random.default_rng(20261118)
N = 2_000_000
ALPHA, BETA = 0.10, 0.10
OUT = Path("experiments/artifacts/a4/cert_family_math.json")


def draw(name: str) -> np.ndarray:
    if name == "exponential":
        return RNG.exponential(1.0, N)
    if name == "lognormal_s1":
        return RNG.lognormal(0.0, 1.0, N)
    if name == "lognormal_s0.5":
        return RNG.lognormal(0.0, 0.5, N)
    if name == "pixel_mix":                      # 85 % well-fit pixels, 15 % hard pixels
        hard = RNG.random(N) < 0.15
        e = RNG.exponential(0.6, N)
        e[hard] = RNG.lognormal(1.0, 0.8, hard.sum())
        return e
    raise ValueError(name)


def q_conformal(x: np.ndarray, level: float) -> float:
    """Split-conformal quantile: ceil((n+1)*level)/n order statistic."""
    n = x.size
    k = int(np.ceil((n + 1) * level))
    return float(np.partition(x, min(k, n) - 1)[min(k, n) - 1])


def main() -> None:
    rows = []
    for name in ("exponential", "lognormal_s0.5", "lognormal_s1", "pixel_mix"):
        e = draw(name)
        q = q_conformal(e, 1 - ALPHA)
        mu = float(e.mean())
        for s in (0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5):
            delta = np.abs(RNG.normal(0.0, s * mu, N))         # edit-induced change, scale s * mean residual
            d_beta = q_conformal(delta, 1 - BETA)
            edited = e + delta
            true_cov_at_q = float(np.mean(edited <= q))         # what the recipient actually experiences
            true_cov_at_new = float(np.mean(edited <= q + d_beta))
            v2_bound = float(np.mean(e <= q - d_beta))          # F_cal(q - Delta), no KS term yet
            rows.append(dict(dist=name, s=round(s, 3), q=round(q, 4), mean_resid=round(mu, 4),
                             delta_beta=round(d_beta, 4), delta_over_q=round(d_beta / q, 3),
                             threshold_inflation_x=round((q + d_beta) / q, 3),
                             true_cov_at_q=round(true_cov_at_q, 4),
                             true_cov_at_new=round(true_cov_at_new, 4),
                             v1_floor=round(1 - ALPHA - BETA, 3),
                             v2_loss_bound_pp=round(100 * (1 - v2_bound), 2),
                             v2_true_loss_pp=round(100 * (1 - true_cov_at_q), 2),
                             v2_over_true=(round((1 - v2_bound) / max(1e-9, 1 - true_cov_at_q), 2)
                                           if true_cov_at_q < 1 else None)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{'dist':14s} {'s':>5s} {'D/q':>6s} {'thr x':>6s} {'V2 bound':>9s} {'V2 true':>8s} {'ratio':>6s}")
    for r in rows:
        print(f"{r['dist']:14s} {r['s']:5.2f} {r['delta_over_q']:6.2f} {r['threshold_inflation_x']:6.2f} "
              f"{r['v2_loss_bound_pp']:9.1f} {r['v2_true_loss_pp']:8.1f} {str(r['v2_over_true']):>6s}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
