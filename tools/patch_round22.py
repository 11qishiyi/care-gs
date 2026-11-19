# -*- coding: utf-8 -*-
"""Two additions that close stated gaps in the certificate report.

1. **SH degree reduction** (degree 3 -> 1) as a second *appearance* edit, next to
   the geometric pruning edits and the precision-only quantisation.  It drops the
   coefficient count from 16 to 4 per channel, which is a real compression step,
   but unlike pruning it does not move any geometry.

2. **Repair curve**: after pruning, how many calibration views are needed before
   the certificate is restored to the nominal level?  This turns "you must
   re-certify" into "you must re-certify with at least N views".
"""
import io

p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()

# --- 1. SH degree reduction -------------------------------------------------
s = s.replace('''def conformal_q(scores: np.ndarray, alpha: float) -> float:''',
'''def reduce_sh_degree(splats, keep_deg: int = 1):
    """Zero the SH coefficients above ``keep_deg`` (3 -> 1 keeps 4 of 16 coeffs)."""
    n_keep = (keep_deg + 1) ** 2 - 1
    if splats.shN is not None and splats.shN.shape[1] > n_keep:
        splats.shN = splats.shN.clone()
        splats.shN[:, n_keep:, :] = 0.0
    return splats


def conformal_q(scores: np.ndarray, alpha: float) -> float:''')

s = s.replace('''        edits = args.edits.split(",")
        if "quant8" in edits:''',
'''        edits = args.edits.split(",")
        if "shdeg1" in edits:
            d1 = reduce_sh_degree(load_splats(ply, device=args.device), keep_deg=1)
            row = evaluate(d1, "shdeg1")
            stale = float((residuals(d1, c2w, K, gt, dep, W, H, args.device)
                           .cpu().numpy().reshape(-1) <= base["q_pix"]).mean())
            row.update(stale_cov_pix=stale, drift_pix=float(row["cov_pix"] - base["cov_pix"]),
                       selfcheck_err_pix=float(row["pred_pix"] - row["cov_pix"]))
            rows.append(dict(scene=scene, edit="shdeg1", **row))
            print(f"  {'shdeg1':10s} stale={stale:.3f} recal={row['cov_pix']:.3f} "
                  f"[{row['ci_lo']:.3f},{row['ci_hi']:.3f}] "
                  f"drift={row['drift_pix']:+.3f} selfcheck_err={row['selfcheck_err_pix']:+.3f}",
                  flush=True)

        if "quant8" in edits:''')

# --- 2. repair curve --------------------------------------------------------
s = s.replace('''            print(f"  {row['edit']:10s} stale={stale_cov:.3f} recal={cov_pix_new:.3f} "''',
'''            if "repair" in edits:
                curve = []
                for n_cal in (2, 4, 6, 8, len(cal)):
                    if n_cal > len(cal):
                        continue
                    r_rc = residuals(pruned, c2w, K, gt, cal[:n_cal], W, H, args.device).cpu().numpy()
                    q_rc = conformal_q(r_rc.reshape(-1), alpha)
                    cov_rc = float((residuals(pruned, c2w, K, gt, dep, W, H, args.device)
                                    .cpu().numpy().reshape(-1) <= q_rc).mean())
                    curve.append(dict(n_cal=int(n_cal), cov_rc=cov_rc))
                row["repair_curve"] = curve
                print("    repair: " + "  ".join(f"n={c['n_cal']}:{c['cov_rc']:.3f}" for c in curve),
                      flush=True)
            print(f"  {row['edit']:10s} stale={stale_cov:.3f} recal={cov_pix_new:.3f} "''')

s = s.replace('ap.add_argument("--edits", default="prune50,prune30,quant8")',
              'ap.add_argument("--edits", default="prune50,prune30,quant8,shdeg1,repair")')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s)
print("added: SH degree reduction + repair curve")
