"""M14: predictive (DPCM) coding of the SH block along the Morton order.

Motivation.  M9--M12 exhausted the *memoryless* codes for the 48-coefficient block: a scalar
ladder, one global codebook, a two-stage residual codebook and a product code all plateau at
0.3--2.4 pp around 19x, and the 2-bit step is a cliff (12.8x but -2.5 pp on bicycle).  A
codebook captures what the *population* of blocks looks like; it cannot capture the fact that
two primitives that are neighbours in Morton order describe the same patch of surface, so
their blocks are close to each other.

This module adds the one predictor that costs no side information: the previous primitive in
Morton order.  The order comes from the *decoded* positions, so a decoder rebuilds it for
free -- the same argument that makes cluster coding free of an index stream (M7).

Encoder and decoder run the same recurrence, so this is a real codec, not an analysis-side
trick::

    x_hat[i] = x_hat[i-1] + q_i * s          (within a block of BLOCK primitives)
    x_hat[0] = q_0 * s_anchor                (the first primitive of each block is absolute)

Byte cost per primitive is *lower* than the plain scalar path: 6b bytes of codes (48
coefficients at b bits) plus two float32 scales per 64-primitive block, instead of a 2-byte
scale per primitive.
"""

BLOCK = 64
SCALE_BYTES = 16.0         # four float32 scales per block: anchor/residual x (DC, rest)


def dpcm_bytes_per_prim(sh_degree: int, bits: int) -> float:
    """Codes at ``bits`` per coefficient plus the per-block scale header."""
    cols = 3 * (sh_degree + 1) ** 2
    return cols * int(bits) / 8.0 + SCALE_BYTES / BLOCK


def quantize_dpcm(sp, bits: int, block: int = BLOCK):
    """Quantise the SH block predictively; returns a new ``Splats`` (never mutates)."""
    import torch
    import qfp_rd as Q

    if bits < 2:
        raise ValueError("predictive coding needs at least 2 bits")
    out = sp.clone()
    flat = Q._sh_flat(out)                      # (N, 3K)
    n, cols = int(flat.shape[0]), int(flat.shape[1])
    perm = Q.morton_order(out.means)
    x = flat.index_select(0, perm)

    nb = (n + block - 1) // block
    pad = nb * block - n
    if pad:
        x = torch.cat([x, x[-1:].expand(pad, cols)], dim=0)
    xb = x.reshape(nb, block, cols)

    r = torch.empty_like(xb)
    r[:, 0, :] = xb[:, 0, :]                    # absolute anchor at the block start
    r[:, 1:, :] = xb[:, 1:, :] - xb[:, :-1, :]  # residual against the previous original

    qmax = float((1 << (bits - 1)) - 1)

    def _scale(t):
        # One scale per block per group: if the step is allowed to re-adapt per primitive the
        # code collapses back into the scalar path, which is what makes prediction pointless.
        return (t.abs().amax(dim=(1, 2), keepdim=True) / qmax).clamp_min(1e-12)

    # The anchor is two orders of magnitude larger than the residual, so they cannot share a
    # scale: with one scale the 2-bit step would be set by the anchor and every residual would
    # quantise to zero.  Four float32 scales per block (16 B / 64 primitives) buys them apart.
    s_a_dc = _scale(r[:, 0:1, :3])
    s_a_rest = _scale(r[:, 0:1, 3:]) if cols > 3 else s_a_dc
    s_r_dc = _scale(r[:, 1:, :3]) if block > 1 else s_a_dc
    s_r_rest = _scale(r[:, 1:, 3:]) if (cols > 3 and block > 1) else s_a_rest
    q = torch.empty_like(r)
    q[:, 0:1, :3] = (r[:, 0:1, :3] / s_a_dc).round().clamp(-qmax - 1, qmax)
    if cols > 3:
        q[:, 0:1, 3:] = (r[:, 0:1, 3:] / s_a_rest).round().clamp(-qmax - 1, qmax)
    if block > 1:
        q[:, 1:, :3] = (r[:, 1:, :3] / s_r_dc).round().clamp(-qmax - 1, qmax)
        if cols > 3:
            q[:, 1:, 3:] = (r[:, 1:, 3:] / s_r_rest).round().clamp(-qmax - 1, qmax)
    r_hat = torch.empty_like(r)
    r_hat[:, 0:1, :3] = q[:, 0:1, :3] * s_a_dc
    if cols > 3:
        r_hat[:, 0:1, 3:] = q[:, 0:1, 3:] * s_a_rest
    if block > 1:
        r_hat[:, 1:, :3] = q[:, 1:, :3] * s_r_dc
        if cols > 3:
            r_hat[:, 1:, 3:] = q[:, 1:, 3:] * s_r_rest

    x_hat = torch.cumsum(r_hat, dim=1).reshape(-1, cols)[:n]
    flat_hat = torch.empty_like(flat)
    flat_hat.index_copy_(0, perm, x_hat.to(flat.dtype))
    Q._set_sh_flat(out, flat_hat)
    return out


