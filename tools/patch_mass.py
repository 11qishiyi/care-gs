# -*- coding: utf-8 -*-
"""Add a per-Gaussian, mass-conserving compensation operator.

Global opacity gain is crude: the removed mass varies per pixel.  For each kept
Gaussian j we estimate the average removed alpha over the pixels it covers and
rescale its opacity so that accumulated coverage is restored locally.
"""
import io
p = r"D:\3dsg_1\research\code\scripts\compress_bench.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''# --------------------------------------------------------------------------- #
def main():''', '''@torch.no_grad()
def removed_mass_per_gaussian(kept: Splats, removed: Splats, c2w, K, idx, W, H):
    """Average alpha of the *removed* primitives over each kept splat's footprint."""
    import gsplat
    dev = kept.means.device
    idx_t = torch.as_tensor(idx, device=dev)
    a_out = render(removed, c2w[idx_t], K[idx_t], W, H)
    alpha_rm = a_out["alphas"].permute(0, 3, 1, 2)[:, 0]          # (n,H,W)
    vm = torch.linalg.inv_ex(c2w[idx_t]).inverse
    acc = torch.zeros(kept.n, device=dev)
    cnt = torch.zeros(kept.n, device=dev)
    for st in range(0, len(idx), 8):
        vm_s, K_s = vm[st:st + 8], K[idx_t][st:st + 8]
        radii, means2d, depths, _, _ = gsplat.fully_fused_projection(
            means=kept.means, covars=None, quats=kept.quats, scales=kept.scales,
            viewmats=vm_s, Ks=K_s, width=W, height=H, packed=False)
        u = means2d[..., 0].round().long().clamp(0, W - 1)
        v = means2d[..., 1].round().long().clamp(0, H - 1)
        for c in range(vm_s.shape[0]):
            gi = st + c
            if gi >= alpha_rm.shape[0]:
                break
            vis = radii[c, :, 0] > 0
            vals = alpha_rm[gi][v[c], u[c]]
            acc += torch.where(vis, vals, torch.zeros_like(vals))
            cnt += vis.float()
    return acc / cnt.clamp_min(1.0)


@torch.no_grad()
def compensate_mass(kept: Splats, removed: Splats, c2w, K, idx, W, H, max_gain=4.0):
    """Rescale each kept splat's opacity to restore the removed alpha mass."""
    m = removed_mass_per_gaussian(kept, removed, c2w, K, idx, W, H)
    gain = (1.0 / (1.0 - m.clamp(0, 0.95))).clamp(1.0, max_gain)
    o = kept.clone()
    o.opacities = (kept.opacities * gain).clamp(1e-4, 1 - 1e-4)
    return o, float(gain.mean())


# --------------------------------------------------------------------------- #
def main():''')

s = s.replace('''            if mname == "residual":
                spc, gain = compensate_opacity(sp, c2w, K, gt, cal, W, H)''',
'''            if mname == "residual":
                removed_mask = torch.ones(splats.n, dtype=torch.bool, device=splats.means.device)
                removed_mask[keep] = False
                sp_rm = splats.subset(torch.nonzero(removed_mask).flatten())
                spm, mgain = compensate_mass(sp, sp_rm, c2w, K, cal, W, H)
                pm, sm = evaluate(spm)
                rows.append(dict(method="residual+mass", ratio=r, n=k, psnr=pm, ssim=sm,
                                 gain=mgain))
                print(f"  {'res+mass':9s} r={r:.1f} n={k}: psnr={pm:.3f} ({pm-p0:+.3f}) "
                      f"ssim={sm:.4f}  mean_gain={mgain:.2f}", flush=True)
                spc, gain = compensate_opacity(sp, c2w, K, gt, cal, W, H)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched compress_bench with mass compensation")
