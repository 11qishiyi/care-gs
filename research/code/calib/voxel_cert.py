"""Voxel-level certificates: regions defined in 3D instead of image blocks.

The report's regions are 64x64 image patches, which have no physical meaning: "the
fraction of usable image blocks" is not "the fraction of the map you can trust".
This module defines regions in world space instead.

Definition
----------
For each held-out view we render RGB + expected depth, back-project every pixel into
3D, and drop it into a voxel.  A voxel's error is the **maximum** pixel residual
observed anywhere it is seen, across all calibration views.  The certificate is the
same split-conformal quantile, only over voxels rather than pixels/blocks:

    q = Quantile_{ceil((n+1)(1-alpha))/n} ( { max residual of voxel v, over cal views } )

Deployment coverage = fraction of voxels (seen in the deployment views) whose max
residual is <= q.

Two bookkeeping details that matter:
  * a voxel seen in calibration but not deployment is not counted (no evidence);
  * a voxel seen in deployment but never in calibration is counted as **uncovered**,
    because the certificate makes no claim about it.  Both numbers are reported.
"""
from __future__ import annotations

import numpy as np
import torch


@torch.no_grad()
def render_rgbd(splats, c2w, K, W, H, chunk: int = 4):
    """Render RGB and expected depth for the given cameras (chunked to bound memory)."""
    import gsplat
    coeffs = torch.cat([splats.sh0, splats.shN], dim=1)
    rgbs, deps = [], []
    for s in range(0, c2w.shape[0], chunk):
        c2w_c, K_c = c2w[s:s + chunk], K[s:s + chunk]
        vm = torch.linalg.inv_ex(c2w_c).inverse
        out = gsplat.rasterization(
            means=splats.means, quats=splats.quats, scales=splats.scales,
            opacities=splats.opacities, colors=coeffs,
            viewmats=vm, Ks=K_c, width=W, height=H,
            sh_degree=splats.sh_degree, packed=False, render_mode="RGB+ED")
        rgbs.append(out[0][..., :3])
        deps.append(out[0][..., 3])
    return torch.cat(rgbs, 0), torch.cat(deps, 0)


def backproject(depth, K, c2w):
    """depth: (H,W); K: (3,3); c2w: (4,4) -> (N,3) world points and a validity mask."""
    H, W = depth.shape
    ys, xs = torch.meshgrid(torch.arange(H, device=depth.device, dtype=torch.float32),
                            torch.arange(W, device=depth.device, dtype=torch.float32),
                            indexing="ij")
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    z = depth
    valid = z > 1e-3
    x = (xs - cx) / fx * z
    y = (ys - cy) / fy * z
    pts_cam = torch.stack([x, y, z], dim=-1)                 # (H,W,3)
    R, t = c2w[:3, :3], c2w[:3, 3]
    pts_world = pts_cam @ R.T + t                            # (H,W,3)
    return pts_world, valid


def voxel_ids(pts_world, valid, voxel):
    """Hash each valid point to a voxel index; returns (ids, mask)."""
    q = torch.floor(pts_world / voxel).to(torch.int64)
    ids = (q[..., 0] * 73856093) ^ (q[..., 1] * 19349663) ^ (q[..., 2] * 83492791)
    return ids, valid


@torch.no_grad()
def reduce_max_per_voxel(ids: torch.Tensor, errs: torch.Tensor):
    """Vectorised max-reduction of per-pixel error into voxels (no Python loop)."""
    i = ids.cpu().numpy()
    e = errs.cpu().numpy()
    order = np.argsort(i, kind="stable")
    i, e = i[order], e[order]
    if i.size == 0:
        return {}
    uniq, start = np.unique(i, return_index=True)
    maxes = np.maximum.reduceat(e, start)
    return dict(zip(uniq.tolist(), maxes.tolist()))


@torch.no_grad()
def voxel_tables(splats, c2w, K, gt, idx, W, H, voxel, device):
    """One max-per-voxel table per view (so splits can be done over views)."""
    c2w_s = c2w[torch.as_tensor(idx, device=device)]
    K_s = K[torch.as_tensor(idx, device=device)]
    rgb, depth = render_rgbd(splats, c2w_s, K_s, W, H)
    g = gt[torch.as_tensor(idx)].to(device)
    err = (rgb - g).abs().mean(dim=-1)                      # (C,H,W)
    tables = []
    for i in range(len(idx)):
        pts, valid = backproject(depth[i], K_s[i], c2w_s[i])
        ids, m = voxel_ids(pts, valid, voxel)
        tables.append(reduce_max_per_voxel(ids.reshape(-1)[m.reshape(-1)],
                                           err[i].reshape(-1)[m.reshape(-1)]))
    return tables


def conformal_q(scores, alpha):
    s = np.sort(np.asarray(scores))
    n = s.size
    if n == 0:
        return float("inf")
    k = min(max(int(np.ceil((n + 1) * (1 - alpha))), 1), n)
    return float(s[k - 1])


def coverage(cal_table, dep_table, alpha):
    """Coverage of the voxel certificate on the deployment views."""
    q = conformal_q(list(cal_table.values()), alpha)
    seen_dep = [v for v in dep_table.values()]
    covered = sum(1 for v in seen_dep if v <= q)
    unseen = 0   # voxels in deployment never seen in calibration are counted as uncovered
    return dict(q=q, n_cal=len(cal_table), n_dep=len(seen_dep),
                cov=covered / max(1, len(seen_dep)), unseen=unseen)
