import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()

# --- signature: sharing switches ---------------------------------------------------------------
s = s.replace(
    "           attr_bits: int = 8, dc_bits: int = 6, offset_bits: int = OFFSET_BITS) -> tuple:",
    "           attr_bits: int = 8, dc_bits: int = 6, offset_bits: int = OFFSET_BITS,\n"
    "           share_scale: bool = True, share_quat: bool = True, share_opacity: bool = True,\n"
    "           share_rest: bool = True) -> tuple:")

# --- encode: per-primitive fallbacks -----------------------------------------------------------
old = '''    scodes, smn, sstep = _quant(a_scale, attr_bits)
    st["a_scale"] = M.pack_bits(scodes.reshape(-1), attr_bits)
    st["a_scale_hdr"] = np.concatenate([smn, sstep]).astype(np.float32).tobytes()

    ocodes, omn, ostep = _quant(a_opac.reshape(-1, 1), attr_bits)
    st["a_opac"] = M.pack_bits(ocodes.reshape(-1), attr_bits)
    st["a_opac_hdr"] = np.concatenate([omn, ostep]).astype(np.float32).tobytes()

    qwhich, qabc = GP.st3_encode(a_quat, attr_bits)
    st["a_quat_which"] = M.pack_bits(np.asarray(qwhich, dtype=np.int64).reshape(-1), 2)
    st["a_quat_abc"] = M.pack_bits(np.asarray(qabc, dtype=np.int64).reshape(-1), attr_bits)
'''
new = '''    #: A shared attribute stores one value per voxel; an unshared one stores one per primitive.
    #: The switches exist because the first measurement said the sharing cost 6-8 dB, and the
    #: question "which attribute cannot be shared" has to be answered before the representation is
    #: judged: an anchor grid whose *opacity* is constant inside a voxel is not the same object as
    #: one whose opacity is predicted from the offset.
    if share_scale:
        scodes, smn, sstep = _quant(a_scale, attr_bits)
        st["a_scale"] = M.pack_bits(scodes.reshape(-1), attr_bits)
        st["a_scale_hdr"] = np.concatenate([smn, sstep]).astype(np.float32).tobytes()
    else:
        psc = scales[order]
        sc, smn, sstep = _quant(psc, attr_bits)
        st["p_scale"] = M.pack_bits(sc.reshape(-1), attr_bits)
        st["p_scale_hdr"] = np.concatenate([smn, sstep]).astype(np.float32).tobytes()

    if share_opacity:
        ocodes, omn, ostep = _quant(a_opac.reshape(-1, 1), attr_bits)
        st["a_opac"] = M.pack_bits(ocodes.reshape(-1), attr_bits)
        st["a_opac_hdr"] = np.concatenate([omn, ostep]).astype(np.float32).tobytes()
    else:
        pl = np.log(opac_lin[order] / (1 - opac_lin[order])).reshape(-1, 1)
        oc, omn, ostep = _quant(pl, attr_bits)
        st["p_opac"] = M.pack_bits(oc.reshape(-1), attr_bits)
        st["p_opac_hdr"] = np.concatenate([omn, ostep]).astype(np.float32).tobytes()

    if share_quat:
        qwhich, qabc = GP.st3_encode(a_quat, attr_bits)
        st["a_quat_which"] = M.pack_bits(np.asarray(qwhich, dtype=np.int64).reshape(-1), 2)
        st["a_quat_abc"] = M.pack_bits(np.asarray(qabc, dtype=np.int64).reshape(-1), attr_bits)
    else:
        pq = quats[order]
        qwhich, qabc = GP.st3_encode(pq, attr_bits)
        st["p_quat_which"] = M.pack_bits(np.asarray(qwhich, dtype=np.int64).reshape(-1), 2)
        st["p_quat_abc"] = M.pack_bits(np.asarray(qabc, dtype=np.int64).reshape(-1), attr_bits)
'''
assert old in s
s = s.replace(old, new)

# --- rest sharing ------------------------------------------------------------------------------
old_rest = '''    a_rest = _mean(rest_all)
    f = B.fit(a_rest, rank)'''
new_rest = '''    a_rest = _mean(rest_all) if share_rest else np.asarray(rest_all, dtype=np.float32)[order]
    n_rest = int(a_rest.shape[0])
    f = B.fit(a_rest, rank)'''
assert old_rest in s
s = s.replace(old_rest, new_rest)
s = s.replace('    codes = B.unpack_codes(streams["a_coef"], bits, na, str(meta.get("sh_layout", "bits")))',
              '    n_rest = int(meta.get("n_rest", na))\n'
              '    codes = B.unpack_codes(streams["a_coef"], bits, n_rest, str(meta.get("sh_layout", "bits")))')
s = s.replace('    coef = np.empty((na, len(bits)), dtype=np.float32)',
              '    coef = np.empty((n_rest, len(bits)), dtype=np.float32)')

