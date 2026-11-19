"""m4_bytes + m1_analyse: carry the PQ payload and its byte model."""
import io

B = r"D:\3dsg_1\experiments\m4_bytes.py"
b = io.open(B, encoding="utf-8").read()

b = b.replace('''    if getattr(spec, "sh_msc", None) is not None:''',
'''    if getattr(spec, "sh_pq", None) is not None:
        # Product quantisation: ``m`` interleaved sub-vectors, each with its own
        # 2**b-centre codebook.  Only the codes vary per primitive; the codebooks are a
        # fixed cost of the asset and are amortised in the model exactly as stored.
        import torch
        import qfp_rd as Q
        cols = sh_cols(deg_out)
        m_pq, b_pq = int(spec.sh_pq[0]), int(spec.sh_pq[1])
        dc = sh["dc"].reshape(sh["dc"].shape[0], -1)
        rest = sh["rest"].reshape(sh["rest"].shape[0], -1)
        flat = take(np.concatenate([dc, rest], axis=1)[:, :cols])
        xt = torch.from_numpy(np.ascontiguousarray(flat)).float()
        key = ("pq", m_pq, b_pq, cols, int(flat.shape[0]))
        if codebooks is not None and key in codebooks:
            books = codebooks[key]
        else:
            books = [Q.quantise_codebook(Q._kmeans(xt[:, g::m_pq].contiguous(), 1 << b_pq,
                                                   seed=g, iters=15), 8)
                     for g in range(m_pq)]
            if codebooks is not None:
                codebooks[key] = books
        idx = np.zeros((int(flat.shape[0]), m_pq), dtype=np.int64)
        for g, C in enumerate(books):
            idx[:, g] = Q._vq_assign(xt[:, g::m_pq].contiguous(), C).numpy()
        streams["sh_pq_idx"] = pack_bits(idx, b_pq)
        cb = np.concatenate([C.numpy().reshape(-1) for C in books], axis=0)
        cb_u8 = np.ascontiguousarray(np.asarray(cb, dtype=np.uint8))
        streams["sh_cb_hdr"] = np.array([m_pq, b_pq], dtype=np.uint8).tobytes()
        streams["sh_cb_centroids"] = cb_u8.tobytes()
        n = float(max(1, int(flat.shape[0])))
        per_prim += m_pq * b_pq / 8.0 + cb_u8.size / n
        return streams, per_prim

    if getattr(spec, "sh_msc", None) is not None:''', 1)

io.open(B, "w", encoding="utf-8", newline="\n").write(b)
print("m4", len(b))

A = r"D:\3dsg_1\experiments\m1_analyse.py"
a = io.open(A, encoding="utf-8").read()

a = a.replace('''def msc_bytes_per_prim(sh_degree: int, b_dict: int, b_scalar: int,''',
'''def pq_bytes_per_prim(sh_degree: int, m: int, b: int, n_stored: int = None) -> float:
    """Same PQ model as ``qfp_rd.pq_bytes_per_prim``."""
    cols = sh_cols(sh_degree)
    return float(m * b) / 8.0 + (1 << b) * cols / float(n_stored or VQ_NOMINAL_PRIMS)


def msc_bytes_per_prim(sh_degree: int, b_dict: int, b_scalar: int,''', 1)

a = a.replace('''                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None) -> float:''',
'''                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None, sh_pq: tuple = None) -> float:''', 1)

a = a.replace('''    if sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),''',
'''    if sh_pq is not None:
        b_sh = pq_bytes_per_prim(sh_degree, int(sh_pq[0]), int(sh_pq[1]), n_stored)
    elif sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),''', 1)

# parser -> 9-tuple
a = a.replace('        return 1.0, 32, {}, None, None, None, None, None',
              '        return 1.0, 32, {}, None, None, None, None, None, None')
a = a.replace('                return 1.0, 32, {attr: int(body[len(alias):])}, None, None, None, None, None',
              '                return 1.0, 32, {attr: int(body[len(alias):])}, None, None, None, None, None, None')
a = a.replace('        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None, None, None, None',
              '        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None, None, None, None, None')
a = a.replace('    if not rest:\n        return keep, sh_bits, geo, deg_out, None, None, None, None',
              '    if not rest:\n        return keep, sh_bits, geo, deg_out, None, None, None, None, None')
a = a.replace('    geo = {a: int(rest[2:]) for a in GEO_SCALARS}\n    return keep, sh_bits, geo, deg_out, None, None, None, None',
              '    geo = {a: int(rest[2:]) for a in GEO_SCALARS}\n    return keep, sh_bits, geo, deg_out, None, None, None, None, None')

a = a.replace('''            or (rest.startswith("msc") and "-" in rest)):
        geo_l, sh_l, cbits, vq_l, rvq_l, msc_l = {}, 32, None, None, None, None''',
'''            or (rest.startswith("msc") and "-" in rest)
            or (rest.startswith("pq") and "-" in rest)):
        geo_l, sh_l, cbits, vq_l, rvq_l, msc_l, pq_l = {}, 32, None, None, None, None, None''', 1)

a = a.replace('''            elif tok.startswith("msc") and "-" in tok:''',
'''            elif tok.startswith("pq") and "-" in tok:
                p, _, q = tok[2:].partition("-")
                pq_l = (int(p), int(q))
            elif tok.startswith("msc") and "-" in tok:''', 1)

a = a.replace('        return keep_l, sh_l, geo_l, deg_out, cbits, vq_l, rvq_l, msc_l',
              '        return keep_l, sh_l, geo_l, deg_out, cbits, vq_l, rvq_l, msc_l, pq_l')

a = a.replace('''    keep, sh_bits, geo, deg_out, cbits, vq_bits, rvq_bits, msc_bits = parse_spec(name)''',
'''    keep, sh_bits, geo, deg_out, cbits, vq_bits, rvq_bits, msc_bits, pq_bits = parse_spec(name)''', 1)
a = a.replace('''                         sh_msc=msc_bits)''', '''                         sh_msc=msc_bits, sh_pq=pq_bits)''', 1)
a = a.replace('    keep, sh_bits, geo, deg_out, cbits, _vq, _rvq, _msc = parse_spec(s)',
              '    keep, sh_bits, geo, deg_out, cbits, _vq, _rvq, _msc, _pq = parse_spec(s)')
a = a.replace('                    keep, sh_bits, _geo, _deg, _cb, _vq, _rvq, _msc = parse_spec(spec)',
              '                    keep, sh_bits, _geo, _deg, _cb, _vq, _rvq, _msc, _pq = parse_spec(spec)')

io.open(A, "w", encoding="utf-8", newline="\n").write(a)
print("m1_analyse", len(a))
