"""A differentiable rate pressure for 3DGS fine-tuning (M36).

The container's rate is decided by zstd on quantised codes, which is not differentiable.  The surrogate
here is the log-domain entropy of a parameter group normalised by its own scale:

    R(θ) = mean( log2(1 + (θ/σ)²) )

* it is smooth, positive and increasing in |θ|, so gradient descent shrinks the parameter mass;
* it is *scale invariant*: replacing θ by cθ and σ by cσ leaves R unchanged, which is what makes it a
  statement about the *shape* of the distribution rather than about the units;
* shrinking the tail is exactly what lowers the entropy of the quantised codes, so it is the cheapest
  smooth stand-in for "spend fewer bits here".

The control that makes the experiment meaningful is L2 at the same weight: ``mean((θ/σ)²)``.  Plain
weight decay also shrinks parameters, and a round that only compares "rate term" against "nothing" cannot
tell the two apart.  Both are exposed here so train_gs.py can run either behind the same flag.

Everything is deliberately independent of the tensor library version: it takes torch tensors, returns a
scalar tensor, and has no other state.
"""
from __future__ import annotations

import torch

#: the parameter groups the container actually spends bytes on (means and quats are geometry, not rate)
DEFAULT_GROUPS = ("shN", "sh0", "scales", "opacities")


def group_scale(t: torch.Tensor, quantile: float = 0.5, factor: float = 1.5,
                max_samples: int = 1 << 22) -> torch.Tensor:
    """σ for one parameter group: ``factor`` times its median absolute value, floored.

    A median rather than a standard deviation: the SH rest coefficients are heavy-tailed, and a σ taken from
    the mean would be set by the few largest coefficients and leave the rest effectively free.

    Two things about the implementation were learned the hard way on the node:

    * the quantile tensor has to live on the parameter's device -- ``torch.quantile`` rejects a CPU ``q``
      for a CUDA input (`RuntimeError: quantile() q tensor must be on the same device as the input tensor`);
    * ``torch.quantile`` has a size limit (`RuntimeError: quantile() input tensor is too large`) and the SH
      rest group is 1,532,988 × 45 = 69 M elements, so the median is taken on a strided subsample of at most
      ``max_samples``.  A median of four million draws is the same median to three decimals, and σ is only
      ever used once, at initialisation.
    """
    with torch.no_grad():
        flat = t.detach().abs().flatten().float()
        if flat.numel() > max_samples:
            flat = flat[:: max(1, flat.numel() // max_samples)]
        q = torch.tensor(float(quantile), dtype=flat.dtype, device=flat.device)
        s = float(torch.quantile(flat, q))
    return torch.tensor(max(factor * s, 1e-8), dtype=t.dtype, device=t.device)


def rate_term(t: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
    """``mean(log2(1 + (t/scale)^2))`` — the smooth stand-in for a group's code entropy."""
    r = (t / scale) ** 2
    return torch.log2(1.0 + r).mean()


def shrink_term(t: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
    """``mean((t/scale)^2)`` — the control: the same pressure without the logarithm."""
    return ((t / scale) ** 2).mean()


def penalty(params: dict, scales: dict, groups=DEFAULT_GROUPS, kind: str = "log") -> torch.Tensor:
    """Sum of the per-group term over ``groups``.  ``kind`` is ``"log"`` (rate) or ``"l2"`` (control)."""
    fn = rate_term if kind == "log" else shrink_term
    total = None
    for g in groups:
        if g not in params or g not in scales:
            continue
        v = fn(params[g], scales[g])
        total = v if total is None else total + v
    if total is None:
        raise KeyError(f"no group of {groups} present in params ({sorted(params)})")
    return total / max(1, len(groups))


def calibrate_lambda(loss_grad_norm: float, rate_grad_norm: float, share: float = 0.05) -> float:
    """λ such that the rate term's gradient is ``share`` of the rendering loss's gradient norm.

    Fixed before the run and then frozen, so that the arm's λ cannot be chosen after seeing its PSNR.
    """
    if rate_grad_norm <= 0:
        raise ValueError("rate gradient norm must be positive")
    return float(share) * float(loss_grad_norm) / float(rate_grad_norm)
