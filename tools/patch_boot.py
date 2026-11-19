# -*- coding: utf-8 -*-
"""Add view-level bootstrap confidence intervals to the certificate audit.

With only ~10 deployment views the *effective* sample size for a coverage claim is
the number of views, not the number of pixels.  Reporting a point estimate without
a view-level interval overstates the evidence, so we resample views with
replacement and report the 2.5/97.5 percentiles for both the clean coverage and
the post-edit drop.
"""
import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''def block_max(r: np.ndarray, blk: int) -> np.ndarray:''',
'''def bootstrap_ci(per_view_cov: np.ndarray, n_boot: int = 2000, seed: int = 0):
    """View-level bootstrap CI for a coverage estimate."""
    rng = np.random.default_rng(seed)
    n = per_view_cov.size
    if n == 0:
        return (float("nan"), float("nan"))
    means = rng.choice(per_view_cov, size=(n_boot, n), replace=True).mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def block_max(r: np.ndarray, blk: int) -> np.ndarray:''')

s = s.replace('''            q_pix = conformal_q(r_use.reshape(-1), alpha)''',
'''            q_pix = conformal_q(r_use.reshape(-1), alpha)
            per_view_cov = (r_dep <= q_pix).reshape(len(r_dep), -1).mean(axis=1)
            ci_lo, ci_hi = bootstrap_ci(per_view_cov)''')

s = s.replace('''            return dict(tag=tag, n=int(sp.n), q_pix=q_pix, q_blk=q_blk,
                        cov_pix=cov_pix, cov_blk=cov_blk, pred_pix=pred_pix,
                        cal_med=float(np.median(r_cal)), dep_med=float(np.median(r_dep)))''',
'''            return dict(tag=tag, n=int(sp.n), q_pix=q_pix, q_blk=q_blk,
                        cov_pix=cov_pix, cov_blk=cov_blk, pred_pix=pred_pix,
                        ci_lo=ci_lo, ci_hi=ci_hi, n_dep=int(len(r_dep)),
                        cal_med=float(np.median(r_cal)), dep_med=float(np.median(r_dep)))''')

s = s.replace('''        print(f"  clean: pix cov={base['cov_pix']:.3f} blk cov={base['cov_blk']:.3f} "
              f"(nominal {1-alpha:.2f})  q_pix={base['q_pix']:.4f}", flush=True)''',
'''        print(f"  clean: pix cov={base['cov_pix']:.3f} "
              f"[{base['ci_lo']:.3f},{base['ci_hi']:.3f}] blk={base['cov_blk']:.3f} "
              f"(nominal {1-alpha:.2f}, dep views={base['n_dep']})", flush=True)''')

s = s.replace('''            print(f"  {row['edit']:10s} stale={stale_cov:.3f} recal={cov_pix_new:.3f} "
                  f"drift={row['drift_pix']:+.3f} selfcheck_err={row['selfcheck_err_pix']:+.3f}",
                  flush=True)''',
'''            print(f"  {row['edit']:10s} stale={stale_cov:.3f} recal={cov_pix_new:.3f} "
                  f"[{new['ci_lo']:.3f},{new['ci_hi']:.3f}] "
                  f"drift={row['drift_pix']:+.3f} selfcheck_err={row['selfcheck_err_pix']:+.3f}",
                  flush=True)''')

s = s.replace('ap.add_argument("--max_views", type=int, default=12)',
              'ap.add_argument("--max_views", type=int, default=40)')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added view-level bootstrap CIs; use all test views")
