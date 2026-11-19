# -*- coding: utf-8 -*-
"""Add a label-free self-coverage diagnostic.

If the calibration views are exchangeable with the deployment views, then after an
edit the fraction of *calibration* residuals that still fall inside the old
interval estimates the fraction of *deployment* residuals that do -- without
touching any deployment label.  This turns "is my certificate still valid?" into
a number you can compute for free.
"""
import io
p = r"D:\3dsg_1\research\code\scripts\run_scene2.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace(
'''        r_dep_edit, f_dep_edit, _, _ = view_stats(s2, c2w, K, gt, dep_idx, W, H)
        cov_stale = float((r_dep_edit.cpu().numpy() <= q_clean).mean())''',
'''        r_cal_edit, f_cal_edit, _, _ = view_stats(s2, c2w, K, gt, cal_idx, W, H)
        r_dep_edit, f_dep_edit, _, _ = view_stats(s2, c2w, K, gt, dep_idx, W, H)
        cov_stale = float((r_dep_edit.cpu().numpy() <= q_clean).mean())
        # label-free diagnostic: self-coverage of the OLD interval on the
        # calibration views, after the edit
        cal_self = float((r_cal_edit.cpu().numpy() <= q_clean).mean())
        # label-free drift magnitude: how much did the calibration residuals move
        cal_shift = float(r_cal_edit.cpu().numpy().mean() - rec_zero_mean)''')

s = s.replace(
'''            stale=dict(cov=cov_stale, q_clean=float(q_clean)),''',
'''            stale=dict(cov=cov_stale, q_clean=float(q_clean),
                       cal_self_cov=cal_self, cal_resid_shift=cal_shift),''')

s = s.replace(
'''        print(f"[{e}] stale={cov_stale:.3f} recal={recal['naive']['cov']:.3f} "''',
'''        print(f"[{e}] stale={cov_stale:.3f} cal_self={cal_self:.3f} "
              f"recal={recal['naive']['cov']:.3f} "''')

# record the clean calibration residual mean for the shift computation
s = s.replace(
'''    q_clean = conformal_quantile(
        view_stats(splats, c2w, K, gt, cal_idx, W, H)[0].cpu().numpy().ravel(), args.alpha)''',
'''    _r_cal0, _, _, _ = view_stats(splats, c2w, K, gt, cal_idx, W, H)
    _r_cal0_np = _r_cal0.cpu().numpy()
    q_clean = conformal_quantile(_r_cal0_np.ravel(), args.alpha)
    rec_zero_mean = float(_r_cal0_np.mean())''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched run_scene2 with self-coverage diagnostic")
