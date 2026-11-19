# -*- coding: utf-8 -*-
"""Fix: importance ranking sign, and record the edit's residual footprint."""
import io
p = r"D:\3dsg_1\research\code\scripts\sel_sweep.py"
s = io.open(p, encoding="utf-8").read()

# sign fix: keep HIGH-importance primitives when lam -> 1
s = s.replace("imp_n = _rank(-imp.cpu().numpy().astype(np.float64)) / max(1, splats.n - 1)",
              "imp_n = _rank(imp.cpu().numpy().astype(np.float64)) / max(1, splats.n - 1)")

# record the residual footprint of the removed set: mean alpha mass of removed
# primitives over calibration pixels (label-free, one extra render)
s = s.replace('''        # diagnostic: rank agreement between the edit criterion and the residual
        # contribution, on the *kept* set
        kept_app = app_n[keep_ids.cpu().numpy()]
        kept_imp = imp_n[keep_ids.cpu().numpy()]
        rho = float(np.corrcoef(kept_app, kept_imp)[0, 1])''',
'''        # diagnostic: rank agreement between the edit criterion and the residual
        # contribution, on the *kept* set
        kept_app = app_n[keep_ids.cpu().numpy()]
        kept_imp = imp_n[keep_ids.cpu().numpy()]
        rho = float(np.corrcoef(kept_app, kept_imp)[0, 1])

        # residual footprint: how much of the calibration image the removed
        # primitives actually covered (label-free, one render)
        removed_mask = torch.ones(splats.n, dtype=torch.bool, device=splats.means.device)
        removed_mask[keep_ids] = False
        removed = splats.subset(torch.nonzero(removed_mask).flatten())
        fp = 0.0
        if removed.n > 0:
            a = render(removed, c2w[torch.as_tensor(cal_idx, device=splats.means.device)],
                       K[torch.as_tensor(cal_idx, device=splats.means.device)], W, H,
                       render_mode="RGB")["alphas"]
            fp = float(a.mean())''')

s = s.replace('''                   sel_corr=rho)''', '''                   sel_corr=rho, footprint=fp)''')
s = s.replace('''              f"region={region_cert:.3f} resid_cal={r_cal.mean():.4f} sel_corr={rho:+.3f}",''',
              '''              f"region={region_cert:.3f} resid_cal={r_cal.mean():.4f} "
              f"sel_corr={rho:+.3f} footprint={fp:.4f}",''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched sel_sweep")
