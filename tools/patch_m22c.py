import numpy as np

p = "experiments/m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s

s = s.replace('''    b = allocate(comp, bits_total)
    out = np.empty_like(coef, dtype=np.float32)
    codes = []
    for j, bj in enumerate(b):
        step = 2.0 / float(1 << int(bj))
        v = np.asarray(coef[:, j], dtype=np.float32) / comp[j]
        c = np.clip(np.floor((v + 1.0) / step), 0, (1 << int(bj)) - 1).astype(np.uint8)
        out[:, j] = ((c.astype(np.float32) + 0.5) * step - 1.0) * comp[j]
        codes.append(c)''',
'''    b = allocate(comp, bits_total)
    out = np.empty_like(coef, dtype=np.float32)
    wide = int(b.max()) > 8
    codes = []
    for j, bj in enumerate(b):
        step = 2.0 / float(1 << int(bj))
        v = np.asarray(coef[:, j], dtype=np.float32) / comp[j]
        c = np.clip(np.floor((v + 1.0) / step), 0, (1 << int(bj)) - 1)
        c = c.astype(np.uint16 if wide else np.uint8)
        out[:, j] = ((c.astype(np.float32) + 0.5) * step - 1.0) * comp[j]
        codes.append(c)''')

# ---- packing: one sub-stream per component, its own depth -----------------------------------
s = s.replace('''def solve_basis(meta: dict, streams: dict, n: int, cols: int) -> np.ndarray:''',
'''def pack_codes(codes, bits, layout: str = "bits") -> bytes:
    """Concatenate per-component codes; each component has its own depth, so each gets its own span."""
    import m19_codec as C

    out = []
    for j, (c, bj) in enumerate(zip(codes, bits)):
        if layout == "bytes":
            out.append(np.asarray(c, dtype=np.uint8 if int(bj) <= 8 else np.uint16).tobytes())
        else:
            out.append(C.pack_bits(np.asarray(c, dtype=np.uint8 if int(bj) <= 8 else np.uint16)
                                   .astype(np.int64), int(bj)))
    return b"".join(out)


def unpack_codes(buf, bits, n: int, layout: str = "bits") -> list:
    import m19_codec as C

    out, off, el = [], 0, 1
    for bj in bits:
        nbytes = int(np.ceil(n * int(bj) / 8.0)) if layout != "bytes" else n * (1 if int(bj) <= 8 else 2)
        el = 1 if int(bj) <= 8 else 2
        if layout == "bytes":
            out.append(np.frombuffer(buf, dtype=np.uint8 if el == 1 else np.uint16, count=n,
                                     offset=off).copy())
        else:
            out.append(C.unpack_bits(buf[off:off + nbytes], int(bj), n))
        off += nbytes
    return out


def solve_basis(meta: dict, streams: dict, n: int, cols: int) -> np.ndarray:''')

s = s.replace('''    comp = np.frombuffer(streams["sh_basis_comp"], dtype=np.float32).astype(np.float64)
    if meta.get("sh_coef_layout") == "bits":''',
'''    comp = np.frombuffer(streams["sh_basis_comp"], dtype=np.float32).astype(np.float64)
    if "sh_coef_bits" in streams:
        bits = list(np.frombuffer(streams["sh_coef_bits"], dtype=np.uint8))
        codes = unpack_codes(streams["sh_coef"], bits, n, str(meta.get("sh_coef_layout", "bits")))
        coef = np.empty((n, len(bits)), dtype=np.float64)
        for j, bj in enumerate(bits):
            step = 2.0 / float(1 << int(bj))
            coef[:, j] = ((codes[j].astype(np.float64) + 0.5) * step - 1.0) * comp[j]
        return mean[None, :] + coef @ basis
    if meta.get("sh_coef_layout") == "bits":''')

assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched codes/packing")
