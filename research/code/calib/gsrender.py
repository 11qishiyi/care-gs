"""Thin rendering / visibility wrapper around gsplat for calibration experiments.

Design
------
* load an INRIA-format 3DGS PLY (means, log-scales, quats, logit-opacities, SH);
* render a batch of cameras with the same call gsplat's ``simple_trainer`` uses,
  passing SH coefficients directly so the rasterizer does the SH evaluation
  (this keeps numbers comparable with the reference implementation);
* expose **per-Gaussian visibility per view**: exactly the signal the
  calibration-curation idea needs, and exactly what an implicit representation
  cannot hand you cheaply;
* no training logic -- calibration is a post-hoc property of a frozen model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch

import gsplat


@dataclass
class Splats:
    """3DGS parameters in the convention gsplat's rasterizer consumes."""

    means: torch.Tensor      # (N, 3)
    scales: torch.Tensor     # (N, 3)  actual (exp'd) scales
    quats: torch.Tensor      # (N, 4)  normalised
    opacities: torch.Tensor  # (N,)    actual (sigmoid'd) opacities
    sh0: torch.Tensor        # (N, 1, 3)
    shN: torch.Tensor        # (N, K-1, 3) or (N, 0, 3)

    def to(self, device, dtype=torch.float32) -> "Splats":
        return Splats(
            means=self.means.to(device=device, dtype=dtype),
            scales=self.scales.to(device=device, dtype=dtype),
            quats=self.quats.to(device=device, dtype=dtype),
            opacities=self.opacities.to(device=device, dtype=dtype),
            sh0=self.sh0.to(device=device, dtype=dtype),
            shN=self.shN.to(device=device, dtype=dtype),
        )

    def clone(self) -> "Splats":
        return Splats(self.means.clone(), self.scales.clone(), self.quats.clone(),
                      self.opacities.clone(), self.sh0.clone(), self.shN.clone())

    def subset(self, idx: torch.Tensor) -> "Splats":
        return Splats(self.means[idx], self.scales[idx], self.quats[idx],
                      self.opacities[idx], self.sh0[idx], self.shN[idx])

    @property
    def sh_degree(self) -> int:
        k = self.shN.shape[1] + 1
        return int(round(math.sqrt(k))) - 1

    @property
    def n(self) -> int:
        return int(self.means.shape[0])

    def nbytes(self) -> int:
        """Rough on-disk size in bytes (fp32 attributes + SH)."""
        per = (3 + 3 + 4 + 1 + 3 + self.shN.shape[1] * 3) * 4
        return self.n * per


def load_splats(ply_path: str, device="cuda") -> Splats:
    """Load an INRIA-format 3DGS PLY into :class:`Splats`."""
    try:
        d = gsplat.load_ply_to_splats(ply_path)
        _raw = True
    except AttributeError:
        from .plyio import load_inria_ply
        d = load_inria_ply(ply_path)
        _raw = False
    if _raw:
        scales = torch.exp(torch.as_tensor(d["scales"]).float())
        opacities = torch.sigmoid(torch.as_tensor(d["opacities"]).float())
        quats = torch.as_tensor(d["quats"]).float()
        sh0 = torch.as_tensor(d["sh0"]).float()
        shN = torch.as_tensor(d["shN"]).float()
    else:
        scales = torch.as_tensor(d["scales"]).float()
        opacities = torch.as_tensor(d["opacities"]).float()
        quats = torch.as_tensor(d["quats"]).float()
        sh0 = torch.as_tensor(d["sh0"]).float()
        shN = torch.as_tensor(d["shN"]).float()
    if sh0.dim() == 2:
        sh0 = sh0[:, None, :]
    quats = quats / quats.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    return Splats(means=torch.as_tensor(d["means"]).float(), scales=scales,
                  quats=quats, opacities=opacities, sh0=sh0, shN=shN).to(device)


@torch.no_grad()
def render(
    splats: Splats,
    camtoworlds: torch.Tensor,
    Ks: torch.Tensor,
    width: int,
    height: int,
    near: float = 0.01,
    far: float = 1e10,
    sh_degree: int | None = None,
    chunk: int = 2,
    render_mode: str = "RGB",
) -> dict:
    """Render cameras.

    Returns dict with ``colors`` (C,H,W,3), ``alphas`` (C,H,W,1) and, when
    ``render_mode`` contains ``ED``, ``depth`` (C,H,W,1).
    """
    device = splats.means.device
    camtoworlds = camtoworlds.to(device)
    Ks = Ks.to(device)
    viewmats = torch.linalg.inv_ex(camtoworlds).inverse
    deg = splats.sh_degree if sh_degree is None else min(sh_degree, splats.sh_degree)
    coeffs = torch.cat([splats.sh0, splats.shN], dim=1)  # (N,K,3)

    out_c, out_a, out_d = [], [], []
    for i in range(0, camtoworlds.shape[0], chunk):
        vm = viewmats[i: i + chunk]
        K = Ks[i: i + chunk]
        colors, alphas, info = gsplat.rasterization(
            means=splats.means,
            quats=splats.quats,
            scales=splats.scales,
            opacities=splats.opacities,
            colors=coeffs,
            viewmats=vm,
            Ks=K,
            width=width,
            height=height,
            near_plane=near,
            far_plane=far,
            sh_degree=deg,
            packed=False,
            render_mode=render_mode,
        )
        out_c.append(colors.cpu())
        out_a.append(alphas.cpu())
        del colors, alphas
        if "ED" in render_mode:
            out_d.append(out_c[-1][..., 3:4])
            out_c[-1] = out_c[-1][..., :3]
    res = {"colors": torch.cat(out_c, 0).to(device), "alphas": torch.cat(out_a, 0).to(device)}
    if out_d:
        res["depth"] = torch.cat(out_d, 0).to(device)
    return res


@torch.no_grad()
def visibility(
    splats: Splats,
    camtoworlds: torch.Tensor,
    Ks: torch.Tensor,
    width: int,
    height: int,
    near: float = 0.01,
) -> torch.Tensor:
    """Boolean (C, N): is primitive j inside the frustum of view c?

    True when the projected 2D radius is positive and the centre is in front of
    the near plane -- the same test the rasterizer uses to build tile lists.
    One projection pass, no ground-truth image required.
    """
    device = splats.means.device
    camtoworlds = camtoworlds.to(device)
    Ks = Ks.to(device)
    viewmats = torch.linalg.inv_ex(camtoworlds).inverse

    outs = []
    for i in range(0, camtoworlds.shape[0], 8):
        vm = viewmats[i: i + 8]
        K = Ks[i: i + 8]
        radii, means2d, depths, conics, comp = gsplat.fully_fused_projection(
            means=splats.means,
            covars=None,
            quats=splats.quats,
            scales=splats.scales,
            viewmats=vm,
            Ks=K,
            width=width,
            height=height,
            near_plane=near,
            packed=False,
        )
        outs.append(((radii[..., 0] > 0) & (depths > near)).reshape(vm.shape[0], -1))
    return torch.cat(outs, 0)


def image_to_tensor(img: np.ndarray, device="cuda") -> torch.Tensor:
    """uint8 HWC -> float CHW in [0,1]."""
    t = torch.as_tensor(np.ascontiguousarray(img)).to(device).float() / 255.0
    if t.dim() == 3 and t.shape[-1] in (3, 4):
        t = t[..., :3].permute(2, 0, 1)
    return t


def psnr(a: torch.Tensor, b: torch.Tensor) -> float:
    mse = torch.mean((a - b) ** 2).clamp_min(1e-12)
    return float(-10.0 * torch.log10(mse))