# the meta records what is shared, and the rest row count
s = s.replace('        "sh_scale_levels": 1,\n    }',
              '        "sh_scale_levels": 1, "n_rest": int(a_rest.shape[0]),\n'
              '        "share": {"scale": bool(share_scale), "quat": bool(share_quat),\n'
              '                  "opacity": bool(share_opacity), "rest": bool(share_rest)},\n    }')

# --- decode: honour the switches ---------------------------------------------------------------
old_dec = '''    a_scale = _attr("scale", 3)
    a_opac = _attr("opac", 1).reshape(-1)
    which = C.unpack_bits(streams["a_quat_which"], 2, na, dtype=np.uint8)
    abc = C.unpack_bits(streams["a_quat_abc"], ab, na * 3, dtype=np.uint8).reshape(na, 3)
    a_quat = np.asarray(GP.st3_decode(which, abc, ab), dtype=np.float32)
'''
new_dec = '''    def _prim(name, dim):
        h = np.frombuffer(streams[f"p_{name}_hdr"], dtype=np.float32).reshape(-1, dim)
        c = C.unpack_bits(streams[f"p_{name}"], ab, n * dim, dtype=np.uint8).reshape(n, dim)
        return h[0] + c.astype(np.float32) * h[1]

    if "a_scale" in streams:
        scales = np.exp(_attr("scale", 3)[ofa]).astype(np.float32)
    else:
        scales = np.exp(_prim("scale", 3)).astype(np.float32)
    if "a_opac" in streams:
        a_opac = _attr("opac", 1).reshape(-1)
        opac = (1.0 / (1.0 + np.exp(-a_opac[ofa]))).astype(np.float32)
    else:
        opac = (1.0 / (1.0 + np.exp(-_prim("opac", 1).reshape(-1)))).astype(np.float32)
    if "a_quat_which" in streams:
        which = C.unpack_bits(streams["a_quat_which"], 2, na, dtype=np.uint8)
        abc = C.unpack_bits(streams["a_quat_abc"], ab, na * 3, dtype=np.uint8).reshape(na, 3)
        quats = np.asarray(GP.st3_decode(which, abc, ab), dtype=np.float32)[ofa]
    else:
        which = C.unpack_bits(streams["p_quat_which"], 2, n, dtype=np.uint8)
        abc = C.unpack_bits(streams["p_quat_abc"], ab, n * 3, dtype=np.uint8).reshape(n, 3)
        quats = np.asarray(GP.st3_decode(which, abc, ab), dtype=np.float32)
'''
assert old_dec in s
s = s.replace(old_dec, new_dec)

old_tail = '''    rest_a = coef @ basis + vmean
    sh_rest = rest_a[ofa].reshape(n, -1, 3)

    return {"means": means.astype(np.float32), "scales": np.exp(a_scale[ofa]).astype(np.float32),
            "quats": a_quat[ofa], "opacities": (1.0 / (1.0 + np.exp(-a_opac[ofa]))).astype(np.float32),
            "sh_dc": sh_dc.astype(np.float32), "sh_rest": sh_rest.astype(np.float32)}'''
new_tail = '''    rest_a = (coef @ basis + vmean).astype(np.float32)
    sh_rest = (rest_a[ofa] if rest_a.shape[0] == na else rest_a).reshape(n, -1, 3)

    return {"means": means.astype(np.float32), "scales": scales, "quats": quats,
            "opacities": opac, "sh_dc": sh_dc.astype(np.float32),
            "sh_rest": sh_rest.astype(np.float32)}'''
assert old_tail in s
s = s.replace(old_tail, new_tail)

# --- CLI switches ------------------------------------------------------------------------------
s = s.replace('    ap.add_argument("--offset-bits", type=int, default=OFFSET_BITS)',
              '    ap.add_argument("--offset-bits", type=int, default=OFFSET_BITS)\n'
              '    ap.add_argument("--per-primitive", default="",\n'
              '                    help="comma list of attributes to keep per primitive: scale,quat,opac,rest")')
s = s.replace('''    import m20_model
    splats = m20_model.load_model(a.ply)''',
              '''    import m20_model
    splats = m20_model.load_model(a.ply)
    keep = {x.strip() for x in a.per_primitive.split(",") if x.strip()}''')
s = s.replace('''                         offset_bits=a.offset_bits, path=a.out)''',
              '''                         offset_bits=a.offset_bits, path=a.out,
                         share_scale="scale" not in keep, share_quat="quat" not in keep,
                         share_opacity="opac" not in keep, share_rest="rest" not in keep)''')
s = s.replace('"dc_bits": a.dc_bits, "offset_bits": a.offset_bits,',
              '"dc_bits": a.dc_bits, "offset_bits": a.offset_bits, "per_primitive": sorted(keep),')
io.open(p, "w", encoding="utf-8").write(s)
print("patched sharing switches")
