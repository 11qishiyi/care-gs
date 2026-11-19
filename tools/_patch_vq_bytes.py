"""Teach m4_bytes to encode vector-quantised SH (M9) so measured bytes cover the dictionary."""
import io

P = r"D:\3dsg_1\experiments\m4_bytes.py"
s = io.open(P, encoding="utf-8").read()

HELP = '''

def sh_cols(deg: int) -> int:
    return 3 * (deg + 1) ** 2


def _nearest(x: np.ndarray, centres: np.ndarray, chunk: int = 20000) -> np.ndarray:
    """Index of the nearest centre for every row of ``x`` (Chebyshev-safe, chunked)."""
    n = int(x.shape[0])
    out = np.empty(n, dtype=np.int64)
    ct = np.einsum("ij,ij->i", centres, centres)
    for s0 in range(0, n, chunk):
        xb = x[s0:s0 + chunk]
        d2 = (xb * xb).sum(1)[:, None] - 2.0 * (xb @ centres.T) + ct[None, :]
        out[s0:s0 + chunk] = d2.argmin(1)
    return out


def _codebook(flat: np.ndarray, vq_bits: int, seed: int = 0):
    """Train the SH dictionary the way ``qfp_rd`` does, then quantise it to 8 bit.

    Returns ``(codes8, header_bytes, centroids_float)``: the *stored* form is one
    byte per coefficient plus a two-float header, which is what the model charges.
    """
    import torch
    import qfp_rd as Q
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    x = torch.from_numpy(np.ascontiguousarray(flat)).float().to(dev)
    C = Q._kmeans(x, 1 << int(vq_bits), iters=15, seed=seed)
    C = Q.quantise_codebook(C, 8)
    Cf = C.detach().cpu()
    mn = float(Cf.amin())
    step = float(((Cf.amax() - mn) / 255.0).clamp_min(1e-12))
    codes8 = torch.round((Cf - mn) / step).clamp_(0.0, 255.0).to(torch.uint8).contiguous()
    hdr = np.asarray([mn, step], dtype=np.float32).tobytes()
    return codes8.numpy(), hdr, Cf.numpy()

'''
if "def _codebook(" not in s:
    anchor = "\ndef _attribute_arrays(splats):"
    s = s.replace(anchor, HELP + "\ndef _attribute_arrays(splats):", 1)

OLD = "def _encode(spec, geo, sh, deg: int, keep_idx, perm) -> tuple:"
NEW = "def _encode(spec, geo, sh, deg: int, keep_idx, perm, codebooks=None) -> tuple:"
if OLD in s:
    s = s.replace(OLD, NEW, 1)

VQ_BLOCK = '''    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
    if getattr(spec, "sh_vq_bits", None) is not None:
        # Dictionary-coded view-dependent block: one index per primitive plus a
        # per-asset codebook of 8-bit centroids (the codebook is part of the file,
        # so it is charged here -- an uNpaid dictionary would not be a codec).
        vq_bits = int(spec.sh_vq_bits)
        cols = sh_cols(deg_out)
        dc = sh["dc"].reshape(sh["dc"].shape[0], -1)
        rest = sh["rest"].reshape(sh["rest"].shape[0], -1)
        flat = np.concatenate([dc, rest], axis=1)[:, :cols]
        flat = take(flat)
        key = (vq_bits, deg_out, int(flat.shape[0]))
        if codebooks is not None and key in codebooks:
            codes8, hdr, cen = codebooks[key]
        else:
            codes8, hdr, cen = _codebook(flat, vq_bits)
            if codebooks is not None:
                codebooks[key] = (codes8, hdr, cen)
        codes = _nearest(flat, cen)
        streams["sh_index"] = pack_bits(codes, vq_bits)
        streams["sh_cb_hdr"] = hdr
        streams["sh_cb_centroids"] = np.ascontiguousarray(codes8).tobytes()
        per_prim += vq_bits / 8.0 + (codes8.size) / float(flat.shape[0])
        return streams, per_prim

'''
OLD_HEAD = '''    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
    blocks = [("sh_dc", sh["dc"])]'''
if OLD_HEAD in s:
    s = s.replace(OLD_HEAD, VQ_BLOCK + '''    blocks = [("sh_dc", sh["dc"])]''', 1)

# thread the codebook cache through measure_scene
OLD = '''        streams, model_per_stored = _encode(spec, geo, sh, deg, keep_idx, None)'''
NEW = '''        streams, model_per_stored = _encode(spec, geo, sh, deg, keep_idx, None,
                                             codebooks=cache)'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)
OLD = '''            stream_m, _ = _encode(spec, geo, sh, deg, keep_idx, inner)'''
NEW = '''            stream_m, _ = _encode(spec, geo, sh, deg, keep_idx, inner, codebooks=cache)'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)
OLD = '''            stream_m, _ = _encode(spec, geo, sh, deg, None, perm)'''
NEW = '''            stream_m, _ = _encode(spec, geo, sh, deg, None, perm, codebooks=cache)'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)
OLD = '''    order = morton_order(geo["means"])

    rows = []'''
NEW = '''    order = morton_order(geo["means"])

    cache = {}
    rows = []'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok", len(s))
