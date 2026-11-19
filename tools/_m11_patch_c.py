"""qfp_rd stage 3: the selector itself, the realise path, and the M11 grid."""
import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace(
    """def base_degree(sp) -> int:""",
    '''def _q_block(x, bits: int):
    """Published block quantiser on one primitive block (per-primitive max scale)."""
    import torch
    qmax = float((1 << (int(bits) - 1)) - 1)
    a = x.abs().amax(dim=1, keepdim=True).clamp_min(1e-12)
    st = a / qmax
    return torch.round(x / st).clamp(-qmax - 1.0, qmax) * st


def msc_select(sp, spec: QSpec, state, deg_out: int):
    """Pick a mode per primitive: ``argmin_m D_m + lam * c_m``.

    ``lam`` is normalised so that ``alpha = 1`` prices one byte at the asset's mean
    scalar-quantisation error, which keeps the three alphas comparable across assets.
    Returns ``(modes, rec_dict_full, rec_scalar_full, frac)``.
    """
    import torch
    cols = sh_cols(int(deg_out))
    m = spec.sh_msc
    b_d, b_s, alpha = int(m["b_dict"]), int(m["b_scalar"]), float(m["alpha"])
    flat = _sh_flat(sp)[:, :cols].contiguous()
    C = state.codebook(b_d, deg_out)
    a = _vq_assign(flat, C)
    rec_d = C.index_select(0, a)
    Dd = ((flat - rec_d) ** 2).sum(1)
    q0 = _q_block(flat[:, :3], b_s)
    q1 = _q_block(flat[:, 3:], b_s)
    rec_s = torch.cat([q0, q1], dim=1)
    Ds = ((flat - rec_s) ** 2).sum(1)
    Dz = (flat ** 2).sum(1)
    c_dict, c_scalar, c_zero = msc_bytes(deg_out, b_d, b_s, int(sp.n))
    lam = alpha * float(Ds.mean()) / max(c_scalar, 1e-12)
    cost = torch.stack([Dz + lam * c_zero, Dd + lam * c_dict, Ds + lam * c_scalar], dim=1)
    modes = cost.argmin(dim=1)
    n = float(max(1, int(sp.n)))
    frac = (float((modes == MSC_ZERO).sum()) / n,
            float((modes == MSC_DICT).sum()) / n,
            float((modes == MSC_SCALAR).sum()) / n)
    return modes, rec_d, rec_s, frac


def quantize_msc(sp, spec: QSpec, state, deg_out: int):
    """Write the selected reconstruction into the SH block; bands above are zeroed."""
    import torch
    cols = sh_cols(int(deg_out))
    modes, rec_d, rec_s, frac = msc_select(sp, spec, state, deg_out)
    flat = _sh_flat(sp)
    out = flat.clone()
    out[:, :cols] = 0.0
    sel_d = modes == MSC_DICT
    sel_s = modes == MSC_SCALAR
    if bool(sel_d.any()):
        out[sel_d, :cols] = rec_d[sel_d]
    if bool(sel_s.any()):
        out[sel_s, :cols] = rec_s[sel_s]
    if cols < int(out.shape[1]):
        out[:, cols:] = 0.0
    _set_sh_flat(sp, out)
    return modes, frac


def base_degree(sp) -> int:''', 1)

s = s.replace(
    """    out = sp.clone()
    if spec.sh_rvq_bits is not None:""",
    """    out = sp.clone()
    if spec.sh_msc is not None:
        if state is None:
            raise RuntimeError("mode-selected SH needs the scene state (codebook)")
        deg_out = spec.out_degree(int(base_degree(sp)))
        _, frac = quantize_msc(out, spec, state, deg_out)
        spec.msc_frac = frac
    elif spec.sh_rvq_bits is not None:""", 1)

s = s.replace(
    '''#: M10 grid: two-stage dictionary.''',
    '''#: M11 grid: per-primitive mode selection.  M9 and M10 pushed uniform coding to its
#: limit (19x at 0.3-2.4 pp), and the matched-rate curves show the best family depends on
#: the rate; the remaining freedom is letting each primitive choose its own mode.
M11_VARIANTS = ",".join([
    "clean",
    # single-family anchors at the same bytes
    "c8_o8_sh2", "c8_o8_sh3", "vq12_c8_o8", "rvq10-4_c8_o8",
    # the selector: dict width 12, scalar width 4, three prices for a byte
    "msc12-4-a1_c8_o8", "msc12-4-a2_c8_o8", "msc12-4-a4_c8_o8",
    # a wider scalar option should help the primitives the dictionary serves badly
    "msc12-6-a1_c8_o8", "msc12-6-a4_c8_o8",
    # cheaper dictionary, narrower scalar
    "msc10-4-a2_c8_o8", "msc12-2-a1_c8_o8",
    # buy back 2 B from the nine scalars and spend it on SH
    "msc12-4-a1_c8_o6", "msc12-6-a4_c8_o6",
    # low-rate corner
    "p30_msc12-4-a1_c8_o8",
])


#: M10 grid: two-stage dictionary.''', 1)

s = s.replace(
    """                                                  M9_VARIANTS, M10_VARIANTS):""",
    """                                                  M9_VARIANTS, M10_VARIANTS,
                                                  M11_VARIANTS):""", 1)

s = s.replace(
    """                "m10": M10_VARIANTS}[preset]""",
    """                "m10": M10_VARIANTS, "m11": M11_VARIANTS}[preset]""", 1)

s = s.replace(
    """choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9", "m10"],""",
    """choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9", "m10", "m11"],""", 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("stage 3", len(s))
