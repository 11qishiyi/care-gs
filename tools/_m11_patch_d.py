"""m4_bytes + m1_analyse: carry the MSC payload and its byte model."""
import io

B = r"D:\3dsg_1\experiments\m4_bytes.py"
b = io.open(B, encoding="utf-8").read()

b = b.replace(
    """    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
    if getattr(spec, "sh_rvq_bits", None) is not None:""",
    """    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
    if getattr(spec, "sh_msc", None) is not None:
        # Per-primitive mode selection: a 2-bit flag per primitive, then only the
        # payload each mode actually needs.  The selection is recomputed here with the
        # same routine ``qfp_rd`` uses, so the streams describe the same file.
        import torch
        import qfp_rd as Q
        cols = sh_cols(deg_out)
        m = spec.sh_msc
        b_d, b_s = int(m["b_dict"]), int(m["b_scalar"])
        alpha = float(m["alpha"])
        dc = sh["dc"].reshape(sh["dc"].shape[0], -1)
        rest = sh["rest"].reshape(sh["rest"].shape[0], -1)
        flat = take(np.concatenate([dc, rest], axis=1)[:, :cols])
        key = ("msc", b_d, cols, int(flat.shape[0]))
        if codebooks is not None and key in codebooks:
            c_u8, hdr, cen = codebooks[key]
        else:
            c_u8, hdr, cen = _codebook(flat, b_d)
            if codebooks is not None:
                codebooks[key] = (c_u8, hdr, cen)
        xt = torch.from_numpy(np.ascontiguousarray(flat)).float()
        ct = torch.from_numpy(np.ascontiguousarray(cen)).float()
        a = Q._vq_assign(xt, ct)
        rec_d = ct.index_select(0, a)
        q0 = Q._q_block(xt[:, :3], b_s)
        q1 = Q._q_block(xt[:, 3:], b_s)
        rec_s = torch.cat([q0, q1], dim=1)
        Dd = ((xt - rec_d) ** 2).sum(1)
        Ds = ((xt - rec_s) ** 2).sum(1)
        Dz = (xt ** 2).sum(1)
        c_dict, c_scalar, c_zero = Q.msc_bytes(deg_out, b_d, b_s, int(flat.shape[0]))
        lam = alpha * float(Ds.mean()) / max(c_scalar, 1e-12)
        cost = torch.stack([Dz + lam * c_zero, Dd + lam * c_dict,
                            Ds + lam * c_scalar], dim=1)
        modes = cost.argmin(dim=1)
        mz = (modes == 0).numpy()
        md = (modes == 1).numpy()
        ms = (modes == 2).numpy()
        streams["msc_modes"] = pack_bits(modes.numpy().reshape(-1, 1), Q.MSC_FLAG_BITS)
        n = float(max(1, int(flat.shape[0])))
        per_prim += Q.MSC_FLAG_BITS / 8.0 + c_u8.size / n
        if md.any():
            streams["sh_index"] = pack_bits(a.numpy()[md].reshape(-1, 1), b_d)
            per_prim += (float(md.sum()) / n) * b_d / 8.0
        if ms.any():
            sub = xt[ms]
            s0 = sub[:, :3].abs().amax(dim=1, keepdim=True).clamp_min(1e-12)
            s1 = sub[:, 3:].abs().amax(dim=1, keepdim=True).clamp_min(1e-12)
            qmax = float((1 << (b_s - 1)) - 1)
            st0, st1 = s0 / qmax, s1 / qmax
            c0 = torch.round(sub[:, :3] / st0).clamp(-qmax - 1.0, qmax).numpy().astype(np.int64)
            c1 = torch.round(sub[:, 3:] / st1).clamp(-qmax - 1.0, qmax).numpy().astype(np.int64)
            scales = np.concatenate([st0.numpy(), st1.numpy()], axis=1).astype(np.float32)
            streams["sh_scalar_scale"] = scales.tobytes()
            streams["sh_scalar_codes"] = (pack_bits(c0, b_s + 1)
                                          + pack_bits(c1, b_s + 1))
            per_prim += (float(ms.sum()) / n) * (cols * (b_s + 1) / 8.0 + 2.0)
        streams["sh_cb_hdr"] = hdr
        streams["sh_cb_centroids"] = np.ascontiguousarray(c_u8).tobytes()
        _ = mz
        return streams, per_prim

    if getattr(spec, "sh_rvq_bits", None) is not None:""", 1)

io.open(B, "w", encoding="utf-8", newline="\n").write(b)
print("m4", len(b))

A = r"D:\3dsg_1\experiments\m1_analyse.py"
a = io.open(A, encoding="utf-8").read()

