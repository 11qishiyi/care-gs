# -*- coding: utf-8 -*-
"""Wire weighted conformal calibration into the certificate audit."""
import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace("from calib.colmap_io import load_images, normalize_exposure  # noqa: E402",
              "from calib.colmap_io import load_images, normalize_exposure  # noqa: E402\n"
              "from calib.weighted import view_covariates, density_ratios, weighted_quantile  # noqa: E402")

old = '''            r_use = r_cal
            if args.cal_mode == "hard":'''
new = '''            r_use = r_cal
            if args.cal_mode == "weighted":
                # label-free covariate: the renderer's own escape mass per view
                c_cal = view_covariates(sp, c2w, K, cal, W, H, args.device)
                c_dep = view_covariates(sp, c2w, K, dep, W, H, args.device)
                w_view = density_ratios(c_cal, c_dep)
                flat = r_cal.reshape(-1)
                view_of = np.repeat(np.arange(len(cal)), r_cal.shape[1] * r_cal.shape[2])
                q_pix = weighted_quantile(flat, view_of, w_view, alpha)
                print(f"    [weighted] covariate cal={c_cal.mean():.4f} dep={c_dep.mean():.4f} "
                      f"w_range=[{w_view.min():.2f},{w_view.max():.2f}]", flush=True)
            if args.cal_mode == "hard":'''
assert old in s
s = s.replace(old, new)

# q_pix is computed just above in the original code; make the weighted branch override it
s = s.replace('''            q_pix = conformal_q(r_use.reshape(-1), alpha)
            per_view_cov''', '''            if args.cal_mode != "weighted":
                q_pix = conformal_q(r_use.reshape(-1), alpha)
            per_view_cov''')

s = s.replace('choices=["pooled", "hard"])', 'choices=["pooled", "hard", "weighted"])')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("wired weighted conformal")
