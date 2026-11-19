"""M4: measure the byte model against a real codec (M4 spec, METHOD_PLAN.md).

Every M1-M3 number rests on an *analytical* byte model:

    bytes/prim = sum_a  n_a * b_a / 8  +  SH_SCALE_BYTES (only when SH is quantised)

That model is a claim about a codec nobody ran.  This script runs one:

1. **codes** -- rebuild the exact integer codes the model charges for (scene-level
   min-max grid for the nine geometric scalars, published per-block scale for SH,
   band truncation dropping whole coefficient blocks);
2. **packed** -- bit-pack the codes at exactly ``b`` bits, so ``packed`` must equal
   the model to within one byte per stream (that is the model's own arithmetic);
3. **zstd** -- compress each packed stream with zstd at ``--level``; real codecs
   use entropy coding, the model does not;
4. **morton** -- reorder primitives by the Morton code of their *reconstructed*
   positions before compressing.  No side information is needed: a decoder that
   has decoded the positions can recompute the same order, so this is free.

Criteria (registered in METHOD_PLAN.md M4.4):

G1  the model is an upper bound -- ``morton+zstd`` bytes must be <= model bytes
    for every measured spec (if it is not, the RD curves are optimistic and must
    be recomputed with the higher price);
G2  no rank inversion -- sorting the measured bytes of the measured specs must
    reproduce their order under the model (otherwise the RD tables, which are
    built on the model, would order settings wrongly).

Usage (node, after the dump has finished):

    python experiments/m4_bytes.py --archive /workspace/data/out3dgs \
        --scenes bicycle,flowers,stump,treehill \
        --specs clean,sh4_g16,m16_o8_sh3,m16_o6_sh2,p30 --level 12 \
        --out /workspace/res/m4/m4_bytes.json
"""

import argparse
import json
import os
import sys

import numpy as np


def _C():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common as C
    return C


FP32_BITS = 32
#: mirror of ``qfp_rd.SH_SCALE_BYTES`` (asserted equal in the self-test): the model
#: charges one 2-byte entry for the two block-max scales, not two.
Q_SH_SCALE_BYTES = 2
GEO_ORDER = ("means", "scales", "quats", "opacities")
GEO_DIMS = {"means": 3, "scales": 3, "quats": 4, "opacities": 1}
#: mirror of ``qfp_rd.CLUSTER_SIZE`` / ``CLUSTER_HEADER_BYTES`` (asserted equal in
#: the self-test): cluster-relative positions pay one 24-byte header per block.
CLUSTER_SIZE = 256
CLUSTER_HEADER_BYTES = 24.0
CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)


# ---------------------------------------------------------------------------
# code extraction: the integers the byte model charges for
# ---------------------------------------------------------------------------


def _grid(t: np.ndarray, bits: int):
    n_lev = (1 << int(bits)) - 1
    mn = t.min(axis=0, keepdims=True)
    mx = t.max(axis=0, keepdims=True)
    step = np.maximum(mx - mn, 1e-12) / float(n_lev)
    return mn, step, n_lev


def codes_grid(t: np.ndarray, bits: int) -> np.ndarray:
    """Unsigned codes in ``[0, 2**bits - 1]`` for a per-component uniform grid."""
    if int(bits) >= FP32_BITS:
        raise ValueError("fp32 attributes are not coded as integers")
    mn, step, n_lev = _grid(np.asarray(t, dtype=np.float64), bits)
    q = np.rint((t - mn) / step)
    return np.clip(q, 0, n_lev).astype(np.int64)


def geo_header_bytes(geo: dict, spec) -> bytes:
    """The min/step of every grid-coded attribute, as the decoder needs them.

    ``codes_grid`` derives these from the data and used to drop them, which made the streams
    non-invertible: a decoder had no way to turn a code back into a value.  Two float32 vectors per
    coded attribute cost 64 B for a full 3DGS model -- 1e-5 B/primitive at six million primitives,
    i.e. invisible in every ratio this series reports, but the difference between a byte model and
    a format.
    """
    out = []
    for attr in ("means", "scales", "quats", "opacities"):
        if attr == "means" and getattr(spec, "means_cluster_bits", None) is not None:
            continue                      # cluster coding carries its own per-block origin/step
        bits = int(spec.geo.get(attr, FP32_BITS))
        if bits >= FP32_BITS:
            continue
        mn, step, _ = _grid(np.asarray(geo[attr], dtype=np.float64), bits)
        out.append(np.asarray(mn, dtype=np.float32).reshape(-1))
        out.append(np.asarray(step, dtype=np.float32).reshape(-1))
    return np.concatenate(out).tobytes() if out else b""