a = a.replace(
    """def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None) -> float:""",
    """def msc_bytes_per_prim(sh_degree: int, b_dict: int, b_scalar: int,
                       frac=(0.0, 1.0, 0.0), n_stored: int = None) -> float:
    \"\"\"Same mode-mix model as ``qfp_rd.msc_bytes_per_prim``.\"\"\"
    cols = sh_cols(sh_degree)
    n = float(n_stored or VQ_NOMINAL_PRIMS)
    c_dict = b_dict / 8.0 + vq_codebook_bytes(b_dict, cols) / n
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    tot = sum(frac) or 1.0
    f = [x / tot for x in frac]
    return float(MSC_FLAG_BITS / 8.0 + f[1] * c_dict + f[2] * c_scalar)


def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None) -> float:""", 1)

a = a.replace(
    """    cols = sh_cols(sh_degree)
    if sh_rvq is not None:""",
    """    cols = sh_cols(sh_degree)
    if sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),
                                  int(sh_msc["b_scalar"]), sh_msc.get("frac")
                                  or (0.0, 1.0, 0.0), n_stored)
    elif sh_rvq is not None:""", 1)

a = a.replace("""VQ_NOMINAL_PRIMS = 4_000_000""",
              """VQ_NOMINAL_PRIMS = 4_000_000
MSC_FLAG_BITS = 2""", 1)

# parser: msc token -> 8-tuple
a = a.replace('    if s == "clean":\n        return 1.0, 32, {}, None, None, None, None',
              '    if s == "clean":\n        return 1.0, 32, {}, None, None, None, None, None', 1)
a = a.replace('                return 1.0, 32, {attr: int(body[len(alias):])}, None, None, None, None',
              '                return 1.0, 32, {attr: int(body[len(alias):])}, None, None, None, None, None', 1)
a = a.replace('        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None, None, None',
              '        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None, None, None, None', 1)
a = a.replace('    if not rest:\n        return keep, sh_bits, geo, deg_out, None, None, None',
              '    if not rest:\n        return keep, sh_bits, geo, deg_out, None, None, None, None', 1)
a = a.replace('    geo = {a: int(rest[2:]) for a in GEO_SCALARS}\n    return keep, sh_bits, geo, deg_out, None, None, None',
              '    geo = {a: int(rest[2:]) for a in GEO_SCALARS}\n    return keep, sh_bits, geo, deg_out, None, None, None, None', 1)

a = a.replace("""            or (rest.startswith("rvq") and rest[3:4].isdigit())):
        geo_l, sh_l, cbits, vq_l, rvq_l = {}, 32, None, None, None""",
              """            or (rest.startswith("rvq") and rest[3:4].isdigit())
            or (rest.startswith("msc") and "-" in rest)):
        geo_l, sh_l, cbits, vq_l, rvq_l, msc_l = {}, 32, None, None, None, None""", 1)

a = a.replace("""            elif tok.startswith("rvq") and "-" in tok:
                p, _, q = tok[3:].partition("-")
                rvq_l = (int(p), int(q))""",
              """            elif tok.startswith("rvq") and "-" in tok:
                p, _, q = tok[3:].partition("-")
                rvq_l = (int(p), int(q))
            elif tok.startswith("msc") and "-" in tok:
                parts = tok[3:].split("-")
                msc_l = {"b_dict": int(parts[0]), "b_scalar": int(parts[1]),
                         "alpha": int(parts[2].lstrip("a"))}""", 1)

a = a.replace("""        return keep_l, sh_l, geo_l, deg_out, cbits, vq_l, rvq_l""",
              """        return keep_l, sh_l, geo_l, deg_out, cbits, vq_l, rvq_l, msc_l""", 1)

a = a.replace("""    keep, sh_bits, geo, deg_out, cbits, vq_bits, rvq_bits = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits,
                         sh_vq_bits=vq_bits, n_stored=n_stored, sh_rvq=rvq_bits)""",
              """    keep, sh_bits, geo, deg_out, cbits, vq_bits, rvq_bits, msc_bits = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits,
                         sh_vq_bits=vq_bits, n_stored=n_stored, sh_rvq=rvq_bits,
                         sh_msc=msc_bits)""", 1)

a = a.replace("""    keep, sh_bits, geo, deg_out, cbits, _vq, _rvq = parse_spec(s)""",
              """    keep, sh_bits, geo, deg_out, cbits, _vq, _rvq, _msc = parse_spec(s)""", 1)
a = a.replace("""                    keep, sh_bits, _geo, _deg, _cb, _vq, _rvq = parse_spec(spec)""",
              """                    keep, sh_bits, _geo, _deg, _cb, _vq, _rvq, _msc = parse_spec(spec)""", 1)

io.open(A, "w", encoding="utf-8", newline="\n").write(a)
print("m1_analyse", len(a))
