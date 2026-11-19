# -*- coding: utf-8 -*-
"""Tighten the certificate so the clean state is close to nominal coverage.

Observed problem: pooled conformal over all calibration views gives 0.944-0.988
coverage at a 0.90 nominal level, because the calibration views are systematically
easier than the deployment views.  A conservative certificate hides the very
degradation we want to measure.

Fix: calibrate on the *harder half* of the calibration views (a crude but
label-free covariate shift correction -- the deployment views we care about are
the harder ones).  We also expose a per-view Mondrian option.
"""
import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''            r_cal = residuals(sp, c2w, K, gt, cal, W, H, args.device).cpu().numpy()
            r_dep = residuals(sp, c2w, K, gt, dep, W, H, args.device).cpu().numpy()
            q_pix = conformal_q(r_cal.reshape(-1), alpha)''',
'''            r_cal = residuals(sp, c2w, K, gt, cal, W, H, args.device).cpu().numpy()
            r_dep = residuals(sp, c2w, K, gt, dep, W, H, args.device).cpu().numpy()
            r_use = r_cal
            if args.cal_mode == "hard":
                # keep only the harder half of the calibration views (higher median
                # residual); deployment views are systematically harder than the
                # average calibration view, and a certificate calibrated on easy
                # views is trivially conservative
                med = np.median(r_cal.reshape(len(r_cal), -1), axis=1)
                keep = np.argsort(-med)[: max(1, len(cal) // 2)]
                r_use = r_cal[keep]
            q_pix = conformal_q(r_use.reshape(-1), alpha)''')

s = s.replace("            q_blk = conformal_q(block_max(r_cal, args.block).reshape(-1), alpha)",
              "            q_blk = conformal_q(block_max(r_use, args.block).reshape(-1), alpha)")
s = s.replace('            pred_pix = float((r_cal.reshape(-1) <= q_pix).mean())',
              '            pred_pix = float((r_use.reshape(-1) <= q_pix).mean())')
s = s.replace('ap.add_argument("--device", default="cuda")',
              'ap.add_argument("--cal_mode", default="hard", choices=["pooled", "hard"])\n'
              '    ap.add_argument("--device", default="cuda")')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added hard-half calibration")