def codes_published_sh_parts(block: np.ndarray, bits: int, chunk: int = 1 << 20, perm=None):
    """Codes and per-primitive scales under the published SH quantiser.

    ``dump_artifacts._quantize_splats`` divides each primitive's coefficient block
    by ``max|coef| / qmax`` and rounds; reproducing that here keeps the measured
    bytes honest about the *same* quantiser the RD curves used.  The scale is
    returned so the shipping format can charge for it (the model charges
    ``SH_SCALE_BYTES`` for the two blocks of a primitive).

    Rows are independent -- the scale is a per-row maximum -- so the work is done in
    ``chunk``-row slices.  M42 removed the whole-array temporaries (four of them, 2.2 GB
    each on bicycle) and M43 narrowed the output: the codes are bounded by
    ``2**bits``, so they are stored in the smallest integer that holds them instead of
    the ``int64`` the arithmetic produces.  Both steps are arithmetic-neutral; the bytes
    are pinned by ``experiments/tests/test_m42_encoder_mem.py``.

    ``perm`` gathers rows out of ``block`` one slice at a time (M44).  The caller used to
    materialise ``block[perm]`` -- a second full-size float64 array, 2.2 GB for the SH rest
    block -- only so that this function could read it in Morton order.  Gathering inside the
    loop costs a slice-sized temporary and yields the same codes in the same order.
    """
    qmax = (1 << (int(bits) - 1)) - 1
    if qmax <= 0:
        raise ValueError(f"{bits}-bit SH has qmax=0 and cannot be coded")
    rows = int(block.shape[0])
    cols = int(np.prod(block.shape[1:])) if block.ndim > 1 else 1
    peak = qmax + 1 + qmax                      # the largest code the clip can emit
    dtype = np.uint8 if peak <= 0xFF else (np.uint16 if peak <= 0xFFFF else np.int64)
    out = np.empty((rows, cols), dtype=dtype)
    scale = np.empty((rows, 1), dtype=np.float64)
    flat = block.reshape(rows, cols)
    for i in range(0, rows, max(1, int(chunk))):
        seg = np.asarray(flat[i:i + chunk] if perm is None else flat[np.asarray(perm[i:i + chunk])],
                         dtype=np.float64)
        s = np.abs(seg).max(axis=1, keepdims=True) / float(qmax)
        s = np.where(s > 0, s, 1.0)
        codes = seg / s                      # one temporary the size of the slice
        np.rint(codes, out=codes)
        np.clip(codes, -qmax - 1, qmax, out=codes)
        codes += qmax + 1
        out[i:i + chunk] = codes             # exact: every value is in [0, 2**bits)
        scale[i:i + chunk] = s
    return out, scale[:, 0]


def codes_published_sh(block: np.ndarray, bits: int) -> np.ndarray:
    """Codes only (see :func:`codes_published_sh_parts`)."""
    return codes_published_sh_parts(block, bits)[0]


# ---------------------------------------------------------------------------
# packing and compression
# ---------------------------------------------------------------------------


