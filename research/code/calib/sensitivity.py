"""PUP-style sensitivity score: a genuinely strong pruning baseline.

PUP 3D-GS ranks primitives by the diagonal of the Hessian of the rendering loss
(a Fisher approximation).  The cheap, widely used proxy is the squared gradient
magnitude accumulated over a handful of calibration views:

    score_i = sum_p  ( dL / d theta_{i,p} )^2

We compute it by actually back-propagating the photometric loss on a few
calibration views -- this is the strongest classical baseline for "which
primitive can I delete", and the number our task-aware allocation has to beat.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def sensitivity_scores(splats, c2w, K, gt, idx, W, H, n_views: int = 6, device="cuda"):
    """Accumulated squared gradient per primitive (Fisher-diagonal proxy)."""
    import gsplat

    means = splats.means.detach().clone().requires_grad_(True)
    scales = torch.log(splats.scales.detach().clamp_min(1e-8)).requires_grad_(True)
    quats = splats.quats.detach().clone().requires_grad_(True)
    opac = torch.logit(splats.opacities.detach().clamp(1e-6, 1 - 1e-6)).requires_grad_(True)
    sh0 = splats.sh0.detach().clone().requires_grad_(True)
    shN = splats.shN.detach().clone().requires_grad_(True)
    params = [means, scales, quats, opac, sh0, shN]
    acc = [torch.zeros_like(p) for p in params]

    pick = list(idx)[:n_views]
    for vi in pick:
        c2w_i = c2w[vi:vi + 1]
        K_i = K[vi:vi + 1]
        g = gt[vi:vi + 1].permute(0, 3, 1, 2).to(device)      # (1,3,H,W)
        coeffs = torch.cat([sh0, shN], dim=1)
        out = gsplat.rasterization(
            means=means, quats=F.normalize(quats, dim=-1), scales=torch.exp(scales),
            opacities=torch.sigmoid(opac), colors=coeffs, viewmats=torch.linalg.inv_ex(c2w_i).inverse,
            Ks=K_i, width=W, height=H, sh_degree=splats.sh_degree, packed=False)
        rgb = out[0].permute(0, 3, 1, 2)
        loss = (rgb - g).abs().mean()
        grads = torch.autograd.grad(loss, params, retain_graph=False, allow_unused=True)
        for a, p, gr in zip(acc, params, grads):
            if gr is not None:
                a += gr.detach() ** 2
        for p in params:
            p.grad = None
    score = sum(a.sum(dim=tuple(range(1, a.dim()))) for a in acc)   # (N,)
    return score.detach()
