"""m4_bytes: measure the two-stage (rvq) payload exactly like the single-stage one."""
import io

B = r"D:\3dsg_1\experiments\m4_bytes.py"
b = io.open(B, encoding="utf-8").read()

b = b.replace(
    '''def _attribute_arrays(splats):''',
    '''def _codebook_pair(flat: np.ndarray, b1: int, b2: int, seed: int = 0):
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


def _attribute_arrays(splats):''', 1)

b = b.replace(
    '''    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
    if getattr(spec, "sh_vq_bits", None) is not None:''',
    '''    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
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

    if getattr(spec, "sh_vq_bits", None) is not None:''', 1)

io.open(B, "w", encoding="utf-8", newline="\n").write(b)
print("patched", len(b))