def pack_bits(codes: np.ndarray, bits: int, chunk: int = 1 << 24) -> bytes:
    """Bit-pack unsigned codes at exactly ``bits`` bits each (row-major).

    M42: the bit-plane version built an ``int64`` plane array of ``size x bits``, which
    is 6.6 GB for bicycle's 276 M SH codes, twice over.  M43: the codes are already
    ``uint8``/``uint16`` where they fit, so the packer slices first and widens per
    slice instead of copying the whole array to ``int64`` up front.  Every chunk is a
    whole number of bytes (8 codes at any width), so the concatenation is identical to
    packing the whole array at once -- ``test_m42_encoder_mem.py`` checks that against
    ``np.packbits`` at every width the format uses.
    """
    bits = int(bits)
    flat = np.asarray(codes).reshape(-1)
    if bits == 8:
        return flat.astype(np.uint8).tobytes()
    if bits == 16:
        return flat.astype(np.uint16).tobytes()
    if bits == 32:
        return flat.astype(np.uint32).tobytes()
    dtype = np.uint8 if bits <= 8 else np.uint16
    shifts = np.arange(bits, dtype=dtype)
    out = []
    step = max(8, (int(chunk) // max(1, bits) // 8) * 8)   # a multiple of 8 codes => whole bytes
    for i in range(0, max(1, flat.size), step):
        seg = np.asarray(flat[i:i + step]).astype(dtype, copy=False)
        planes = ((seg[:, None] >> shifts[None, :]) & dtype(1))
        out.append(np.packbits(planes.reshape(-1)).tobytes())
    return b"".join(out)


ZSTD_BACKEND = None


def _zstd(data: bytes, level: int) -> bytes:
    """zstd when available; otherwise lzma, which is a *weaker* codec.

    The fallback only exists so the self-test runs on a laptop; the node installs
    ``zstandard``, and the recorded ``backend`` says which one produced the bytes.
    """
    global ZSTD_BACKEND
    try:
        import zstandard as zstd
        ZSTD_BACKEND = "zstd"
        return zstd.ZstdCompressor(level=int(level)).compress(data)
    except ImportError:
        import lzma
        ZSTD_BACKEND = "lzma-fallback"
        return lzma.compress(data, preset=int(min(9, max(1, level // 2))))


def morton_order(means: np.ndarray, bits: int = 21) -> np.ndarray:
    """Permutation sorting primitives by the Morton code of their positions.

    Positions are normalised into ``[0, 2**bits)`` per axis first, so the code is
    computable from the *reconstructed* positions alone -- the decoder recomputes
    the same order, hence no permutation has to be stored.
    """
    m = np.asarray(means, dtype=np.float64)
    lo, hi = m.min(axis=0, keepdims=True), m.max(axis=0, keepdims=True)
    u = (m - lo) / np.maximum(hi - lo, 1e-12)
    q = np.clip(np.rint(u * ((1 << bits) - 1)), 0, (1 << bits) - 1).astype(np.uint64)
    code = np.zeros(q.shape[0], dtype=np.uint64)
    # Highest bit first, and the three axes interleaved inside each bit, so that a
    # contiguous run of codes is a compact box -- that is what makes cluster coding of
    # positions work.  Laying the axes out as three consecutive blocks instead would be
    # a plain lexicographic sort by ``x``: the blocks then span the whole scene, the
    # per-block grid gets as coarse as the scene, and the decoded cloud loses decimetres
    # (measured: 25x the position error of `qfp_rd.quantize_cluster`, 4.3 dB of PSNR).
    for b in range(bits - 1, -1, -1):
        for dim in range(3):
            code = (code << np.uint64(1)) | ((q[:, dim] >> np.uint64(b)) & np.uint64(1))
    return np.argsort(code, kind="stable")


# ---------------------------------------------------------------------------
# the measurement itself
# ---------------------------------------------------------------------------



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


def _codebook_pair(flat: np.ndarray, b1: int, b2: int, seed: int = 0):
    """Two-stage dictionary, mirroring ``qfp_rd.build_codebook_pair``.

    The second codebook is trained on the residual of the first, so the stored bytes
    are ``codes1`` + ``codes2`` + both centroid tables.
    """
    import torch
    import qfp_rd as Q
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    x = torch.from_numpy(np.ascontiguousarray(flat)).float().to(dev)
    C1 = Q.quantise_codebook(Q._kmeans(x, 1 << int(b1), iters=15, seed=seed), 8)
    a1 = Q._vq_assign(x, C1)
    R = x - C1.index_select(0, a1)
    C2 = Q.quantise_codebook(Q._kmeans(R, 1 << int(b2), iters=15, seed=seed + 1), 8)

    def pack(C):
        Cf = C.detach().cpu()
        mn = float(Cf.amin())
        step = float(((Cf.amax() - mn) / 255.0).clamp_min(1e-12))
        codes8 = torch.round((Cf - mn) / step).clamp_(0.0, 255.0).to(torch.uint8)
        hdr = np.asarray([mn, step], dtype=np.float32).tobytes()
        return codes8.contiguous().numpy(), hdr, Cf.numpy()
    return pack(C1) + pack(C2)


def _attribute_arrays(splats):
    """The raw (pre-quantisation) attributes, in the domains the model codes."""
    means = np.asarray(splats.means.detach().cpu().numpy(), dtype=np.float64)
    scales = np.asarray(splats.scales.detach().cpu().numpy(), dtype=np.float64)
    quats = np.asarray(splats.quats.detach().cpu().numpy(), dtype=np.float64)
    opac = np.asarray(splats.opacities.detach().cpu().numpy(), dtype=np.float64).reshape(-1, 1)
    op = np.clip(opac, 1e-6, 1 - 1e-6)
    geo = dict(means=means,
               scales=np.log(np.maximum(scales, 1e-12)),
               quats=quats,
               opacities=np.log(op / (1.0 - op)))
    sh = dict(dc=np.asarray(splats.sh0.detach().cpu().numpy(), dtype=np.float64),
              rest=np.asarray(splats.shN.detach().cpu().numpy(), dtype=np.float64))
    return geo, sh


def _sh_stream(codes: np.ndarray, bits: int, layout: str) -> bytes:
    """Byte layout for the SH codes.

    ``bits`` bit-packs them (the layout every model in M1-M19 assumed); ``bytes`` stores one
    byte per code in primitive-major order and ``bytes_coef`` in coefficient-major order, so
    that zstd's symbol stage sees an eight-symbol alphabet instead of three bit-planes.  The
    payload grows four-fold and shrinks again under entropy coding -- whether it wins is a
    measurement, not an argument (M20).

    ``codes`` arrives already offset to ``0 .. 2**bits - 1`` by
    :func:`codes_published_sh_parts`; adding the offset again here would shift every
    coefficient by half the range, which decodes as a colour cast rather than an error.
    """
    u = np.clip(np.asarray(codes, dtype=np.int64), 0, (1 << int(bits)) - 1).astype(np.uint8)
    if layout == "bits":
        return pack_bits(u, bits)
    if layout == "bytes":
        return np.ascontiguousarray(u).tobytes()
    if layout == "bytes_coef":
        return np.ascontiguousarray(u.T).tobytes()
    raise ValueError(f"unknown SH layout {layout!r}")


def _encode(spec, geo, sh, deg: int, keep_idx, perm, codebooks=None,
            sh_layout: str = "bits", parts=("geo", "sh")) -> tuple:
    """Byte streams for one spec, optionally reordered by ``perm``.

    ``keep_idx`` selects the retained primitives (pruning); ``perm`` reorders
    them (Morton).  Returns ``(streams, bytes_per_stored_primitive)`` where the
    byte count is the *model's* arithmetic for the same configuration, so the
    two can be compared stream by stream.

    ``parts`` restricts the work to the geometry streams, the colour streams, or both (M45).
    The geometry streams do not depend on ``sh_layout``, so an alphabet search over three SH
    layouts needs the geometry built once, not three times.
    """
    def take(a):
        a = a if keep_idx is None else a[keep_idx]
        return a if perm is None else a[perm]

    do_geo = "geo" in parts
    do_sh = "sh" in parts
    streams, per_prim = {}, 0.0
    for attr in GEO_ORDER if do_geo else ():
        cbits = getattr(spec, "means_cluster_bits", None)
        bq = getattr(spec, "quat_st3", None)
        if attr == "quats" and bq is not None:
            # Smallest-three quaternions (M15): the index of the largest component
            # (2 bits, and its sign comes for free) plus the three others on a
            # ``bq``-bit grid over [-1/sqrt2, 1/sqrt2].  The stream is what a decoder
            # reads; the fourth component is a square root, so it costs no bits.
            import geom_pack as GP
            arr = np.asarray(take(geo[attr]), dtype=np.float64)
            which, codes = GP.st3_encode(arr, int(bq))
            streams["geo_quat_which"] = pack_bits(which.reshape(-1, 1), 2)
            streams["geo_quat_abc"] = pack_bits(codes, int(bq))
            per_prim += (2 + 3 * int(bq)) / 8.0
            continue
        if attr == "means" and cbits is not None:
            # Cluster-relative positions: a per-block origin and per-component step,
            # then three offsets per primitive.  The block order is the Morton order
            # of the *stored* positions, so a decoder can rebuild it for free.
            arr = np.asarray(take(geo[attr]), dtype=np.float64)
            x = arr[morton_order(arr)]
            block = CLUSTER_SIZE
            nblk = max(1, (x.shape[0] + block - 1) // block)
            pad = nblk * block - x.shape[0]
            if pad:
                x = np.concatenate([x, np.repeat(x[-1:], pad, axis=0)], axis=0)
            x = x.reshape(nblk, block, 3)
            o = x.min(axis=1, keepdims=True)
            mx = x.max(axis=1, keepdims=True)
            n_lev = float((1 << int(cbits)) - 1)
            step = np.maximum((mx - o) / n_lev, 1e-12)
            u = np.clip(np.rint((x - o) / step), 0.0, n_lev).astype(np.int64)
            hdr = np.concatenate([o.reshape(nblk, 3), step.reshape(nblk, 3)],
                                 axis=1).astype(np.float32)
            streams["cluster_hdr"] = hdr.tobytes()
            streams["cluster_off"] = pack_bits(u.reshape(-1, 3), int(cbits))
            per_prim += 3 * int(cbits) / 8.0 + CLUSTER_HEADER_PER_PRIM
            continue
        bits = int(spec.geo.get(attr, FP32_BITS))
        arr = take(geo[attr])
        if bits >= FP32_BITS:
            blob = np.ascontiguousarray(arr.astype(np.float32))
            streams[f"geo_{attr}"] = blob.tobytes()
            per_prim += blob.nbytes / arr.shape[0]
        else:
            streams[f"geo_{attr}"] = pack_bits(codes_grid(arr, bits), bits)
            per_prim += GEO_DIMS[attr] * bits / 8.0

    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
    #: The side information a decoder cannot recompute.  Charged to the model like any other
    #: stream, so the measured B/primitive includes it.
    if do_geo:
        streams["geo_hdr"] = geo_header_bytes(geo, spec)
        per_prim += len(streams["geo_hdr"]) / float(max(1, geo["means"].shape[0]))
    if not do_sh:
        return streams, per_prim
    if getattr(spec, "sh_pq", None) is not None:
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
            off = int(qmax) + 1
            c0 = (torch.round(sub[:, :3] / st0).clamp(-qmax - 1.0, qmax)
                  .numpy().astype(np.int64) + off)
            c1 = (torch.round(sub[:, 3:] / st1).clamp(-qmax - 1.0, qmax)
                  .numpy().astype(np.int64) + off)
            # two 8-bit block scales per primitive (the published quantiser charges
            # one byte per SH block), with a float32 reference for each block
            s0 = st0.numpy().reshape(-1).astype(np.float64)
            s1 = st1.numpy().reshape(-1).astype(np.float64)
            ref = np.array([s0.max() if s0.size else 1.0,
                            s1.max() if s1.size else 1.0], dtype=np.float32)
            q0 = np.clip(np.rint(s0 / max(ref[0], 1e-12) * 255.0), 0, 255).astype(np.uint8)
            q1 = np.clip(np.rint(s1 / max(ref[1], 1e-12) * 255.0), 0, 255).astype(np.uint8)
            streams["sh_scalar_scale"] = ref.tobytes() + q0.tobytes() + q1.tobytes()
            streams["sh_scalar_codes"] = pack_bits(c0, b_s) + pack_bits(c1, b_s)
            per_prim += (float(ms.sum()) / n) * (cols * b_s / 8.0 + 2.0)
        streams["sh_cb_hdr"] = hdr
        streams["sh_cb_centroids"] = np.ascontiguousarray(c_u8).tobytes()
        spec.msc_frac = (float(mz.sum()) / n, float(md.sum()) / n, float(ms.sum()) / n)
        # the model is only meaningful once the realised mode mix is known
        per_prim = spec.bytes_per_prim(deg, int(flat.shape[0]))
        return streams, per_prim

    if getattr(spec, "sh_rvq_bits", None) is not None:
        # Two-stage dictionary: index1 + index2 + both centroid tables.  The residual
        # codebook is trained on this asset, so it is charged to this asset.
        b1, b2 = int(spec.sh_rvq_bits[0]), int(spec.sh_rvq_bits[1])
        cols = sh_cols(deg_out)
        dc = sh["dc"].reshape(sh["dc"].shape[0], -1)
        rest = sh["rest"].reshape(sh["rest"].shape[0], -1)
        flat = np.concatenate([dc, rest], axis=1)[:, :cols]
        flat = take(flat)
        key = ("rvq", b1, b2, deg_out, int(flat.shape[0]))
        if codebooks is not None and key in codebooks:
            c1u8, h1, cen1, c2u8, h2, cen2 = codebooks[key]
        else:
            c1u8, h1, cen1, c2u8, h2, cen2 = _codebook_pair(flat, b1, b2)
            if codebooks is not None:
                codebooks[key] = (c1u8, h1, cen1, c2u8, h2, cen2)
        a1 = _nearest(flat, cen1)
        resid = flat - cen1[a1]
        a2 = _nearest(resid, cen2)
        streams["sh_index"] = pack_bits(a1, b1)
        streams["sh_index2"] = pack_bits(a2, b2)
        streams["sh_cb_hdr"] = h1
        streams["sh_cb_centroids"] = np.ascontiguousarray(c1u8).tobytes()
        streams["sh_cb2_hdr"] = h2
        streams["sh_cb2_centroids"] = np.ascontiguousarray(c2u8).tobytes()
        per_prim += ((b1 + b2) / 8.0
                     + (c1u8.size + c2u8.size) / float(flat.shape[0]))
        return streams, per_prim

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

    blocks = [("sh_dc", sh["dc"])]
    if deg_out >= 1:
        rest = sh["rest"]
        if deg_out < deg:
            rest = rest[:, : (deg_out + 1) ** 2 - 1, :]
        blocks.append(("sh_rest", rest))
    block_scales = []
    for key, block in blocks:
        if sh_bits >= FP32_BITS:
            block = take(block)
            blob = np.ascontiguousarray(block.astype(np.float32))
            streams[key] = blob.tobytes()
            per_prim += blob.nbytes / block.shape[0]
            continue
        cols = block.reshape(block.shape[0], -1).shape[1]
        #: M44: the permutation is applied slice by slice inside the quantiser.  ``take(block)``
        #: would copy the whole float64 SH block (2.2 GB on bicycle) just to reorder it.
        if perm is None:
            block = take(block)
        codes, scale = codes_published_sh_parts(block, sh_bits, perm=perm)
        streams[key] = _sh_stream(codes, sh_bits, sh_layout)
        per_prim += (cols * sh_bits / 8.0 if sh_layout == "bits" else cols * 1.0)
        block_scales.append(scale)
    if sh_bits < FP32_BITS:
        # The scale factors the quantiser needs, at the price the model charges:
        # one byte per block, normalised by a scene-wide reference (a handful of
        # floats in the header), so the stream costs 2 bytes per primitive.
        sc = np.stack(block_scales, axis=1)                     # (N, 2) float
        ref = np.maximum(sc.max(axis=0, keepdims=True), 1e-12)
        lvl = np.clip(np.rint(sc / ref * 255.0), 0, 255).astype(np.int64)
        streams["sh_scale"] = pack_bits(lvl, 8)
        #: Two reference scales; without them the ladder is a set of integers with no units.
        streams["sh_hdr"] = np.asarray(ref, dtype=np.float32).tobytes()
        per_prim += Q_SH_SCALE_BYTES + len(streams["sh_hdr"]) / float(max(1, sc.shape[0]))
    return streams, per_prim



def _zstd_memoed(buf, level: int, memo: dict) -> bytes:
    """``_zstd`` with a content-keyed memo.

    Streams are compressed independently, and several specs in one grid share
    byte-identical geometry streams (everything that keeps geometry at fp32 with the
    same retained set).  Hashing is milliseconds against seconds of zstd-12, and the
    key includes the length, so a hit is always the same blob.
    """
    import hashlib

    key = (int(level), len(buf), hashlib.blake2b(buf, digest_size=16).digest())
    hit = memo.get(key)
    if hit is None:
        hit = _zstd(buf, level)
        memo[key] = hit
    return hit

def measure_scene(splats, specs, level: int, log=None, skip_flat: bool = False) -> dict:
    """Model bytes vs. bit-packed bytes vs. zstd bytes for one asset and several specs."""
    import qfp_rd as Q

    geo, sh = _attribute_arrays(splats)
    deg = int(splats.sh_degree)
    n = geo["means"].shape[0]
    order = morton_order(geo["means"])

    cache = {}
    zmemo = {}
    rows = []
    for name in specs:
        spec = Q.parse_spec(name)
        keep = float(spec.keep)
        # Pruning is a *count* question for the byte model; the paper's own
        # action space keeps the highest-scoring primitives, and for a byte
        # measurement any subset of that size prices the same.  We take the first
        # ``k`` in file order (which is *not* spatially sorted, so the Morton
        # experiment below still has something to reorder).
        keep_idx = None if keep >= 1.0 else np.arange(max(1, int(round(keep * n))))
        stored = n if keep_idx is None else int(keep_idx.size)

        streams, model_per_stored = _encode(spec, geo, sh, deg, keep_idx, None,
                                             codebooks=cache)
        perm = order[keep_idx] if keep_idx is not None else order
        # ``order`` indexes the full array; for a pruned subset we re-derive the
        # same ordering inside the subset so that the permutation is a bijection.
        if keep_idx is not None:
            inner = morton_order(geo["means"][keep_idx])
            stream_m, _ = _encode(spec, geo, sh, deg, keep_idx, inner, codebooks=cache)
        else:
            stream_m, _ = _encode(spec, geo, sh, deg, None, perm, codebooks=cache)

        packed = sum(len(v) for v in streams.values()) / stored
        # ``skip_flat`` exists for the M5 pass, which only needs the stream we would
        # actually ship (Morton + zstd) and does not want to pay for a second codec run.
        zstd_flat = None if skip_flat else \
            sum(len(_zstd_memoed(v, level, zmemo)) for v in streams.values()) / stored
        zstd_morton = sum(len(_zstd_memoed(v, level, zmemo))
                          for v in stream_m.values()) / stored

        rows.append(dict(spec=name, keep=keep, stored=stored, n=n,
                         model_bytes_per_prim=model_per_stored,
                         packed_bytes_per_prim=packed,
                         zstd_bytes_per_prim=zstd_flat,
                         zstd_morton_bytes_per_prim=zstd_morton,
                         streams={k: int(len(v)) for k, v in streams.items()}))
        if log:
            flat_txt = "     n/a" if zstd_flat is None else f"{zstd_flat:7.2f}"
            log(f"    {name:14s} model {model_per_stored:7.2f}  packed {packed:7.2f}  "
                f"zstd {flat_txt}  zstd+morton {zstd_morton:7.2f} B/stored prim")
    return dict(n=int(n), sh_degree=deg, rows=rows)


def main(argv=None) -> int:
    C = _C()
    ap = argparse.ArgumentParser(description="M4: measure the byte model with zstd")
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill")
    ap.add_argument("--ply-pattern", default="{archive}/output/{scene}/point_cloud/"
                                             "iteration_40000/point_cloud.ply")
    ap.add_argument("--specs", default="clean,sh4_g16,m16_o8_sh3,m16_o6_sh2,p30")
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--skip-flat", action="store_true",
                    help="measure only the shipped format (Morton + zstd); halves the runtime")
    ap.add_argument("--out", default="/workspace/res/m4/m4_bytes.json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    C.add_code_root()                       # <repo>/research/code for ``calib``
    from calib.gsrender import load_splats
    specs = [s for s in args.specs.split(",") if s.strip()]
    scenes = [s for s in args.scenes.split(",") if s.strip()]
    out = dict(specs=specs, level=int(args.level), scenes=[], criteria={})
    for scene in scenes:
        path = args.ply_pattern.format(archive=args.archive, scene=scene)
        C.log(f"[{C.stamp()}] {scene}: {path}")
        sp = load_splats(path, device="cpu")
        res = measure_scene(sp, specs, args.level, log=C.log, skip_flat=args.skip_flat)
        res["scene"] = scene
        out["scenes"].append(res)
        C.log(f"  {scene}: n={res['n']} deg={res['sh_degree']}")

    # G1: the model must be an upper bound on a real codec.
    viol = []
    for sc in out["scenes"]:
        for row in sc["rows"]:
            if row["zstd_morton_bytes_per_prim"] > row["model_bytes_per_prim"] + 1e-6:
                viol.append(dict(scene=sc["scene"], spec=row["spec"],
                                 model=row["model_bytes_per_prim"],
                                 zstd_morton=row["zstd_morton_bytes_per_prim"]))
    out["criteria"]["G1_model_is_upper_bound"] = dict(verdict=not viol, violations=viol)
    # G2: the ordering the model implies must survive the measurement.
    inv = []
    for sc in out["scenes"]:
        by_model = sorted(sc["rows"], key=lambda r: r["model_bytes_per_prim"])
        by_real = sorted(sc["rows"], key=lambda r: r["zstd_morton_bytes_per_prim"])
        if [r["spec"] for r in by_model] != [r["spec"] for r in by_real]:
            inv.append(dict(scene=sc["scene"],
                            order_model=[r["spec"] for r in by_model],
                            order_real=[r["spec"] for r in by_real],
                            ratio_model=[round(r["model_bytes_per_prim"], 2) for r in by_model],
                            ratio_real=[round(r["zstd_morton_bytes_per_prim"], 2)
                                        for r in by_real]))
    out["criteria"]["G2_no_rank_inversion"] = dict(verdict=not inv, inversions=inv)
    out["backend"] = ZSTD_BACKEND
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    C.json_dump(args.out, out)
    C.log("=" * 70)
    for k, v in out["criteria"].items():
        C.log(f"  {k}: {v['verdict']}")
    C.log(f"WROTE {args.out}")
    return 0


# ---------------------------------------------------------------------------
# self-test (no PLY, no GPU)
# ---------------------------------------------------------------------------


def selftest() -> int:
    C = _C()
    C.add_code_root()          # <repo>/research/code, so ``calib`` imports
    import torch
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import qfp_rd as Q
    from calib.gsrender import Splats

    fails = []

    def check(name, cond, detail=""):
        C.log(f"  [{'ok' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails.append(name)

    rng = np.random.default_rng(0)
    n = 500
    means = rng.normal(0, 1, size=(n, 3)) * np.array([2.0, 0.5, 1.0])
    scales = np.exp(rng.normal(-3, 0.4, size=(n, 3)))
    quats = rng.normal(0, 1, size=(n, 4))
    quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    opac = rng.uniform(0.05, 0.95, size=(n,))
    sh0 = rng.normal(0, 0.5, size=(n, 1, 3))
    shN = rng.normal(0, 0.2, size=(n, 15, 3))
    sp = Splats(means=torch.tensor(means, dtype=torch.float32),
                scales=torch.tensor(scales, dtype=torch.float32),
                quats=torch.tensor(quats, dtype=torch.float32),
                opacities=torch.tensor(opac, dtype=torch.float32),
                sh0=torch.tensor(sh0, dtype=torch.float32),
                shN=torch.tensor(shN, dtype=torch.float32))

    # bit packing must be exactly bits/8 bytes per code, for every width
    for bits in (2, 3, 4, 6, 8, 16):
        c = rng.integers(0, 1 << bits, size=(37, 5), dtype=np.int64)
        blob = pack_bits(c, bits)
        want = int(np.ceil(c.size * bits / 8))
        check(f"pack {bits}-bit codes at {bits}/8 byte", len(blob) == want,
              f"{len(blob)} vs {want}")

    # G1 direction: measured bytes must be reproducible and the model arithmetic
    # must match packing to within one byte per stream.
    res = measure_scene(sp, ["clean", "sh4_g16", "m16_o8_sh3"], level=9, log=None)
    check("SH scale ledger matches qfp_rd", int(Q.SH_SCALE_BYTES) == Q_SH_SCALE_BYTES,
          f"{Q.SH_SCALE_BYTES} vs {Q_SH_SCALE_BYTES}")
    for row in res["rows"]:
        spec = Q.parse_spec(row["spec"])
        # the scale stream is now part of ``streams``, so it is already charged
        scale = 0.0
        diff = row["packed_bytes_per_prim"] - row["model_bytes_per_prim"]
        # Bit packing rounds *each stream* up to a whole byte (a real codec would
        # concatenate them and round once), so one byte per stream is the only
        # slack the model is allowed.
        tol = (len(row["streams"]) + 1) / float(row["stored"])
        check(f"packed codes + scale ledger == model for {row['spec']}", abs(diff) <= tol,
              f"model {row['model_bytes_per_prim']:.3f} packed "
              f"{row['packed_bytes_per_prim']:.3f} scale {scale:.1f} diff {diff:+.4f} "
              f"tol {tol:.4f}")
    check("zstd is not larger than packed on quantised streams",
          all(r["zstd_bytes_per_prim"] <= r["packed_bytes_per_prim"] + 1e-6
              for r in res["rows"]), "")
    check("packed bytes are the model bytes for a pruned spec too",
          abs(measure_scene(sp, ["p50"], level=9)["rows"][0]["packed_bytes_per_prim"]
              - measure_scene(sp, ["p50"], level=9)["rows"][0]["model_bytes_per_prim"]) < 1e-6,
          "")

    # M9: dictionary-coded SH.  The codebook must appear in the streams (it is part
    # of the file) and the packed bytes must still match the model.
    res_vq = measure_scene(sp, ["vq6_c8_o8", "c8_o8_sh3"], level=9)
    vq_row = res_vq["rows"][0]
    check("dictionary streams carry index + centroids",
          {"sh_index", "sh_cb_centroids", "sh_cb_hdr"} <= set(vq_row["streams"]),
          str(sorted(vq_row["streams"])))
    tol_vq = (len(vq_row["streams"]) + 1) / float(vq_row["stored"])
    # cluster coding pads the last block up to CLUSTER_SIZE, so a 500-primitive
    # asset pays for 512 offsets; on a real asset that is <0.01 %, here it is 2 %.
    pad = CLUSTER_SIZE * 3 * 8 / 8.0 / float(vq_row["stored"])
    check("packed == model for a dictionary spec",
          abs(vq_row["packed_bytes_per_prim"] - vq_row["model_bytes_per_prim"])
          <= tol_vq + pad,
          f"model {vq_row['model_bytes_per_prim']:.3f} packed "
          f"{vq_row['packed_bytes_per_prim']:.3f}")
    check("dictionary is much smaller than scalar SH at the same geometry",
          vq_row["model_bytes_per_prim"] < 0.6 * res_vq["rows"][1]["model_bytes_per_prim"],
          f"{vq_row['model_bytes_per_prim']:.2f} vs "
          f"{res_vq['rows'][1]['model_bytes_per_prim']:.2f} B/prim")
    check("zstd also shrinks the dictionary file",
          vq_row["zstd_morton_bytes_per_prim"] <= vq_row["packed_bytes_per_prim"] + 1e-6,
          f"{vq_row['zstd_morton_bytes_per_prim']:.2f}")

    # M10: two-stage dictionary.  Both index streams and both centroid tables are
    # part of the file, and packed bytes must still land on the model's arithmetic.
    res_rvq = measure_scene(sp, ["rvq6-2_c8_o8", "rvq8-4_c8_o8"], level=9)
    rvq_row = res_rvq["rows"][0]
    check("two-stage streams carry both indexes and both codebooks",
          {"sh_index", "sh_index2", "sh_cb_centroids", "sh_cb2_centroids"}
          <= set(rvq_row["streams"]), str(sorted(rvq_row["streams"])))
    tol_rvq = (len(rvq_row["streams"]) + 1) / float(rvq_row["stored"])
    check("packed == model for a two-stage spec",
          abs(rvq_row["packed_bytes_per_prim"] - rvq_row["model_bytes_per_prim"])
          <= tol_rvq + pad,
          f"model {rvq_row['model_bytes_per_prim']:.3f} packed "
          f"{rvq_row['packed_bytes_per_prim']:.3f}")
    check("more residual bits cost more bytes",
          res_rvq["rows"][1]["model_bytes_per_prim"]
          > rvq_row["model_bytes_per_prim"],
          f"{rvq_row['model_bytes_per_prim']:.2f} vs "
          f"{res_rvq['rows'][1]['model_bytes_per_prim']:.2f} B/prim")

    order = morton_order(means)
    check("morton order is a permutation", sorted(order.tolist()) == list(range(n)), "")    # spatial coherence: consecutive primitives after Morton sorting must be
    # closer on average than before (that is the whole point of the ordering).
    d_before = np.linalg.norm(np.diff(means, axis=0), axis=1).mean()
    d_after = np.linalg.norm(np.diff(means[order], axis=0), axis=1).mean()
    check("morton order shortens the mean step between neighbours",
          d_after < d_before, f"{d_after:.3f} < {d_before:.3f}")

    C.log("=" * 60)
    if fails:
        C.log(f"FAILED {len(fails)}: {fails}")
        return 1
    C.log("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
