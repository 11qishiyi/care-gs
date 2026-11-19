"""M23: geometry, coded again.

Two of this round's three changes are *lossless recodings*: they take the integers the current codec
already produces, store them in a different alphabet, and put them back bit for bit.  That is the point
-- the M20 probe showed the position offsets survive zstd untouched (22.99 MB -> 23.00 MB), which means
the block is coded in an alphabet where bytes carry no information that a byte-level coder can see.

The transform: Morton order makes consecutive primitives spatial neighbours, so the quantised levels of
one primitive predict the next.  Store deltas (int16) instead of levels, and give zstd small numbers
around zero instead of a uniform spread over the block's range.

``to_delta`` / ``from_delta`` are the whole of it.  ``apply`` rewrites a container's streams on the way
out, ``restore`` rewrites them on the way in, and ``m19_codec.decode`` calls ``restore`` when the meta
block says the file was written this way -- so there is still exactly one decoder.
"""

from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m4_bytes as M  # noqa: E402

#: stream name -> (source stream, attribute name in the spec, components, delta stream name)
TARGETS = {
    "geo_scales": ("geo_scales", "scales", 3, "geo_scales_d"),
    "geo_opacities": ("geo_opacities", "opacities", 1, "geo_opacities_d"),
}

#: streams measured and rejected: ``cluster_off`` is 10 bits packed (1.25 B/level), so a byte-aligned
#: int16 delta costs 2 B/level before zstd and measured +2.2 MB on the file (M23).  Kept here so the
#: next round does not re-try it.
REJECTED = {"cluster_off": "10-bit packed is 1.25 B/level; int16 deltas are 2 B and lost 2.2 MB"}


def to_delta(levels: np.ndarray) -> np.ndarray:
    """``(n, k)`` integers -> ``(n, k)`` first differences along Morton order, in int32."""
    a = np.asarray(levels)
    a = a.reshape(-1, 1) if a.ndim == 1 else a
    d = np.empty(a.shape, dtype=np.int32)
    d[0] = a[0]
    d[1:] = a[1:].astype(np.int32) - a[:-1].astype(np.int32)
    return d


def block_residual(levels: np.ndarray, size: int = M.CLUSTER_SIZE) -> tuple:
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


def narrow(d: np.ndarray, bits: int) -> tuple:
    """Store an 8-bit level stream's deltas as *modular* uint8: same width, lower entropy.

    An autocorrelation of 0.9 between neighbouring levels is worth nothing if exposing it costs 2 B
    instead of 1, which is what an int16 delta does (measured: scales went 18.40 MB -> 36.79 MB before
    zstd).  Modular arithmetic keeps the level width and lets zstd see small values near zero and near
    255 instead of a uniform spread.
    """
    if bits <= 8:
        return (d & 0xFF).astype(np.uint8), "u1"
    lo, hi = int(d.min()), int(d.max())
    if -128 <= lo and hi <= 127:
        return d.astype(np.int8), "i1"
    assert -32768 <= lo and hi <= 32767, f"delta does not fit int16: {lo}..{hi}"
    return d.astype("<i2"), "i2"


def from_delta(d: np.ndarray, count: int) -> np.ndarray:
    """Inverse of :func:`to_delta`; ``count`` is the number of levels (padded rows included)."""
    a = np.cumsum(np.asarray(d, dtype=np.int64), axis=0)
    return a[:count]


def _count(meta: dict, streams: dict, name: str, dim: int) -> int:
    """How many levels the packed stream holds (positions pad to a whole cluster)."""
    n = int(meta["n"])
    if name == "cluster_off":
        hdr = np.frombuffer(streams["cluster_hdr"], dtype=np.float32).reshape(-1, 6)
        return int(hdr.shape[0]) * M.CLUSTER_SIZE
    return n


def apply(meta: dict, streams: dict, mode: str = "delta") -> tuple:
    """Rewrite the geometry streams of a freshly encoded container as deltas."""
    import m19_codec as C
    import qfp_rd as Q

    spec = Q.parse_spec(meta["spec"])
    n = int(meta["n"])
    out = dict(streams)
    flags = {}
    for name, (_src, attr, dim, dname) in TARGETS.items():
        if name not in streams:
            continue
        bits = int(getattr(spec, "means_cluster_bits", 8) if attr == "means"
                   else spec.geo.get(attr, M.FP32_BITS))
        if bits >= M.FP32_BITS:
            continue                                    # not a grid-coded stream
        count = _count(meta, streams, name, dim)
        levels = C.unpack_bits(streams[name], bits, count * dim).reshape(count, dim)
        if mode == "block" and bits <= 8:
            d, means = block_residual(levels)
            out[dname] = d.tobytes()
            out[dname.replace("_d", "_bm")] = means.tobytes()
            flags[name] = {"bits": bits, "dim": dim, "count": count, "dtype": "block"}
        else:
            d, dtype = narrow(to_delta(levels), bits)
            out[dname] = d.tobytes()
            flags[name] = {"bits": bits, "dim": dim, "count": count, "dtype": dtype}
        out.pop(name, None)
    if not flags:
        return meta, out
    meta = dict(meta)
    meta["geo_delta"] = flags
    return meta, out


def restore(meta: dict, streams: dict) -> dict:
    """Rebuild the packed geometry streams so the ordinary decoder can read them."""
    import m19_codec as C

    flags = meta.get("geo_delta")
    if not flags:
        return streams
    out = dict(streams)
    for name, f in flags.items():
        dname = TARGETS[name][3]
        count, dim, bits = int(f["count"]), int(f["dim"]), int(f["bits"])
        if str(f.get("dtype")) == "block":
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
        d = np.frombuffer(out[dname], dtype=dt).astype(np.int64).reshape(count, dim)
        if dt == "u1":
            #: modular: the cumulative sum modulo 2**bits is the level sequence again
            levels = (np.cumsum(d, axis=0) & ((1 << bits) - 1)).astype(np.int64)
        else:
            levels = np.clip(from_delta(d, count), 0, (1 << bits) - 1).astype(np.int64)
        out[name] = M.pack_bits(levels.reshape(-1), bits)
        out.pop(dname, None)
    return out


def stream_table(meta: dict, streams: dict) -> list:
    """``(name, raw bytes, share)`` for the streams this round touches, for the report."""
    total = sum(len(v) for v in streams.values()
                if isinstance(v, (bytes, bytearray)) and not v.startswith(b"GS1"))
    rows = []
    for name in list(TARGETS) + [TARGETS[k][3] for k in TARGETS]:
        if name in streams and isinstance(streams[name], (bytes, bytearray)):
            rows.append((name, len(streams[name]), len(streams[name]) / max(1, total)))
    return sorted(rows, key=lambda r: -r[1])
