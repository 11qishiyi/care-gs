"""M53 -- anchor + prediction prototype for the geometry block.

The question this answers, before any GPU is rented: can positions be coded as an anchor index plus a few
offset bits, and can the attribute block (quaternions, scales, opacity) be *predicted* from the anchor
instead of coded, at a bytes-per-primitive the mid-rate arithmetic can afford?  METHOD_PLAN.md's M53 spec
asks for <= 2.8 B/primitive of geometry at <= 0.4 dB loss; FRONTIER_BOUND.md §31 shows field-wise
coarsening alone floors at 4.71 B, so prediction has to carry the rest.

This file is deliberately not the shipping container.  It measures the same quantities (zstd-12 bytes per
stream on packed codes, and the reconstruction it writes back) with a tenth of the code, so that the round
can be decided on one node run instead of a plumbing project.

    python3 experiments/m53_anchor.py --ply in.ply --out recon.ply --mode p1 --json out.json
    python3 experiments/m53_anchor.py --selfcheck           # synthetic data, no file needed

Streams measured (all zstd level 12, the level the container uses):
    anchor_pos    3 x uint16 per anchor, over the scene box
    anchor_id     uint32 per primitive (Morton-sorted primitives, delta-coded)
    offsets       3 x offbits per primitive, packed
    quat_res      4 x attr_bits (smallest-three is a container detail; this measures the prediction)
    scale_res     3 x attr_bits
    opacity_res   1 x attr_bits
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

try:
    import zstandard as zstd
except Exception:  # pragma: no cover - zstd is on every node image
    zstd = None


# ----------------------------------------------------------------------------- helpers

def _zlen(buf: bytes, level: int = 12) -> int:
    """Compressed length, or the raw length when zstandard is unavailable (tests may skip it)."""
    if zstd is None or len(buf) == 0:
        return len(buf)
    return len(zstd.ZstdCompressor(level=level).compress(bytes(buf)))


def pack_bits(codes: np.ndarray, bits: int) -> bytes:
    """Pack an (N, k) integer array of `bits`-wide codes into a bit stream, row-major."""
    codes = np.asarray(codes, dtype=np.uint64)
    n, k = codes.shape
    flat = codes.reshape(-1)
    out = np.zeros((flat.size * bits + 7) // 8, dtype=np.uint8)
    bitpos = 0
    for v in flat:  # deliberately simple: this measures bytes, not speed
        byte = bitpos // 8
        shift = bitpos % 8
        chunk = int(v) << shift
        for i in range((bits + shift + 7) // 8):
            out[byte + i] |= (chunk >> (8 * i)) & 0xFF
        bitpos += bits
    return out.tobytes()


def quantise(values: np.ndarray, bits: int, lo=None, hi=None):
    """Uniform quantisation over [lo, hi] to `bits`; returns codes, reconstruction, range."""
    v = np.asarray(values, dtype=np.float64)
    lo = float(np.min(v)) if lo is None else float(lo)
    hi = float(np.max(v)) if hi is None else float(hi)
    span = max(hi - lo, 1e-12)
    levels = (1 << bits) - 1
    codes = np.clip(np.rint((v - lo) / span * levels), 0, levels).astype(np.uint32)
    recon = codes.astype(np.float64) / levels * span + lo
    return codes, recon, (lo, hi)


def _h0_bits(codes: np.ndarray) -> float:
    """Order-0 entropy of an integer code stream, in bits per code."""
    flat = np.asarray(codes).reshape(-1)
    if flat.size == 0:
        return 0.0
    _, counts = np.unique(flat, return_counts=True)
    p = counts.astype(np.float64) / flat.size
    return float(-(p * np.log2(p)).sum())


def vq(residuals: np.ndarray, k: int = 256, iters: int = 12, seed: int = 0,
       fit_sample: int = 20000, chunk: int = 200000):
    """Mini-batch k-means over residual vectors; returns (codes, centroids).

    Joint vector quantisation is the mechanism anchor coders use for the attribute block: one code per primitive
    instead of one scalar per component.  Fitting uses a 20 k sample so a 6 M-primitive model stays inside a few
    hundred MB; assignment over the full set is chunked for the same reason.
    """
    rng = np.random.default_rng(seed)
    n, d = residuals.shape
    k = int(min(k, max(1, n)))
    sample = residuals if n <= fit_sample else residuals[rng.choice(n, size=fit_sample, replace=False)]
    C = sample[rng.choice(len(sample), size=k, replace=False)].copy()
    for _ in range(iters):
        d2 = ((sample[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        codes = d2.argmin(1)
        for j in range(k):
            m = codes == j
            if m.any():
                C[j] = sample[m].mean(0)
    out = np.empty(n, dtype=np.int32)
    for s in range(0, n, chunk):
        blk = residuals[s:s + chunk]
        dd = ((blk[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        out[s:s + chunk] = dd.argmin(1)
    return out, C


def estimate_spacing(means: np.ndarray, sample: int = 4000, seed: int = 0) -> float:
    """Typical spacing between primitives, from the primitive density (0.554 / lambda^(1/3)).

    Round 46 replaced the subsample nearest-neighbour estimate this used to do: for a clustered model a 4 000-point
    random subsample almost never contains a same-cluster point, so the "nearest neighbour" it measured was the
    inter-cluster distance - 20x too large on the test scene, which made the cell 20x too big and the offsets 20x
    too coarse.  The density estimate is O(n), has no subsample bias, and agrees with the old one on a uniform cloud.
    """
    m = np.asarray(means, dtype=np.float64)
    n = len(m)
    if n < 4:
        return 1.0
    lo, hi = m.min(axis=0), m.max(axis=0)
    vol = float(np.prod(np.clip(hi - lo, 1e-9, None)))
    density = n / max(vol, 1e-12)
    return float(0.55396 * density ** (-1.0 / 3.0))


def build_clusters(means: np.ndarray, group: int = 256):
    """Count-based clustering in Morton order — the shipping container's own layout.

    Round 46 concluded that a spatial grid is the wrong grouping for 3DGS data (surfaces plus floaters), so this
    follows the container: sort primitives along a Morton curve, cut every `group` of them into one cluster, and code
    offsets inside the cluster's own bounding box.  Two consequences the grid could not give:

    * **no per-primitive anchor index** — the cluster is implied by position in the stream, which removes the ~4 B
      per primitive the grid-anchor version spent on ids;
    * the bbox is local, so a fixed bit width buys a much finer step than a global cell does.

    Returns (cluster_of_primitive, cluster_mean, cluster_lo, cluster_extent, order, counts).
    """
    m = np.asarray(means, dtype=np.float64)
    n = len(m)
    lo, hi = m.min(axis=0), m.max(axis=0)
    span = np.clip(hi - lo, 1e-9, None)
    q = np.clip(((m - lo) / span * ((1 << 20) - 1)).astype(np.int64), 0, (1 << 20) - 1)

    def spread(v):  # 3-way bit interleave, 20 bits each -> 60-bit Morton code
        code = np.zeros(len(v), dtype=np.uint64)
        for b in range(20):
            code |= ((v[:, 0] >> b) & 1).astype(np.uint64) << np.uint64(3 * b)
            code |= ((v[:, 1] >> b) & 1).astype(np.uint64) << np.uint64(3 * b + 1)
            code |= ((v[:, 2] >> b) & 1).astype(np.uint64) << np.uint64(3 * b + 2)
        return code

    order = np.argsort(spread(q), kind="stable")
    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n)
    cluster_of = rank // int(group)
    n_cluster = int(cluster_of.max()) + 1
    cluster_mean = np.zeros((n_cluster, 3))
    cluster_lo = np.zeros((n_cluster, 3))
    cluster_extent = np.zeros((n_cluster, 3))
    counts = np.bincount(cluster_of, minlength=n_cluster).astype(np.float64)
    for axis in range(3):
        cluster_mean[:, axis] = np.bincount(cluster_of, weights=m[:, axis], minlength=n_cluster) / counts
        cluster_lo[:, axis] = np.minimum.reduceat(m[order, axis], np.arange(0, n, int(group)))
        cluster_extent[:, axis] = (np.maximum.reduceat(m[order, axis], np.arange(0, n, int(group)))
                                   - cluster_lo[:, axis])
    return cluster_of, cluster_mean, cluster_lo, np.clip(cluster_extent, 1e-9, None), order, counts


def build_anchors(means: np.ndarray, cell: float):
    """Grid anchors: one anchor per occupied cell.

    Returns (anchor_of_primitive, anchor_mean, anchor_centre, counts).  The **centre** is what positions are coded
    against, and the **mean** is what attributes are predicted from.

    Round 46 found why that distinction matters: coding offsets around the cell *mean* clips any primitive that sits
    near a cell corner (up to 0.87 cell away), and 1 % of primitives were displaced by ~1 world unit — enough to drop
    the render from 24.52 to 12 dB.  Around the centre every member is inside ±cell/2 by construction, so the offset
    quantiser is the only error.
    """
    m = np.asarray(means, dtype=np.float64)
    lo = m.min(axis=0)
    ijk = np.floor((m - lo) / cell).astype(np.int64)
    # unique cells, deterministic order
    keys = ijk[:, 0] * (1 << 42) + ijk[:, 1] * (1 << 21) + ijk[:, 2]
    order = np.argsort(keys, kind="stable")
    sorted_keys = keys[order]
    starts = np.flatnonzero(np.r_[True, sorted_keys[1:] != sorted_keys[:-1]])
    uniq = sorted_keys[starts]
    anchor_of = np.empty(len(m), dtype=np.int64)
    anchor_of[order] = np.repeat(np.arange(len(uniq)), np.diff(np.r_[starts, len(m)]))
    anchor_pos = np.zeros((len(uniq), 3), dtype=np.float64)
    counts = np.bincount(anchor_of, minlength=len(uniq)).astype(np.float64)
    for axis in range(3):
        anchor_pos[:, axis] = np.bincount(anchor_of, weights=m[:, axis], minlength=len(uniq)) / counts
    uniq_ijk = np.stack([(uniq >> 42) & ((1 << 21) - 1), (uniq >> 21) & ((1 << 21) - 1),
                         uniq & ((1 << 21) - 1)], axis=1)
    anchor_centre = lo + (uniq_ijk.astype(np.float64) + 0.5) * cell
    return anchor_of, anchor_pos, anchor_centre, counts


# ----------------------------------------------------------------------------- prediction

def _anchor_features(anchor_pos, counts, anchor_mean_s, anchor_mean_o, anchor_mean_q):
    """Per-anchor features: where the anchor is, how crowded, and what it looks like on average."""
    return np.concatenate([
        anchor_pos,
        np.stack([np.log1p(counts), np.log1p(counts) ** 2], axis=1),
        anchor_mean_s,
        anchor_mean_o[:, None],
        anchor_mean_q,
    ], axis=1)


def _ridge(X: np.ndarray, Y: np.ndarray, lam: float = 1e-3) -> np.ndarray:
    A = X.T @ X + lam * np.eye(X.shape[1])
    return np.linalg.solve(A, X.T @ Y)


def predict_attributes(quats, log_scales, logit_opac, anchor_of, anchor_pos, counts, pos_recon, mode: str):
    """P0: anchor mean.  P1: ridge on anchor features *and the primitive's offset inside its cell*.

    The offset is a decoder-side quantity (it is already in the position stream), so using it is fair.
    The ridge is fitted on the even-indexed primitives and applied to all of them, so half the data is
    always held out from the fit.
    """
    n_anchor = len(anchor_pos)
    cnt = np.bincount(anchor_of, minlength=n_anchor).astype(np.float64).clip(1.0)
    q_mean = np.stack([np.bincount(anchor_of, weights=quats[:, i], minlength=n_anchor) / cnt
                       for i in range(4)], axis=1)
    s_mean = np.stack([np.bincount(anchor_of, weights=log_scales[:, i], minlength=n_anchor) / cnt
                       for i in range(3)], axis=1)
    o_mean = np.bincount(anchor_of, weights=logit_opac, minlength=n_anchor) / cnt
    if mode == "p0":
        return q_mean[anchor_of], s_mean[anchor_of], o_mean[anchor_of]
    if mode != "p1":
        raise SystemExit(f"unknown mode {mode}")
    Xa = _anchor_features(anchor_pos, counts, s_mean, o_mean, q_mean)
    X = np.concatenate([Xa[anchor_of], np.asarray(pos_recon, np.float64)], axis=1)
    Y = np.concatenate([quats, log_scales, logit_opac[:, None]], axis=1)
    fit = np.zeros(len(Y), dtype=bool)
    fit[::2] = True
    W = _ridge(X[fit], Y[fit])
    P = X @ W
    return P[:, 0:4], P[:, 4:7], P[:, 7]


# ----------------------------------------------------------------------------- codec

def encode_geometry(means, quats, log_scales, logit_opac, k: float, offbits: int, attr_bits: int,
                    mode: str = "p1", level: int = 12, vq_k: int = 0, group: int = 0) -> dict:
    means = np.asarray(means, np.float64)
    quats = np.asarray(quats, np.float64)
    log_scales = np.asarray(log_scales, np.float64)
    logit_opac = np.asarray(logit_opac, np.float64).reshape(-1)

    spacing = estimate_spacing(means)
    cell = k * spacing
    if group and group > 1:
        #: count-based clusters, the container's layout: no per-primitive anchor id, local bounding box
        anchor_of, anchor_pos, cluster_lo, cluster_extent, order, counts = build_clusters(means, group)
        means = means[order]
        quats = quats[order]
        log_scales = log_scales[order]
        logit_opac = logit_opac[order]
        anchor_of = anchor_of[order]
        origin = cluster_lo[anchor_of]
        ext = np.maximum(cluster_extent[anchor_of], 1e-9)
    else:
        anchor_of, anchor_pos, anchor_centre, counts = build_anchors(means, cell)

        # --- order primitives by anchor before coding anything.
        # A per-primitive anchor index costs ~4 B/primitive if the model order is arbitrary (the first measured run
        # spent 7.7 B/primitive on the position block because of it).  Sorting by anchor makes the index stream
        # piecewise constant; the reconstructed model is written in the sorted order, which changes no pixel.
        order = np.argsort(anchor_of, kind="stable")
        means = means[order]
        quats = quats[order]
        log_scales = log_scales[order]
        logit_opac = logit_opac[order]
        anchor_of = anchor_of[order]
        origin = anchor_centre[anchor_of] - cell / 2.0
        ext = cell

    # --- positions: origin + offset, where the origin is the cell/cluster box minimum
    a_lo = origin.min(axis=0)
    a_hi = origin.max(axis=0)
    a_codes = np.zeros(origin.shape, dtype=np.uint32)
    a_recon = np.zeros_like(origin)
    for axis in range(3):
        codes, recon, _ = quantise(origin[:, axis], 16, a_lo[axis], a_hi[axis])
        a_codes[:, axis] = codes
        a_recon[:, axis] = recon
    origin = a_recon
    delta = means - origin
    frac = np.clip(delta / ext, 0.0, 1.0)
    levels = (1 << offbits) - 1
    off_codes = np.clip(np.rint(frac * levels), 0, levels).astype(np.uint32)
    off_recon = (off_codes.astype(np.float64) / levels) * ext
    means_recon = origin + off_recon

    # --- attributes: predict, then quantise the residual
    q_pred, s_pred, o_pred = predict_attributes(quats, log_scales, logit_opac, anchor_of,
                                                anchor_pos, counts, means_recon, mode)
    #: The quantiser step is fixed by the *raw* field's range and the width the container uses, and it is the
    #: same for P0 and P1.  Prediction therefore cannot cheat by rescaling its own residual: it only makes the
    #: residual codes smaller, which is what an entropy coder (or a per-cluster alphabet) would cash in.
    def res_codes(res, raw):
        step = max(float(np.ptp(raw)) / ((1 << attr_bits) - 1), 1e-12)
        codes = np.clip(np.rint(res / step), -32768, 32767).astype(np.int16)
        return codes, codes.astype(np.float64) * step, step

    q_codes, q_recon, q_step = res_codes(quats - q_pred, quats)
    s_codes, s_recon, s_step = res_codes(log_scales - s_pred, log_scales)
    o_codes, o_recon, o_step = res_codes(logit_opac - o_pred, logit_opac)
    quats_recon = q_pred + q_recon
    quats_recon /= np.linalg.norm(quats_recon, axis=1, keepdims=True).clip(1e-12)
    scales_recon = s_pred + s_recon
    opac_recon = o_pred + o_recon

    # --- streams
    a_bytes = a_codes.astype(np.uint16).tobytes()
    id_delta = np.diff(anchor_of.astype(np.int64), prepend=0)
    id_bytes = np.clip(id_delta, 0, 2 ** 32 - 1).astype(np.uint32).tobytes()
    off_bytes = pack_bits(off_codes, offbits)
    #: attribute residuals go out byte-aligned and entropy-coded; both the zstd length and the order-0
    #: bound are reported, because the bound is what a context coder could reach and zstd is what we ship.
    attr_streams = {}
    for name, codes in (("quat_res", q_codes), ("scale_res", s_codes), ("opacity_res", o_codes.reshape(-1))):
        buf = codes.astype("<i2").tobytes()
        attr_streams[name] = _zlen(buf, level)
        attr_streams[name + "_h0"] = int(round(_h0_bits(codes) * codes.size / 8.0))
    streams = {
        "anchor_pos": _zlen(a_bytes, level),
        "anchor_id": _zlen(id_bytes, level),
        "offsets": _zlen(off_bytes, level),
        "quat_res": attr_streams["quat_res"],
        "scale_res": attr_streams["scale_res"],
        "opacity_res": attr_streams["opacity_res"],
    }
    #: Optional joint vector quantisation of the attribute residual: one code per primitive instead of one scalar
    #: per component, which is how anchor coders buy the attribute block down.  Reported as its own pair of streams
    #: (codes + codebook) so the comparison against the scalar path is byte-for-byte.
    vq_streams = {}
    if vq_k and vq_k > 1:
        res_mat = np.concatenate([quats - q_pred, log_scales - s_pred, (logit_opac - o_pred)[:, None]], axis=1)
        codes, cent = vq(res_mat, k=vq_k, seed=0)
        recon_mat = cent[codes]
        quats_recon = q_pred + recon_mat[:, 0:4]
        quats_recon /= np.linalg.norm(quats_recon, axis=1, keepdims=True).clip(1e-12)
        scales_recon = s_pred + recon_mat[:, 4:7]
        opac_recon = o_pred + recon_mat[:, 7]
        idx_dtype = np.uint8 if vq_k <= 256 else np.uint16
        vq_streams = {
            "attr_vq_codes": _zlen(codes.astype(idx_dtype).tobytes(), level),
            "attr_vq_codebook": _zlen(cent.astype("<f4").tobytes(), level),
            "attr_vq_codes_h0": int(round(_h0_bits(codes) * codes.size / 8.0)),
        }
    n = len(means)
    attr_bytes = (vq_streams["attr_vq_codes"] + vq_streams["attr_vq_codebook"]) if vq_streams else (
        streams["quat_res"] + streams["scale_res"] + streams["opacity_res"])
    geom = streams["anchor_pos"] + streams["anchor_id"] + streams["offsets"] + attr_bytes
    pos_err = float(np.sqrt(((means_recon - means) ** 2).sum(1)).mean())
    geom_h0 = (streams["anchor_pos"] + streams["anchor_id"] + streams["offsets"] +
               attr_streams["quat_res_h0"] + attr_streams["scale_res_h0"] + attr_streams["opacity_res_h0"])
    return {
        "n": int(n), "anchors": int(len(anchor_pos)), "cell": float(cell), "spacing": spacing,
        "geometry_bytes_h0": int(geom_h0), "geometry_b_per_prim_h0": geom_h0 / n,
        "attr_streams_h0": {k: v for k, v in attr_streams.items() if k.endswith("_h0")},
        "k": k, "offbits": offbits, "attr_bits": attr_bits, "mode": mode,
        "streams": streams, "geometry_bytes": int(geom),
        "geometry_b_per_prim": geom / n,
        "pos_stream_b_per_prim": (streams["anchor_pos"] + streams["anchor_id"] + streams["offsets"]) / n,
        "attr_stream_b_per_prim": ((sum(vq_streams[k] for k in ("attr_vq_codes", "attr_vq_codebook")) if vq_streams
                                    else streams["quat_res"] + streams["scale_res"] + streams["opacity_res"]) / n),
        "vq_k": int(vq_k or 0), "vq_streams": vq_streams,
        "pos_rmse": pos_err,
        "attr_rmse": {
            "quat": float(np.abs(quats_recon - quats).mean()),
            "log_scale": float(np.abs(scales_recon - log_scales).mean()),
            "logit_opac": float(np.abs(opac_recon - logit_opac).mean()),
        },
        "raw_range": {
            "log_scale": float(np.ptp(log_scales)),
            "logit_opac": float(np.ptp(logit_opac)),
        },
        "anchor_quant_step": float(np.mean((a_hi - a_lo) / 65535.0)),
        "offset_step": float(cell / levels),
        "steps": {"quat": q_step, "scale": s_step, "opacity": o_step},
        "_recon": dict(means=means_recon, quats=quats_recon, scales=scales_recon, opacities=opac_recon),
        "_order": order,
    }


# ----------------------------------------------------------------------------- CLI

def _selfcheck() -> int:
    rng = np.random.default_rng(7)
    n = 4000
    means = rng.normal(size=(n, 3))
    quats = rng.normal(size=(n, 4))
    quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    scales = rng.normal(size=(n, 3)) * 0.1
    opac = rng.normal(size=n)
    for mode, vqk in (("p0", 0), ("p1", 0), ("p1", 64), ("p1", 256)):
        out = encode_geometry(means, quats, scales, opac, k=4.0, offbits=4, attr_bits=6, mode=mode, vq_k=vqk)
        print(f"{mode} vq={vqk or '-'}: geometry {out['geometry_b_per_prim']:.2f} B/prim "
              f"(pos {out['pos_stream_b_per_prim']:.2f}, attr {out['attr_stream_b_per_prim']:.2f}), "
              f"anchors {out['anchors']}, pos_rmse {out['pos_rmse']:.4f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ply")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--k", type=float, default=4.0, help="cell size in units of the median spacing")
    ap.add_argument("--offbits", type=int, default=4)
    ap.add_argument("--attr-bits", type=int, default=6)
    ap.add_argument("--mode", default="p1", choices=("p0", "p1"))
    ap.add_argument("--vq", type=int, default=0, help="joint VQ codebook size for the attribute residual (0 = scalar)")
    ap.add_argument("--group", type=int, default=0, help="count-based cluster size (0 = spatial grid anchors)")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck or not a.ply:
        return _selfcheck()

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "code"))
    from calib.plyio import load_inria_ply, save_inria_ply

    d = load_inria_ply(a.ply)
    out = encode_geometry(d["means"], d["quats"], np.log(np.clip(d["scales"], 1e-12, None)),
                          np.log(np.clip(d["opacities"], 1e-6, 1 - 1e-6) /
                                 (1 - np.clip(d["opacities"], 1e-6, 1 - 1e-6))),
                          k=a.k, offbits=a.offbits, attr_bits=a.attr_bits, mode=a.mode, vq_k=a.vq, group=a.group)
    rec = out.pop("_recon")
    order = out.pop("_order", None)
    rec["opacities"] = 1.0 / (1.0 + np.exp(-np.clip(rec["opacities"], -30, 30)))
    rec["scales"] = np.exp(np.clip(rec["scales"], -30, 30))
    if a.out:
        sh0, shN = d["sh0"], d["shN"]
        if order is not None:
            # the prototype sorts primitives by anchor before coding; the colour block must follow the same
            # permutation, otherwise each Gaussian carries another Gaussians colour
            sh0 = sh0[order]
            shN = shN[order] if shN is not None and len(shN) else shN
        save_inria_ply(a.out, rec["means"], rec["scales"], rec["quats"], rec["opacities"], sh0, shN)
    print(json.dumps({k: v for k, v in out.items()}, indent=1))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
