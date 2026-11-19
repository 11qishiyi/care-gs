import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace('''def msc_bytes(sh_degree: int, b_dict: int, b_scalar: int, n_stored: int) -> tuple:
    """``(c_dict, c_scalar, c_zero)`` in bytes per primitive, codebook included."""
    cols = sh_cols(sh_degree)
    c_dict = b_dict / 8.0 + vq_codebook_bytes(b_dict, cols) / float(n_stored)
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    return float(c_dict), float(c_scalar), 0.0''',
'''def msc_bytes(sh_degree: int, b_dict: int, b_scalar: int, n_stored: int) -> tuple:
    """``(c_dict, c_scalar, c_zero)`` in bytes per primitive, codebook excluded.

    The codebook is a *fixed* cost for the asset, so it is divided by the stored
    primitive count once (see :func:`msc_bytes_per_prim`) rather than being weighted
    by the share of dictionary-coded primitives.
    """
    cols = sh_cols(sh_degree)
    c_dict = b_dict / 8.0
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    return float(c_dict), float(c_scalar), 0.0


def msc_codebook_per_prim(sh_degree: int, b_dict: int, n_stored: int) -> float:
    return float(vq_codebook_bytes(b_dict, sh_cols(sh_degree))) / float(
        n_stored or VQ_NOMINAL_PRIMS)''', 1)

s = s.replace('''    c_dict, c_scalar, c_zero = msc_bytes(sh_degree, b_dict, b_scalar,
                                         n_stored or VQ_NOMINAL_PRIMS)
    return float(MSC_FLAG_BITS / 8.0 + f[0] * c_zero + f[1] * c_dict + f[2] * c_scalar)''',
'''    c_dict, c_scalar, c_zero = msc_bytes(sh_degree, b_dict, b_scalar,
                                         n_stored or VQ_NOMINAL_PRIMS)
    return float(MSC_FLAG_BITS / 8.0 + f[0] * c_zero + f[1] * c_dict + f[2] * c_scalar
                 + msc_codebook_per_prim(sh_degree, b_dict, n_stored))''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("qfp_rd ok")

A = r"D:\3dsg_1\experiments\m1_analyse.py"
a = io.open(A, encoding="utf-8").read()
a = a.replace('''    c_dict = b_dict / 8.0 + vq_codebook_bytes(b_dict, cols) / n
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    tot = sum(frac) or 1.0
    f = [x / tot for x in frac]
    return float(MSC_FLAG_BITS / 8.0 + f[1] * c_dict + f[2] * c_scalar)''',
'''    c_dict = b_dict / 8.0
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    tot = sum(frac) or 1.0
    f = [x / tot for x in frac]
    return float(MSC_FLAG_BITS / 8.0 + f[1] * c_dict + f[2] * c_scalar
                 + vq_codebook_bytes(b_dict, cols) / n)''', 1)
io.open(A, "w", encoding="utf-8", newline="\n").write(a)
print("m1_analyse ok")

B = r"D:\3dsg_1\experiments\m4_bytes.py"
b = io.open(B, encoding="utf-8").read()
b = b.replace('''            scales = np.concatenate([st0.numpy(), st1.numpy()], axis=1).astype(np.float32)
            streams["sh_scalar_scale"] = scales.tobytes()''',
'''            # two 8-bit block scales per primitive (the published quantiser charges
            # one byte per SH block), with a float32 reference for each block
            s0 = st0.numpy().reshape(-1).astype(np.float64)
            s1 = st1.numpy().reshape(-1).astype(np.float64)
            ref = np.array([s0.max() if s0.size else 1.0,
                            s1.max() if s1.size else 1.0], dtype=np.float32)
            q0 = np.clip(np.rint(s0 / max(ref[0], 1e-12) * 255.0), 0, 255).astype(np.uint8)
            q1 = np.clip(np.rint(s1 / max(ref[1], 1e-12) * 255.0), 0, 255).astype(np.uint8)
            streams["sh_scalar_scale"] = ref.tobytes() + q0.tobytes() + q1.tobytes()''', 1)
b = b.replace('''            per_prim += (float(ms.sum()) / n) * (cols * b_s / 8.0 + 2.0)''',
'''            per_prim += (float(ms.sum()) / n) * (cols * b_s / 8.0 + 2.0)''', 1)
io.open(B, "w", encoding="utf-8", newline="\n").write(b)
print("m4 ok")
