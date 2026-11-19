p = "experiments/m23_pred.py"
s = open(p, encoding="utf-8").read()
orig = s

s = s.replace('''def narrow(d: np.ndarray, bits: int) -> tuple:''',
'''def block_residual(levels: np.ndarray, size: int = M.CLUSTER_SIZE) -> tuple:
    """Residual against the *block's* mean level, modular in the level width.

    The measurement that motivated this: deltas to the previous primitive bought 0.27 MB in 98 MB,
    i.e. neighbouring Gaussians' quantised attributes are already noise at 8 bits.  Whatever
    smoothness the field has lives at a coarser scale, so predict from the block instead.
    """
    a = np.asarray(levels, dtype=np.int64)
    a = a.reshape(-1, 1) if a.ndim == 1 else a
    n, k = a.shape
    nblk = (n + size - 1) // size
    pad = nblk * size - n
    ap = np.vstack([a, np.zeros((pad, k), dtype=np.int64)]) if pad else a
    means = np.rint(ap.reshape(nblk, size, k).mean(axis=1)).astype(np.int64)      # (nblk, k)
    res = (ap - np.repeat(means, size, axis=0)) & 0xFF
    return res.astype(np.uint8), means.astype(np.uint8)


def narrow(d: np.ndarray, bits: int) -> tuple:''')

s = s.replace('''        levels = C.unpack_bits(streams[name], bits, count * dim).reshape(count, dim)
        d, dtype = narrow(to_delta(levels), bits)
        out[dname] = d.tobytes()
        out.pop(name, None)
        flags[name] = {"bits": bits, "dim": dim, "count": count, "dtype": dtype}''',
'''        levels = C.unpack_bits(streams[name], bits, count * dim).reshape(count, dim)
        if mode == "block" and bits <= 8:
            d, means = block_residual(levels)
            out[dname] = d.tobytes()
            out[dname.replace("_d", "_bm")] = means.tobytes()
            flags[name] = {"bits": bits, "dim": dim, "count": count, "dtype": "block"}
        else:
            d, dtype = narrow(to_delta(levels), bits)
            out[dname] = d.tobytes()
            flags[name] = {"bits": bits, "dim": dim, "count": count, "dtype": dtype}
        out.pop(name, None)''')

s = s.replace('''def apply(meta: dict, streams: dict) -> tuple:''',
'''def apply(meta: dict, streams: dict, mode: str = "delta") -> tuple:''')

s = s.replace('''        dt = {"u1": "u1", "i1": "<i1"}.get(str(f.get("dtype", "i2")), "<i2")
        d = np.frombuffer(out[dname], dtype=dt).astype(np.int64).reshape(count, dim)''',
'''        if str(f.get("dtype")) == "block":
            d = np.frombuffer(out[dname], dtype="u1").astype(np.int64).reshape(count, dim)
            means = np.frombuffer(out[dname.replace("_d", "_bm")], dtype="u1"
                                  ).astype(np.int64).reshape(-1, dim)
            size = M.CLUSTER_SIZE
            nblk = means.shape[0]
            big = (d + np.repeat(means, size, axis=0)[:count]) & 0xFF
            levels = np.clip(big, 0, (1 << bits) - 1).astype(np.int64)
            out[name] = M.pack_bits(levels.reshape(-1), bits)
            out.pop(dname, None)
            out.pop(dname.replace("_d", "_bm"), None)
            continue
        dt = {"u1": "u1", "i1": "<i1"}.get(str(f.get("dtype", "i2")), "<i2")
        d = np.frombuffer(out[dname], dtype=dt).astype(np.int64).reshape(count, dim)''')

assert s != orig
open(p, "w", encoding="utf-8").write(s)

p = "experiments/m19_codec.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''         "cluster_off_d", "geo_scales_d", "geo_opacities_d",''',
'''         "cluster_off_d", "geo_scales_d", "geo_opacities_d",
         "geo_scales_bm", "geo_opacities_bm",''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)

p = "experiments/m23_run.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''#: name -> (spec, geo_delta)
VARIANTS = {
    "A_base": ("c10_o8_sh3", False),
    "B_delta": ("c10_o8_sh3", True),
    "C_st3": ("gp8-8-8_c10_sh3", False),
    "D_both": ("gp8-8-8_c10_sh3", True),
}''',
'''#: name -> (spec, geometry recoding mode, or None for the plain codec)
VARIANTS = {
    "A_base": ("c10_o8_sh3", None),
    "B_delta": ("c10_o8_sh3", "delta"),
    "C_st3": ("gp8-8-8_c10_sh3", None),
    "D_both": ("gp8-8-8_c10_sh3", "delta"),
    "E_block": ("c10_o8_sh3", "block"),
    "F_st3blk": ("gp8-8-8_c10_sh3", "block"),
}''')
s = s.replace('''    for name, (spec, delta) in VARIANTS.items():''',
'''    for name, (spec, delta) in VARIANTS.items():''')
s = s.replace('''    "D_both": "B + C",
}''','''    "D_both": "B + C",
    "E_block": "A + block-mean residuals on scales/opacity (lossless)",
    "F_st3blk": "C + E",
}''')
s = s.replace('''            rec = B.encode_basis(mod, rank=a.rank, bits_total=a.bits, level=a.level, path=path,
                                 spec_name=spec, geo_delta=delta)''',
'''            rec = B.encode_basis(mod, rank=a.rank, bits_total=a.bits, level=a.level, path=path,
                                 spec_name=spec, geo_delta=bool(delta), geo_mode=delta or "delta")''')
s = s.replace('''            "variant": name, "spec": spec, "geo_delta": delta,''',
'''            "variant": name, "spec": spec, "geo_delta": delta,''')
s = s.replace('''    for lhs, rhs in (("B_delta", "A_base"), ("D_both", "C_st3")):''',
'''    for lhs, rhs in (("B_delta", "A_base"), ("D_both", "C_st3"), ("E_block", "A_base"),
                     ("F_st3blk", "C_st3")):''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)

p = "experiments/m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''                 return_recon: bool = False, geo_delta: bool = False) -> dict:''',
'''                 return_recon: bool = False, geo_delta: bool = False,
                 geo_mode: str = "delta") -> dict:''')
s = s.replace('''        import m23_pred
        meta, streams = m23_pred.apply(meta, streams)''',
'''        import m23_pred
        meta, streams = m23_pred.apply(meta, streams, mode=geo_mode)''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched block residuals")