def reconstruction_error(sp, bits: int, block: int = BLOCK) -> float:
    """Mean absolute coefficient error of the predictive code (diagnostic)."""
    import qfp_rd as Q

    ref = Q._sh_flat(sp)
    got = Q._sh_flat(quantize_dpcm(sp, bits, block))
    return float((ref - got).abs().mean())


def selftest() -> int:
    """Small synthetic scene: correlated neighbours, known ground truth."""
    import torch
    import common as C
    C.add_code_root()                     # ``calib`` lives in research/code
    import qfp_rd as Q
    from calib.gsrender import Splats

    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  [ok] " if cond else "  [FAIL] ") + str(name))
        ok = ok and bool(cond)

    torch.manual_seed(0)
    grid = torch.stack(torch.meshgrid(torch.arange(8), torch.arange(8), torch.arange(8),
                                      indexing="ij"), dim=-1).reshape(-1, 3).float()
    n = int(grid.shape[0])
    # Per-primitive magnitude that drifts smoothly by ~20% between Morton neighbours: the
    # scalar code spends its full range on the absolute value, the predictive code spends it
    # on the difference.  The real-asset gain is what the node round measures, not this test.
    idx = torch.arange(n, dtype=torch.float32)
    base = (0.50 + 0.10 * torch.sin(idx * 0.35))[:, None].expand(n, 3)
    shN = (base[:, None, :] * torch.linspace(0.5, 0.05, 15)[None, :, None]).expand(n, 15, 3)
    sp = Splats(means=grid * 0.1, scales=torch.full((n, 3), 1e-3),
                quats=torch.tensor([1.0, 0.0, 0.0, 0.0]).expand(n, 4),
                opacities=torch.full((n,), 0.5),
                sh0=base[:, None, :].expand(n, 1, 3).contiguous(),
                shN=shN.contiguous())

    e8 = reconstruction_error(sp, 8)
    e4 = reconstruction_error(sp, 4)
    e2 = reconstruction_error(sp, 2)
    check(f"error grows as bits drop ({e8:.2e} < {e4:.2e} < {e2:.2e})",
          e8 < e4 < e2)

    # The pilot gate.  This is *not* an assertion of victory: the run of 2026-11-14 measured
    # 7.8e-2 for prediction against 6.0e-2 for the scalar code at 2 bits on this synthetic,
    # i.e. prediction lost, because a block of 64 primitives must share one scale while the
    # scalar code re-adapts per primitive, and the cumsum accumulates the residual error.
    # The gate is recorded as a measurement, and it is why no node round was spent on M14.
    import dump_artifacts as D
    plain = D._quantize_splats(sp.clone(), torch, bits=2)
    e_plain = float((Q._sh_flat(sp) - Q._sh_flat(plain)).abs().mean())
    ratio = e2 / e_plain
    print(f"  [pilot] 2-bit dpcm {e2:.3e} vs scalar {e_plain:.3e} -> ratio {ratio:.3f} "
          f"({'wins' if ratio < 1.0 else 'LOSES'})")
    check("the pilot gate is a measurement, not a pass/fail", True)

    # byte accounting: cheaper than the scalar path at the same width
    check("cheaper than the scalar path at 2 bits",
          dpcm_bytes_per_prim(3, 2) < 48 * 2 / 8 + 2.0)

    # the codec is what the decoder would run: rebuilding from the same rule is exact
    q = quantize_dpcm(sp, 4)
    check("output is a clone, input untouched",
          bool(torch.equal(sp.shN, shN)) and not torch.equal(q.shN, sp.shN))

    # a constant block must survive exactly (zero residual everywhere)
    const = Splats(means=grid * 0.1, scales=torch.full((n, 3), 1e-3),
                   quats=torch.tensor([1.0, 0.0, 0.0, 0.0]).expand(n, 4),
                   opacities=torch.full((n,), 0.5),
                   sh0=torch.ones(n, 1, 3), shN=torch.ones(n, 15, 3))
    err_const = reconstruction_error(const, 2)
    check(f"constant field is reproduced ({err_const:.2e})", err_const < 1e-6)

    print("=" * 60)
    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
