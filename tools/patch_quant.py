# -*- coding: utf-8 -*-
"""Add a quantisation edit (8-bit SH) to the certificate audit.

Pruning is not the only edit that invalidates a certificate: shipping a compressed
asset almost always means quantising the spherical-harmonic coefficients.  We add
an 8-bit-per-coefficient SH quantisation with a per-primitive, per-channel scale
(a standard compression step) and check whether the certificate survives it.
"""
import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''def conformal_q(scores: np.ndarray, alpha: float) -> float:''',
'''def quantize_sh(splats, bits: int = 8):
    """8-bit per-coefficient SH quantisation with per-primitive per-channel scale."""
    qmax = 2 ** (bits - 1) - 1
    for name in ("sh0", "shN"):
        t = getattr(splats, name)
        if t is None:
            continue
        scale = t.abs().amax(dim=(1, 2), keepdim=True).clamp_min(1e-8) / qmax
        tq = torch.round(t / scale).clamp(-qmax - 1, qmax) * scale
        setattr(splats, name, tq)
    return splats


def conformal_q(scores: np.ndarray, alpha: float) -> float:''')

old = '''        for ratio in (0.5, 0.3):
            k = max(1, int(round(ratio * splats.n)))
            keep = torch.argsort(-splats.opacities)[:k].sort().values
            pruned = splats.subset(keep)'''
new = '''        edits = args.edits.split(",")
        if "quant8" in edits:
            q8 = quantize_sh(load_splats(ply, device=args.device), bits=8)
            row = evaluate(q8, "quant8_sh")
            stale = float((residuals(q8, c2w, K, gt, dep, W, H, args.device)
                           .cpu().numpy().reshape(-1) <= base["q_pix"]).mean())
            row.update(stale_cov_pix=stale, drift_pix=float(row["cov_pix"] - base["cov_pix"]),
                       selfcheck_err_pix=float(row["pred_pix"] - row["cov_pix"]))
            rows.append(dict(scene=scene, edit="quant8_sh", **row))
            print(f"  {'quant8':10s} stale={stale:.3f} recal={row['cov_pix']:.3f} "
                  f"[{row['ci_lo']:.3f},{row['ci_hi']:.3f}] "
                  f"drift={row['drift_pix']:+.3f} selfcheck_err={row['selfcheck_err_pix']:+.3f}",
                  flush=True)

        for ratio in (0.5, 0.3):
            if f"prune{int(ratio*100)}" not in edits:
                continue
            k = max(1, int(round(ratio * splats.n)))
            keep = torch.argsort(-splats.opacities)[:k].sort().values
            pruned = splats.subset(keep)'''
assert old in s
s = s.replace(old, new)

s = s.replace('ap.add_argument("--cal_mode", default="hard", choices=["pooled", "hard"])',
              'ap.add_argument("--edits", default="prune50,prune30,quant8")\n'
              '    ap.add_argument("--cal_mode", default="pooled", choices=["pooled", "hard"])')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added 8-bit SH quantisation edit")
