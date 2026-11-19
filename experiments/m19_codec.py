"""M19: turn the byte model into a format you can actually hand to somebody.

Every ratio this series has reported comes from `m4_bytes`, which counts the bytes of the streams a
decoder would read.  It never wrote those streams to disk, and no decoder existed -- `m16_timing.py`
reports `decode_s = null` for exactly that reason.  Two things fall out of that hole:

1. **The streams were not self-contained.**  `codes_grid` normalises each attribute by its own
   min/step and never stores them, and the 3-bit SH ladder divides per-primitive scales by a
   scene-wide ``ref`` that is also not stored.  A decoder cannot invert either.  This module adds
   ``geo_hdr`` (the per-component min/step of the coded attributes) and ``sh_hdr`` (the two SH
   reference scales), so the file stands alone.
2. **Decode cost and size were unmeasured**, which are two of the dimensions the paper compares on.

The container is deliberately boring: a magic, a JSON table, and one zstd frame per stream.
Streams stay independent so a damaged frame costs one attribute and not the asset -- the M19b
robustness measurements rely on that.

Usage::

    python experiments/m19_codec.py --selftest
    python experiments/m19_codec.py --archive ... --scenes bicycle --specs c10_o8_sh3 \\
        --out /tmp/x.gs1 --timing
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m4_bytes as M  # noqa: E402

MAGIC = b"GS1\x00"
VERSION = 1
#: Frames are cut so that a damaged region costs one frame and not the file.  One zstd frame per
#: asset is the obvious implementation and the wrong one: a single flipped byte makes the whole
#: frame unrecoverable, so 1 % damage would cost 100 % of the model.  Each frame also carries a
#: CRC32, so a damage is *detected* rather than decoded into plausible-looking garbage -- without
#: the checksum a corrupted frame either raises (lucky) or silently produces wrong floats
#: (unlucky), and a format cannot rely on which.
CHUNK = 1 << 18
MAX_FRAMES = 512
#: ...but a frame has to be big enough that splitting does not throw away zstd's cross-stream context.
#: One 25 MB stream in 64 frames cost 2.3 % of the file (measured, M19 first pass); a 4 MB floor
#: brings that under 0.3 % and still leaves a 1 % damage confined to one frame of a bulk stream.
#: M34 then measured the boundary itself: a 4 MB frame is 96 % of bonsai's whole colour block, so losing
#: one frame cost 3.09 dB there, while 256 KB frames cost 0.14 dB -- and M40 measured the byte cost of the
#: finer boundary on three scenes as +0.05 % / +0.09 % / -0.03 %.  The default is therefore 256 KB: same
#: bytes, and the damage a lost frame does is set by the frame, not by the size of the model's colour block.
MIN_FRAME = 256 << 10
#: Attribute order in the container's stream table, so two encoders emit the same file.
ORDER = ("geo_hdr", "geo_means", "cluster_hdr", "cluster_off", "sh_hdr", "sh_scale",
         "geo_scales", "geo_quats", "geo_opacities", "geo_quat_which", "geo_quat_abc",
         #: M38 -- one joint codebook over the four attribute groups replaces the four streams above
         "geo_vq_cb", "geo_vq_idx",
         "sh_dc", "sh_rest",
         #: Rate-scalable files (M21) replace ``sh_rest`` with three bit-planes written most
         #: significant first, so a prefix of the payload is a complete model at lower colour
         #: precision instead of a model with some primitives missing.  The LUT comes first: its
         #: 1.3 kB is what makes the coarse steps worth rendering.
         "sh_lut", "sh_rest_p2", "sh_rest_p1", "sh_rest_p0",
         #: M22: shared colour basis -- the rest block as ``rank`` coefficients per primitive.
         "sh_basis", "sh_basis_mean", "sh_basis_comp", "sh_coef_bits", "sh_coef_ref", "sh_coef_lvl", "sh_coef",
         #: M23: geometry recoded as Morton-order deltas (lossless: the levels come back identical).
         "cluster_off_d", "geo_scales_d", "geo_opacities_d",
         "geo_scales_bm", "geo_opacities_bm",
         "sh_index", "sh_cb_hdr", "sh_cb_centroids",
         #: M27: anchor representation -- one attribute record per voxel (``a_*``) and an offset plus
         #: a DC code per primitive.  These names were missing from this tuple on the first run of
         #: M27, and ``write_container`` silently dropped every one of them: the same defect N32 was
         #: written about, in the same file, one round later.  ``write_container`` now refuses
         #: unknown streams instead of dropping them.
         "a_org", "a_vox", "a_count", "a_off",
         "a_scale", "a_scale_hdr", "a_opac", "a_opac_hdr",
         "a_quat_which", "a_quat_abc",
         "a_dc", "a_dc_lvl", "a_dc_lvl_hdr",
         "a_basis", "a_basis_mean", "a_coef", "a_coef_comp", "a_coef_bits",
         #: ... and the same attributes kept per primitive when the ablation asks for them (M27's
         #: "which attribute cannot be shared" arms).  The guard below caught these two names on the
         #: very first ablation run, which is the point of having it.
         "p_scale", "p_scale_hdr", "p_opac", "p_opac_hdr", "p_quat_which", "p_quat_abc",
         #: The multi-stage colour coder (``msc``) writes these; this decoder does not implement it
         #: and says so, but the writer must still carry them rather than drop them (`m19 selftest`
         #: reaches the "refused with a reason" path only if the bytes are actually in the file).
         "msc_modes", "sh_scalar_codes", "sh_scalar_scale", "cluster_bits",
         #: M28: predicted anchors -- the network that turns an anchor record plus a per-primitive
         #: offset into that primitive's attributes.  The weights are part of the file.
         "m28_w")
#: Plane streams in the order they are written (coarsest first).
SH_PLANES = ("sh_rest_p2", "sh_rest_p1", "sh_rest_p0")


def split_sh_planes(streams: dict, n: int = None, ncols: int = None) -> dict:
    """Replace ``sh_rest`` (one byte per code) by three 1-bit planes, MSB first, plus a tiny LUT.

    The information is the same three bits per coefficient; what changes is that the bits are
    *separable* -- a reader that only has the first plane can still decode every primitive, with
    colour quantised to the two outermost levels, so truncating the file degrades quality instead
    of punching holes.  Cost: the planes no longer share one zstd block, so the file grows by a few
    per cent (measured in M21).

    The LUT is what makes the coarser steps usable.  Reconstructing an unknown low bit as the
    midpoint of its bin is only right if codes are uniform inside a bin, and SH coefficients are
    not: they pile up near the signed zero, so the midpoint estimate of a truncated code is
    systematically too large (measured: the one-plane prefix was *worse* than no colour at all).
    The encoder therefore stores the mean code for each prefix pattern (7 bins x ncols float32,
    1.3 kB on a 45-column block), which is the Lloyd-Max reconstruction level conditioned on the
    bits that survived.
    """
    if "sh_rest" not in streams or not streams["sh_rest"]:
        return dict(streams)
    out = {k: v for k, v in streams.items() if k != "sh_rest"}
    codes = np.frombuffer(streams["sh_rest"], dtype=np.uint8)
    if n is not None and ncols is not None:
        c = codes.reshape(n, ncols)
        lut = [c.mean(axis=0, keepdims=True).astype(np.float32)]
        for k in (1, 2):
            nb = 1 << k
            h = (c >> (3 - k))
            t = np.empty((nb, ncols), dtype=np.float32)
            for b in range(nb):
                sel = c[h == b]
                t[b] = sel.mean(axis=0) if sel.size else float(b << (3 - k))
            lut.append(t)
        out["sh_lut"] = np.concatenate(lut, axis=0).tobytes()
    for i, name in enumerate(reversed(SH_PLANES)):  # p0 first in code space, p2 written first
        out[name] = ((codes >> i) & 1).astype(np.uint8).tobytes()
    return out

#: dims of the coded attributes, used for the header layout and for reshaping codes.
DIMS = {"means": 3, "scales": 3, "quats": 4, "opacities": 1}


# ---------------------------------------------------------------------------
# bit packing (inverse of m4_bytes.pack_bits)
# ---------------------------------------------------------------------------


def unpack_bits(buf: bytes, bits: int, count: int, dtype=None) -> np.ndarray:
    """Inverse of :func:`m4_bytes.pack_bits`: ``count`` unsigned codes at ``bits`` bits.

    ``dtype`` lets a caller that only needs the values ask for the narrowest type that holds them:
    a 6 M-primitive colour block is 0.8 GB of int64 codes and 0.1 GB of uint8 codes, and the
    decoder's peak footprint is decided by choices like this one.
    """
    bits = int(bits)
    dt = np.dtype(dtype) if dtype is not None else np.int64
    if bits == 8:
        return np.frombuffer(buf, dtype=np.uint8, count=count).astype(dt)
    if bits == 16:
        return np.frombuffer(buf, dtype=np.uint16, count=count).astype(dt)
    if bits == 32:
        return np.frombuffer(buf, dtype=np.uint32, count=count).astype(dt)
    need = (count * bits + 7) // 8
    raw = np.frombuffer(buf[:need], dtype=np.uint8)
    #: ``unpackbits`` expands to one byte per bit and the accumulate step needs two more bytes per
    #: code, so a 48-bit colour block costs ~880 MB of temporaries if it is done in one go.  Fill the
    #: answer in slices instead: the peak then depends on the slice, not on the asset.
    out = np.empty(count, dtype=dt)
    acc = np.uint16 if bits <= 8 else np.uint32
    shifts = np.arange(bits, dtype=acc)[None, :]
    step = max(1, (1 << 21) // max(1, bits))
    for i in range(0, count, step):
        j = min(count, i + step)
        lo, hi = (i * bits) // 8, (j * bits + 7) // 8
        blk = np.unpackbits(raw[lo:hi])
        want = (j - i) * bits
        #: the slice starts at a bit offset inside the first byte
        off = (i * bits) % 8
        blk = blk[off:off + want].reshape(j - i, bits)
        out[i:j] = (blk.astype(acc) << shifts).sum(axis=1)
    return out


def _sh_codes(buf: bytes, bits: int, n: int, ncols: int, layout: str, dtype=None) -> np.ndarray:
    """``(n, ncols)`` unsigned SH codes from whichever layout the header names.

    ``dtype`` is passed through so the decoder can ask for uint8 rather than int64 (M25: for a 6 M
    primitive asset the difference between those two is 0.8 GB of resident memory).
    """
    dt = np.dtype(dtype) if dtype is not None else np.int64
    if layout == "bits":
        return unpack_bits(buf, bits, n * ncols, dtype=dt).reshape(n, ncols)
    if layout == "bytes":
        return np.frombuffer(buf, dtype=np.uint8, count=n * ncols).reshape(n, ncols).astype(dt)
    if layout == "bytes_coef":
        return np.frombuffer(buf, dtype=np.uint8, count=n * ncols).reshape(ncols, n).T.astype(dt)
    raise ValueError(f"unknown SH layout {layout!r}")


# ---------------------------------------------------------------------------
# side information the encoder used to throw away
# ---------------------------------------------------------------------------


def geo_header(geo: dict, spec) -> bytes:
    """Alias of :func:`m4_bytes.geo_header_bytes`.

    The encoder owns the layout (it charges for the bytes), so the writer must not keep a second
    copy of the same arithmetic that could drift from it.
    """
    return M.geo_header_bytes(geo, spec)


def decode_geo_header(buf: bytes, spec) -> dict:
    """Inverse of :func:`geo_header`: attribute -> (mn, step) as float64 row vectors."""
    out = {}
    off = 0
    for attr in ("means", "scales", "quats", "opacities"):
        if attr == "means" and getattr(spec, "means_cluster_bits", None) is not None:
            continue
        bits = int(spec.geo.get(attr, M.FP32_BITS))
        if bits >= M.FP32_BITS:
            continue
        d = DIMS[attr]
        mn = np.frombuffer(buf[off:off + 4 * d], dtype=np.float32).astype(np.float64)[None, :]
        off += 4 * d
        step = np.frombuffer(buf[off:off + 4 * d], dtype=np.float32).astype(np.float64)[None, :]
        off += 4 * d
        out[attr] = (mn, step)
    return out


def sh_header(streams: dict, block_scales: list):
    """Reference scales for the 3-bit ladder; ``None`` when the spec codes SH another way."""
    if not block_scales:
        return None, b""
    ref = np.maximum(np.stack(block_scales, axis=1).max(axis=0, keepdims=True), 1e-12)
    lvl = np.clip(np.rint(np.stack(block_scales, axis=1) / ref * 255.0), 0, 255).astype(np.int64)
    return lvl, np.asarray(ref, dtype=np.float32).tobytes()


# ---------------------------------------------------------------------------
# container
# ---------------------------------------------------------------------------


def _ordered_names(streams: dict) -> list:
    """``ORDER`` first, then the M29 split buckets right after their base stream."""
    names = []
    for name in ORDER:
        if name in streams:
            names.append(name)
        #: the split buckets stand in for the base stream, so they are emitted even when the base
        #: name itself is absent from the dict (that is the normal case)
        parts = sorted((k for k in streams if k.startswith(name + "#")),
                       key=lambda s: int(s.split("#")[1]))
        names.extend(parts)
    for k in streams:                     # anything ORDER does not know is refused above
        if k not in names and k.split("#")[0] not in ORDER:
            names.append(k)
    return names


def _compress_frames(chunks, level: int, jobs: int = 1):
    """Compress frame payloads, preserving order.

    The frames of a container share nothing: each is an independent zstd call over a contiguous slice of one
    stream.  So the encoder's wall clock is a scheduling artefact, and the only thing a pool can break is the
    order -- which is why the result is a list, built in input order, and why M41's first criterion is that the
    file is byte-identical at every ``jobs``.
    """
    if jobs and int(jobs) > 1 and len(chunks) > 1:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=int(jobs)) as ex:
            return list(ex.map(lambda c: M._zstd(c, level), chunks))
    return [M._zstd(c, level) for c in chunks]


def write_container(path: str, streams: dict, meta: dict, level: int = 12, jobs: int = 1) -> dict:
    """Write ``streams`` as one file; returns the size bookkeeping the paper reports."""
    import zlib

    meta = dict(meta)
    table, blobs = [], []
    #: M29: a context-split stream is ``<name>#<bucket>``; its base name has to be in ORDER
    unknown = [k for k in streams if k not in ORDER and k.split("#")[0] not in ORDER]
    if unknown:
        #: A stream the writer does not know about is a stream the reader will never see.  Silently
        #: dropping it is how M27's first container lost every anchor; failing here costs one line.
        raise KeyError(f"streams not in ORDER (they would be dropped): {sorted(unknown)}")
    for name in _ordered_names(streams):
        raw = streams[name]
        #: Small streams stay in one frame (a header is 64 B); bulk streams are split so a lost
        #: frame costs about 1/64 of one attribute instead of all of it.
        nf = min(MAX_FRAMES, max(1, (len(raw) + CHUNK - 1) // CHUNK))
        step = max(MIN_FRAME, (len(raw) + nf - 1) // nf) if nf else len(raw)
        cuts = list(range(0, max(1, len(raw)), max(1, step)))
        frames = _compress_frames([raw[i:i + step] for i in cuts], level, jobs)
        crcs = [zlib.crc32(f) & 0xFFFFFFFF for f in frames]
        table.append({"name": name, "raw": len(raw), "comp": sum(len(f) for f in frames),
                      "frames": [len(f) for f in frames], "crc": crcs,
                      #: Raw size of each frame, so a reader that lost one knows *which* bytes of
                      #: the decoded attribute are missing and can fill them with a neutral value
                      #: instead of zeros.  Zeros are not neutral for a signed code: they decode to
                      #: the most negative level, which is a black blot rather than "no data".
                      "raw_frames": [min(max(1, step), len(raw) - i) for i in cuts]})
        blobs.extend(frames)
    meta["streams"] = table
    meta["version"] = VERSION
    meta["codec"] = "zstd"
    meta["level"] = int(level)
    meta["chunk"] = CHUNK
    head = json.dumps(meta, sort_keys=True).encode("utf-8")
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<II", VERSION, len(head)))
        f.write(head)
        for b in blobs:
            f.write(b)
    size = os.path.getsize(path)
    return {"path": path, "bytes": size, "header": len(head),
            "payload": size - 8 - len(head) - len(MAGIC), "streams": table}


def read_container(path: str, tolerant: bool = False) -> tuple:
    """Read a container back: ``(meta, streams)`` with every stream decompressed.

    ``tolerant`` keeps going when a frame fails to decompress -- the damaged chunk is replaced by
    zeros of its original length, and the number of lost bytes is recorded in
    ``meta["damaged_bytes"]``.  That is how a file behaves when a few bytes are lost in transit; the
    alternative is `zstd.ZstdError` and no model at all.
    """
    with open(path, "rb") as f:
        if f.read(4) != MAGIC:
            raise ValueError(f"{path}: not a GS1 file")
        version, head_len = struct.unpack("<II", f.read(8))
        if version != VERSION:
            raise ValueError(f"{path}: version {version} != {VERSION}")
        meta = json.loads(f.read(head_len).decode("utf-8"))
        streams, lost = {}, 0
        import zlib

        for ent in meta["streams"]:
            parts, bad = [], 0
            crcs = ent.get("crc") or [None] * len(ent["frames"])
            raws = ent.get("raw_frames") or [0] * len(ent["frames"])
            lost_ranges = []
            off = 0
            for i, nbytes in enumerate(ent["frames"]):
                buf = f.read(nbytes)
                ok = crcs[i] is None or (zlib.crc32(buf) & 0xFFFFFFFF) == crcs[i]
                try:
                    if not ok:
                        raise ValueError("frame checksum mismatch")
                    parts.append(_decompress(buf))
                except Exception:
                    if not tolerant:
                        raise
                    bad += 1
                    lost_ranges.append([off, off + raws[i]])
                    lost += raws[i]
                    #: The hole must keep its *length*.  Appending nothing and padding at the end
                    #: of the stream shifts every later byte by this frame's size, so a single bad
                    #: frame silently reinterprets the rest of the stream: M33 measured a one-frame
                    #: burst changing all 6.1 M colours (median |d| 0.33) because of exactly this.
                    parts.append(b"\x00" * raws[i])
                off += raws[i]
            raw = b"".join(parts)
            if len(raw) < ent["raw"]:
                #: Only reachable for files written before ``raw_frames`` existed: the frame sizes
                #: are then unknown, so the hole can only be padded at the end of the stream.
                lost += ent["raw"] - len(raw)
                raw = raw + b"\x00" * (ent["raw"] - len(raw))
            streams[ent["name"]] = raw[:ent["raw"]]
            ent["bad_frames"] = bad
            ent["frame_count"] = len(ent["frames"])
            ent["lost_ranges"] = lost_ranges
        meta["damaged_bytes"] = lost
    _split_rejoin(meta, streams)
    return meta, streams


def _split_rejoin(meta: dict, streams: dict) -> None:
    """Undo an M29 context split in place.

    Each bucket was packed and compressed on its own; the primitive order is rebuilt from the same
    context rule the encoder used, so the rejoined codes are bit-identical to the unsplit stream.  The
    loop runs in plan order, because the ``scale`` split reads the already-rejoined scale stream.
    """
    plan = meta.get("split_plan") or {}
    if not plan:
        return
    import m29_split
    import qfp_rd as _Q
    spec = _Q.parse_spec(str(meta["spec"]))
    n = int(meta["n"])
    #: ``pos`` first: a ``scale`` split is bucketed by the scale codes, which may themselves be
    #: a split stream.  JSON sorts the plan keys, so the stored order cannot be relied on.
    order = sorted(plan.items(), key=lambda kv: (kv[1].get("kind") != "pos", kv[0]))
    for name, info in order:
        keys = sorted((k for k in streams if k.startswith(name + "#")),
                      key=lambda s: int(s.split("#")[1]))
        if not keys:
            continue
        bits, dims = int(info["bits"]), int(info["dims"])
        k = len(keys)
        b = m29_split.buckets_for(info["kind"], n, k, streams, spec)
        codes = np.empty((n, dims), dtype=np.uint16)
        for j, key in enumerate(keys):
            sel = b == j
            cnt = int(sel.sum())
            arr = unpack_bits(streams[key], bits, cnt * dims, dtype=np.uint16).reshape(cnt, dims)
            codes[sel] = arr
            del streams[key]
        #: the encoder pads a stream to whole blocks (the position stream pads to a 256-primitive
        #: cluster), so the rejoined array is extended with the last row to the original byte length
        want = int(info.get("raw") or 0)
        if want:
            n_codes = (want * 8) // bits
            if n_codes > codes.size:
                pad = codes.reshape(-1).shape[0]
                extra = n_codes - pad
                codes = np.concatenate([codes, np.repeat(codes[-1:], extra, axis=0)], axis=0)
        streams[name] = M.pack_bits(codes.reshape(-1), bits)


def _decompress(buf: bytes) -> bytes:
    try:
        import zstandard as zstd
        return zstd.ZstdDecompressor().decompress(buf)
    except ImportError:
        import lzma
        return lzma.decompress(buf)


# ---------------------------------------------------------------------------
# damage: what a lost byte costs
# ---------------------------------------------------------------------------


def stream_span(path: str, name: str) -> tuple:
    """``(start, end)`` payload offsets of one stream, so damage can be aimed at it."""
    with open(path, "rb") as f:
        if f.read(4) != MAGIC:
            raise ValueError(f"{path}: not a GS1 file")
        _, head_len = struct.unpack("<II", f.read(8))
        meta = json.loads(f.read(head_len).decode("utf-8"))
    off = 4 + 8 + head_len
    for ent in meta["streams"]:
        if ent["name"] == name:
            return off, off + ent["comp"]
        off += ent["comp"]
    raise KeyError(name)


def damage_file(src: str, dst: str, frac: float, seed: int = 0, stream: str = None,
                burst: bool = False) -> dict:
    """Flip bits in ``frac`` of the payload (or of one named stream) and write ``dst``.

    ``burst=True`` damages one contiguous run instead of scattering the damage: that is the case a
    format has to survive (a lost packet, a bad sector), and the case scattering cannot emulate --
    one bit in every frame kills every frame, which measures the frame count and not the frame size.
    """
    buf = bytearray(open(src, "rb").read())
    if stream:
        lo, hi = stream_span(src, stream)
    else:
        #: Damage the payload, not the header: a flipped byte in the JSON table makes the file
        #: unreadable rather than degraded, which measures the wrong thing.
        import struct as _struct

        with open(src, "rb") as f:
            f.read(4)
            _, head_len = _struct.unpack("<II", f.read(8))
        lo, hi = 4 + 8 + head_len, len(buf)
    span = hi - lo
    nflip = max(1, int(round(frac * span)))
    rng = np.random.default_rng(seed)
    nflip = min(nflip, span)
    if burst:
        start = int(rng.integers(lo, max(lo + 1, hi - nflip + 1)))
        pos = np.arange(start, start + nflip)
    else:
        pos = rng.choice(np.arange(lo, hi), size=nflip, replace=False)
    bit = rng.integers(0, 8, size=pos.size)
    for p, b in zip(pos, bit):
        buf[int(p)] ^= (1 << int(b))
    with open(dst, "wb") as f:
        f.write(bytes(buf))
    return {"src": src, "dst": dst, "stream": stream, "flipped": int(pos.size),
            "span": int(span), "frac": frac}


def truncate_file(src: str, dst: str, frac: float) -> dict:
    """Write the first ``frac`` of the payload (header intact) -- a delivery prefix.

    Nothing is rewritten: a rate-scalable file is designed so that every byte after the header is
    optional, and a reader that gets fewer bytes than the table promises fills the rest with zeros
    (``read_container(tolerant=True)``).  That is what a progressive download, an interrupted copy
    or a size-capped CDN edge actually hands a client.
    """
    with open(src, "rb") as f:
        head = f.read(4)
        if head != MAGIC:
            raise ValueError(f"{src}: not a GS1 file")
        version, head_len = struct.unpack("<II", f.read(8))
        hdr = head + struct.pack("<II", version, head_len) + f.read(head_len)
        rest = f.read()
    keep = max(0, min(len(rest), int(round(frac * len(rest)))))
    with open(dst, "wb") as f:
        f.write(hdr)
        f.write(rest[:keep])
    return {"src": src, "dst": dst, "frac": frac, "bytes": os.path.getsize(dst),
            "payload": keep, "payload_total": len(rest)}


def layer_table(path: str) -> list:
    """Streams in file order with the payload offset at which each one *starts*.

    Used to pick truncation points that fall on layer boundaries; truncating at a random byte is
    the interesting case for a client, but the layer boundary is where the quality steps are.
    """
    meta, _ = read_container_sizes(path)
    off, rows = 0, []
    for ent in meta["streams"]:
        rows.append({"name": ent["name"], "start": off, "comp": ent["comp"],
                      "raw": ent["raw"]})
        off += ent["comp"]
    return rows


def read_container_sizes(path: str) -> tuple:
    """``(meta, total_payload)`` without decompressing anything."""
    with open(path, "rb") as f:
        if f.read(4) != MAGIC:
            raise ValueError(f"{path}: not a GS1 file")
        _, head_len = struct.unpack("<II", f.read(8))
        meta = json.loads(f.read(head_len).decode("utf-8"))
    return meta, sum(e["comp"] for e in meta["streams"])


def layer_fracs(path: str) -> dict:
    """Payload fraction at which each quality step becomes available.

    The steps are not arbitrary: geometry plus the DC term is a degree-0 model (every primitive
    present, view-independent colour), and each SH plane adds one bit of directional colour.  A
    client that stops at ``p2`` has a file that is ``f["p2"]`` of the payload and a model that is
    one bit better than the DC-only one -- that is the ladder the format sells.
    """
    rows = layer_table(path)
    total = sum(r["comp"] for r in rows)
    out, seen = {}, 0
    for r in rows:
        seen += r["comp"]
        if r["name"] in ("sh_dc",) + SH_PLANES:
            out[r["name"]] = seen / max(1, total)
    out["full"] = 1.0
    return out


def progressive_report(path: str, fracs=(0.33, 0.67, 1.0), save_ply: bool = False) -> list:
    """Decode a prefix of ``path`` at each fraction: what a client at that budget would see."""
    import tempfile
    import time

    meta, total = read_container_sizes(path)
    name = meta.get("spec", "?")
    rows = []
    for frac in fracs:
        with tempfile.TemporaryDirectory() as td:
            cut = os.path.join(td, "cut.gs1")
            truncate_file(path, cut, frac)
            t0 = time.time()
            m2, s2 = read_container(cut, tolerant=True)
            out = decode(m2, s2)
            dt = time.time() - t0
            rows.append({"spec": name, "frac": float(frac),
                         "bytes": os.path.getsize(cut),
                         "payload_frac": (os.path.getsize(cut) - _header_len(path)) / max(1, total),
                         "damaged_bytes": m2.get("damaged_bytes", 0),
                         "planes": [k for k in SH_PLANES if s2.get(k)],
                         "decode_s": dt, "n": int(out["means"].shape[0]),
                         "sh_rest_abs_mean": float(np.abs(out["sh_rest"]).mean())
                         if out["sh_rest"].size else 0.0})
            if save_ply:
                to_ply(m2, s2, os.path.join(td, "x.ply"))
    return rows


def _header_len(path: str) -> int:
    with open(path, "rb") as f:
        f.read(4)
        _, head_len = struct.unpack("<II", f.read(8))
    return 4 + 8 + head_len


def diff_decoded(clean: dict, damaged: dict, tol: float = 0.0) -> dict:
    """How much of the model changed, in primitives rather than in bytes."""
    out = {}
    n = clean["means"].shape[0]
    for key in ("means", "sh_dc", "sh_rest", "scales", "opacities"):
        a, b = np.asarray(clean[key], dtype=np.float64), np.asarray(damaged[key], dtype=np.float64)
        if a.shape != b.shape:
            out[key] = {"shape_mismatch": True}
            continue
        d = np.abs(a - b)
        bad = d.reshape(n, -1).max(axis=1) > tol
        out[key] = {"prims_changed_frac": float(bad.mean()),
                    "max_abs": float(d.max()) if d.size else 0.0,
                    "mean_abs": float(d.mean()) if d.size else 0.0}
    return out


# ---------------------------------------------------------------------------
# the decoder
# ---------------------------------------------------------------------------


def decode(meta: dict, streams: dict) -> dict:
    """Reconstruct the tensors a renderer needs, from streams alone.

    Returns ``means`` (N,3), ``scales`` (N,3, linear), ``quats`` (N,4), ``opacities`` (N, linear),
    ``sh_dc`` (N,3) and ``sh_rest`` (N, K, 3).  Everything is derived from the streams and the
    meta block; nothing is read back from the encoder's memory.
    """
    import qfp_rd as Q

    if meta.get("anchor_mode"):
        #: M27/M28 -- the file carries voxels, not primitives.  One decoder for the two
        #: representations is not possible (the streams are different objects), so the anchor decoder
        #: stands alone and returns the same dict; everything downstream -- to_ply, the renderer, the
        #: container reader -- is unchanged.  ``predicted`` selects M28, where a small network turns
        #: the anchor record plus the offset into the primitive's own attributes.
        if meta.get("predicted"):
            import m28_pred
            return m28_pred.decode(meta, streams)
        import m27_anchor
        return m27_anchor.decode(meta, streams)
    if meta.get("geo_delta"):
        #: M23 -- the file stored these streams as deltas; put the packed form back so there is
        #: still exactly one decoder for what follows.
        import m23_pred
        streams = m23_pred.restore(meta, streams)
    spec = Q.parse_spec(meta["spec"])
    n = int(meta["n"])
    deg_out = int(meta["deg_out"])

    # --- positions: cluster-relative offsets, or a flat grid -----------------
    if "cluster_hdr" in streams:
        hdr = np.frombuffer(streams["cluster_hdr"], dtype=np.float32).reshape(-1, 6)
        nblk = hdr.shape[0]
        o, step = hdr[:, :3], hdr[:, 3:]
        cbits = int(getattr(spec, "means_cluster_bits", 8))
        if "cluster_bits" in streams:
            #: M30 -- every cluster carries its own width, chosen by the encoder from that cluster's
            #: extent.  The stream is a concatenation of per-cluster packs, so the decoder walks it;
            #: ``step`` is still stored per cluster, so nothing else about the path changes.
            bits_c = np.frombuffer(streams["cluster_bits"], dtype=np.uint8).astype(np.int64)
            block = int(M.CLUSTER_SIZE)
            buf = streams["cluster_off"]
            off = 0
            u = np.empty((nblk, block, 3), dtype=np.uint16)
            for i in range(nblk):
                nb = block * 3 * int(bits_c[i])
                nbytes = (nb + 7) // 8
                u[i] = unpack_bits(buf[off:off + nbytes], int(bits_c[i]), block * 3,
                                   dtype=np.uint16).reshape(block, 3)
                off += nbytes
            u = u.reshape(nblk * block, 3)[:n]
        else:
            u = unpack_bits(streams["cluster_off"], cbits, nblk * M.CLUSTER_SIZE * 3, dtype=np.uint16)
            u = u.reshape(nblk * M.CLUSTER_SIZE, 3)[:n]
        blk = np.repeat(np.arange(nblk), M.CLUSTER_SIZE)[:n]
        means = o[blk] + u.astype(np.float32) * step[blk]
    else:
        bits = int(spec.geo.get("means", M.FP32_BITS))
        if bits >= M.FP32_BITS:
            means = np.frombuffer(streams["geo_means"], dtype=np.float32).reshape(-1, 3)
        else:
            hdr = decode_geo_header(streams["geo_hdr"], spec)
            mn, step = hdr["means"]
            codes = unpack_bits(streams["geo_means"], bits, n * 3).reshape(n, 3)
            means = mn + codes * step

    out = {"means": np.asarray(means, dtype=np.float32)}

    # --- scales / quats / opacities -----------------------------------------
    ghdr = decode_geo_header(streams["geo_hdr"], spec) if "geo_hdr" in streams else {}
    if "geo_vq_idx" in streams:
        #: M38 -- the three attribute groups come from one joint codebook index instead of four
        #: independent scalar codes.  ``decode_attrs`` returns them in *coded* space (log scales, unit
        #: quaternion, logit opacity) so the exp/sigmoid below stays the one nonlinearity in the decoder.
        import m38_vq
        out.update(m38_vq.decode_attrs(streams, meta))
    else:
        for attr in ("scales", "quats", "opacities"):
            bits = int(spec.geo.get(attr, M.FP32_BITS))
            d = DIMS[attr]
            if attr == "quats" and "geo_quat_which" in streams:
                import geom_pack as GP
                bq = int(getattr(spec, "quat_st3", 8))
                which = unpack_bits(streams["geo_quat_which"], 2, n, dtype=np.uint8)
                dt = np.uint8 if bq <= 8 else np.uint16
                abc = unpack_bits(streams["geo_quat_abc"], bq, n * 3, dtype=dt).reshape(n, 3)
                #: ``st3_decode`` works in float64; the answer is float32 like every other attribute, and
                #: for a 6 M primitive asset the difference is 98 MB of resident memory (M25)
                out["quats"] = np.asarray(GP.st3_decode(which, abc, bq), dtype=np.float32)
                continue
            if bits >= M.FP32_BITS:
                out[attr] = np.frombuffer(streams[f"geo_{attr}"], dtype=np.float32).reshape(n, d)
            else:
                mn, step = ghdr[attr]
                dt = np.uint8 if bits <= 8 else np.uint16
                codes = unpack_bits(streams[f"geo_{attr}"], bits, n * d, dtype=dt).reshape(n, d)
                out[attr] = mn.astype(np.float32) + codes.astype(np.float32) * step.astype(np.float32)

    out["scales"] = np.exp(np.asarray(out["scales"], dtype=np.float32))
    op = np.asarray(out["opacities"], dtype=np.float32).reshape(n)
    out["opacities"] = (1.0 / (1.0 + np.exp(-op))).astype(np.float32)

    # --- colour --------------------------------------------------------------
    cols = 3 + 3 * deg_out * (deg_out + 2) if deg_out >= 0 else 3
    if "sh_index" in streams:
        if "sh_vq_bits" not in meta:
            #: Multi-stage dictionaries (``msc``) write ``sh_index`` as well but with a different
            #: meaning (a dictionary id for the subset ``modes`` selects, plus scalar residuals).
            #: Decoding them is out of scope for M19; saying so is better than a KeyError.
            raise NotImplementedError(
                f"{meta['spec']}: the multi-stage (msc) colour coder is not implemented in this "
                f"decoder; the shelf codecs (c8/c10_o8_sh3) and vq are")
        vq_bits = int(meta["sh_vq_bits"])
        codes = unpack_bits(streams["sh_index"], vq_bits, n)
        hdr = np.frombuffer(streams["sh_cb_hdr"], dtype=np.float32)
        cen = np.frombuffer(streams["sh_cb_centroids"], dtype=np.uint8)
        cen = cen.reshape(-1, cols).astype(np.float64)
        flat = cen[codes] * float(hdr[1]) + float(hdr[0])
        out["sh_dc"], out["sh_rest"] = _split_sh(flat, deg_out)
    elif "sh_basis" in streams:
        #: M22: the rest block comes from a basis shared by the whole asset, so the file carries r
        #: numbers per primitive instead of 45.  DC keeps the shelf's own coding.
        import m22_basis as B
        hdr = np.frombuffer(streams["sh_hdr"], dtype=np.float32)
        nlev = int(meta.get("sh_scale_levels", 2))
        lvl = unpack_bits(streams["sh_scale"], 8, n * nlev, dtype=np.uint8).reshape(n, nlev)
        bits = int(spec.sh_bits)
        qmax = (1 << (bits - 1)) - 1
        dc_codes = _sh_codes(streams["sh_dc"], bits, n, 3,
                             str(meta.get("sh_layout", "bits")), dtype=np.float32)
        dc_codes = neutralise(dc_codes, meta, "sh_dc", float(qmax + 1),
                              str(meta.get("sh_layout", "bits")))
        out["sh_dc"] = ((dc_codes - np.float32(qmax + 1))
                        * (lvl[:, 0:1].astype(np.float32) / np.float32(255.0))
                        * np.float32(hdr[0])).astype(np.float32)
        rest = B.solve_basis(meta, streams, n, int(meta["sh_rest_cols"]))
        out["sh_rest"] = rest.reshape(n, -1, 3)
    elif "sh_dc" in streams:
        hdr = np.frombuffer(streams["sh_hdr"], dtype=np.float32)
        lvl = unpack_bits(streams["sh_scale"], 8, n * 2).reshape(n, 2).astype(np.float64)
        blocks = {}
        for i, key in enumerate(("sh_dc", "sh_rest")):
            if key not in streams:
                continue
            bits = int(spec.sh_bits)
            #: ``codes_published_sh_parts`` uses the *signed* range: ``qmax = 2**(bits-1) - 1`` and
            #: stores ``code + qmax + 1``.  Reading ``qmax`` as ``2**bits - 1`` shifts every
            #: coefficient by half the range -- which is exactly the kind of error a tensor
            #: comparison finds and a rendered image hides behind "looks a bit washed out".
            qmax = (1 << (bits - 1)) - 1
            #: ``m4_bytes`` stores ``code + (qmax + 1)`` after clipping to ``[-qmax-1, qmax]``, so
            #: the decoder subtracts ``qmax + 1``.  Using ``qmax // 2 + 1`` here shifted every
            #: coefficient by two quantisation steps -- the kind of bug an image comparison hides
            #: (it reads as a slight colour cast) and a tensor comparison finds in one line.
            ncols = 3 if key == "sh_dc" else cols - 3
            codes = _sh_codes(streams[key], bits, n, ncols,
                              str(meta.get("sh_layout", "bits"))).astype(np.float64)
            codes = neutralise(codes, meta, key, float(qmax + 1),
                               str(meta.get("sh_layout", "bits")))
            scale = (lvl[:, i:i + 1] / 255.0) * float(hdr[i])
            blocks[key] = (codes - float(qmax + 1)) * scale
        out["sh_dc"] = blocks["sh_dc"]
        if "sh_rest" in blocks:
            out["sh_rest"] = blocks["sh_rest"].reshape(n, -1, 3)
        elif any(k in streams for k in SH_PLANES):
            #: Rate-scalable file, possibly truncated: a plane that is absent (or was zero-filled
            #: because its frame was lost) contributes zero bits, which is the coarse end of the
            #: ladder -- every primitive keeps its position and gets a coarser colour.
            out["sh_rest"] = _plane_codes(streams, n, cols - 3, lvl[:, 1:2], float(hdr[1]),
                                          qmax, meta).reshape(n, -1, 3)
        else:
            out["sh_rest"] = np.zeros((n, 0, 3))
    else:
        raise ValueError("no SH stream this decoder understands")
    return out


def _plane_codes(streams: dict, n: int, ncols: int, lvl, ref: float, qmax: int,
                 meta: dict = None) -> np.ndarray:
    """``(n, ncols)`` signed coefficient values from whichever planes survived.

    Truncation throws away the *low* bits first, so the surviving code sits at the bottom of the
    interval it represents and every coefficient would read low by half a step.  The decoder
    therefore adds the midpoint of the unknown bits back (reconstruction levels, the trick scalable
    coders use): with no plane at all the estimate is the middle of the code range, which is the
    signed zero -- a degree-0 model -- instead of the most negative level it could be.
    """
    present = []
    ent = {e["name"]: e for e in (meta or {}).get("streams", [])}
    plane_bit = {name: len(SH_PLANES) - 1 - i for i, name in enumerate(SH_PLANES)}
    codes = np.zeros((n, ncols), dtype=np.float64)
    for name, bit in plane_bit.items():
        buf = streams.get(name)
        e = ent.get(name)
        if e and e.get("frame_count") and e.get("bad_frames", 0) >= e["frame_count"]:
            continue                      # every frame of this plane was lost: no bits at all
        if not buf:
            continue
        present.append(bit)
        b = np.frombuffer(buf[:n * ncols], dtype=np.uint8)
        if b.size < n * ncols:
            b = np.concatenate([b, np.zeros(n * ncols - b.size, np.uint8)])
        codes += b.reshape(n, ncols).astype(np.float64) * (1 << bit)
    k = len(present)
    lut = streams.get("sh_lut")
    #: Measured on synthetic ladders (``m21_lut_probe.py``): the conditional mean beats both the
    #: midpoint rule and "assume zero" once a top bit is known (1.5x and 1.5x lower L1 at k=1,
    #: 1.16x and 1.16x at k=2), while at k=0 nothing beats zero -- so the DC-only step is the
    #: degree-0 model and the LUT is used only when there is a bit to condition on.
    if lut and 0 < k < 3:
        t = np.frombuffer(lut, dtype=np.float32)
        nb = 1 << k
        off = (1 if k >= 1 else 0) + (2 if k >= 2 else 0)
        tab = t[off * ncols:(off + nb) * ncols].reshape(nb, ncols)
        h = (codes.astype(np.int64) >> (3 - k))
        codes = tab[h, np.arange(ncols)[None, :]]
    elif k == 0:
        #: No bit at all is not "uniform over the level grid": SH rest coefficients concentrate
        #: near zero, so the estimate is the signed zero (code ``qmax + 1``) and the prefix renders
        #: as a degree-0 model instead of a model tinted by half a quantisation step.
        codes = codes + float(qmax + 1)
    else:
        #: midpoint of the 3-k missing low bits, added before the signed bias is removed
        codes = codes + float((1 << (3 - k)) - 1) / 2.0
    scale = (lvl / 255.0) * ref
    return (codes - float(qmax + 1)) * scale


def neutralise(codes: np.ndarray, meta: dict, name: str, value: float, layout: str = "bytes"):
    """Fill the codes of lost frames with ``value`` instead of the zero bytes they were given.

    A zero-filled *code* stream does not decode to "no colour": the codes are signed with an offset
    (``qmax + 1`` is zero), so a run of zeros is the most negative level of every coefficient --
    measured as a 9.9 dB render on a file whose colour block had been cut off, against 22.8 dB when
    the missing region decodes to the neutral code.  Positions are left alone: a lost position has
    no neutral value, and pretending otherwise would move geometry.
    """
    if layout != "bytes" or name not in ("sh_dc", "sh_rest") + SH_PLANES:
        return codes
    ent = {e["name"]: e for e in (meta or {}).get("streams", [])}.get(name)
    if not ent:
        return codes
    ranges = ent.get("lost_ranges") or []
    if not ranges:
        return codes
    flat = codes.reshape(-1)
    n = flat.size
    for a, b in ranges:
        if a >= n:
            continue
        flat[a:min(b, n)] = value
    return flat.reshape(codes.shape)


def _split_sh(flat: np.ndarray, deg_out: int):
    dc = flat[:, :3]
    rest = flat[:, 3:]
    if rest.size == 0:
        return dc, np.zeros((flat.shape[0], 0, 3))
    return dc, rest.reshape(flat.shape[0], -1, 3)


# ---------------------------------------------------------------------------
# encode side: wrap m4_bytes so the same numbers are produced, plus a file
# ---------------------------------------------------------------------------


def encode_model(splats, spec_name: str, level: int = 12, path: str = None,
                 sh_layout: str = "bytes", progressive: bool = False, jobs: int = 1) -> dict:
    """Encode one model into a container; returns sizes, the streams and the file name.

    ``sh_layout`` chooses how the SH codes are laid out before zstd; ``bytes`` is the default
    because it is 8 % smaller and a third faster to decode on bicycle and stump (M20), while
    ``bits`` (packed
    bit-planes, ``bytes`` = one byte per code primitive-major, ``bytes_coef`` =
    coefficient-major); the decoder reads the choice back out of the header.
    """
    import qfp_rd as Q

    spec = Q.parse_spec(spec_name)
    geo, sh = M._attribute_arrays(splats)
    deg = int(splats.sh_degree)
    n = int(geo["means"].shape[0])
    order = M.morton_order(geo["means"])
    streams, model_bpp = M._encode(spec, geo, sh, deg, None, order, sh_layout=sh_layout)
    if progressive:
        if sh_layout != "bytes":
            raise ValueError("rate-scalable files need sh_layout='bytes' (one byte per code)")
        if "sh_rest" not in streams:
            raise ValueError(f"{spec_name}: progressive needs the 3-bit SH ladder")
        deg_out = int(spec.out_degree(deg))
        ncols = 3 * deg_out * (deg_out + 2)
        if len(streams["sh_rest"]) != n * ncols:
            raise ValueError(f"{spec_name}: sh_rest has {len(streams['sh_rest'])} bytes, "
                             f"expected {n} x {ncols}")
        streams = split_sh_planes(streams, n, ncols)
    # The header the decoder needs, and which the byte model never charged for.
    streams["geo_hdr"] = geo_header(geo, spec)
    meta = {"spec": spec_name, "n": n, "sh_degree": deg, "sh_layout": sh_layout,
            "deg_out": int(spec.out_degree(deg)), "model_bytes_per_prim": float(model_bpp),
            "min_frame": int(MIN_FRAME)}
    if progressive:
        meta["sh_progressive"] = True
    if getattr(spec, "sh_vq_bits", None):
        meta["sh_vq_bits"] = int(spec.sh_vq_bits)
    info = None
    if path:
        info = write_container(path, streams, meta, level, jobs=jobs)
    return {"streams": streams, "meta": meta, "info": info, "model_bytes_per_prim": float(model_bpp)}


def to_ply(meta: dict, streams: dict, path: str) -> dict:
    """Decode a container and write the INRIA PLY the renderers already read."""
    from calib.plyio import save_inria_ply

    out = decode(meta, streams)
    n = out["means"].shape[0]
    sh_rest = out["sh_rest"] if out["sh_rest"].shape[1] else np.zeros((n, 0, 3))
    save_inria_ply(path, out["means"], out["scales"], out["quats"], out["opacities"],
                   out["sh_dc"], sh_rest)
    return {"path": path, "n": int(n), "bytes": os.path.getsize(path)}


def damage_report(path: str, fracs=(0.001, 0.005, 0.01, 0.02), seed: int = 0,
                  stream: str = "sh_rest") -> list:
    """Damage a fixed fraction of one stream, decode tolerantly, and measure what moved.

    Aimed at a named stream: damaging the payload at random mostly hits the bulk colour streams
    anyway, but naming one makes the "how local is a lost frame" question answerable, and keeps a
    tiny header stream (64 B) from turning the table into "every run loses everything".
    """
    meta, streams = read_container(path)
    clean = decode(meta, streams)
    names = [e["name"] for e in meta["streams"]]
    if stream not in names:
        #: Rate-scalable files have no single colour block: aim at the plane that costs the most,
        #: which is the same question (what does a lost frame of the bulk colour cost?).
        cand = [e for e in meta["streams"] if e["name"].startswith("sh_rest")]
        if not cand:
            raise KeyError(f"{path}: no colour stream to damage")
        stream = max(cand, key=lambda e: e["comp"])["name"]
    ent = [e for e in meta["streams"] if e["name"] == stream][0]
    rows = []
    for frac in fracs:
        dst = path + f".dmg{int(frac * 10000)}"
        damage_file(path, dst, frac=frac, seed=seed, stream=stream, burst=True)
        m2, s2 = read_container(dst, tolerant=True)
        d = diff_decoded(clean, decode(m2, s2))
        rows.append({"frac": frac,
                     "stream": stream,
                     "stream_bytes": ent["comp"],
                     "frames": len(ent["frames"]),
                     "lost_bytes": m2["damaged_bytes"],
                     "lost_frac_of_stream": m2["damaged_bytes"] / max(1, ent["raw"]),
                     "means_changed": d["means"]["prims_changed_frac"],
                     "sh_changed": max(d["sh_dc"]["prims_changed_frac"], d["sh_rest"]["prims_changed_frac"]),
                     "sh_max_abs": max(d["sh_dc"]["max_abs"], d["sh_rest"]["max_abs"])})
        os.remove(dst)
    return rows


def verify_roundtrip(splats, spec_name: str, level: int = 12,
                     sh_layout: str = "bits") -> dict:
    """Encode, decode, and compare against the source arrays *in the encoder's own order*.

    This is the check that separates a codec bug from a PLY-writer bug: both sides are the arrays
    the encoder saw, so a permutation cannot hide a mismatch.  Attributes are compared in the
    domains the model codes (log scale, logit opacity), which is where a quantiser error shows up
    as a constant.
    """
    import qfp_rd as Q

    spec = Q.parse_spec(spec_name)
    geo, sh = M._attribute_arrays(splats)
    deg = int(splats.sh_degree)
    order = M.morton_order(geo["means"])
    streams, _ = M._encode(spec, geo, sh, deg, None, order, sh_layout=sh_layout)
    streams["geo_hdr"] = geo_header(geo, spec)
    meta = {"spec": spec_name, "n": int(geo["means"].shape[0]), "sh_degree": deg,
            "sh_layout": sh_layout,
            "deg_out": int(spec.out_degree(deg)), "model_bytes_per_prim": 0.0}
    if getattr(spec, "sh_vq_bits", None):
        meta["sh_vq_bits"] = int(spec.sh_vq_bits)
    out = decode(meta, streams)
    ref = {k: np.asarray(v, dtype=np.float64)[order] for k, v in geo.items()}
    ref_sh_dc = np.asarray(sh["dc"], dtype=np.float64)[order]
    cols = [np.asarray(sh["dc"], dtype=np.float64), np.asarray(sh["rest"], dtype=np.float64)]
    flat_src = np.concatenate([cols[0].reshape(cols[0].shape[0], -1),
                               cols[1].reshape(cols[1].shape[0], -1)], axis=1)[order]
    res = {}
    n = ref["means"].shape[0]
    #: Compare in the domain the model codes: ``decode`` returns linear scales and probabilities
    #: because a renderer wants them, while ``geo`` holds log-scale and logit.
    coded = {"scales": np.log(np.maximum(out["scales"], 1e-30)),
             "opacities": np.log(np.clip(out["opacities"], 1e-6, 1 - 1e-6)
                                 / (1.0 - np.clip(out["opacities"], 1e-6, 1 - 1e-6)))}
    for key in ("means", "scales", "quats", "opacities"):
        a = np.asarray(ref[key], dtype=np.float64).reshape(n, -1)
        src = out[key] if key in ("means", "quats") else coded[key]
        b = np.asarray(src, dtype=np.float64).reshape(n, -1)
        d = np.abs(a - b)
        res[key] = {"max": float(d.max()), "mean": float(d.mean())}
    dc = out["sh_dc"]
    rest = out["sh_rest"].reshape(dc.shape[0], -1) if out["sh_rest"].size else np.zeros((dc.shape[0], 0))
    flat = np.concatenate([dc, rest], axis=1)
    d = np.abs(flat_src - flat)
    res["sh"] = {"max": float(d.max()), "mean": float(d.mean())}
    return res


def selftest() -> None:
    import torch
    import qfp_rd as Q

    class S:  # minimal stand-in for the splat container
        pass

    rng = np.random.default_rng(0)
    n, deg = 900, 3
    s = S()
    s.sh_degree = deg
    s.means = torch.tensor(rng.normal(0, 1.0, (n, 3)), dtype=torch.float32)
    s.scales = torch.tensor(np.exp(rng.normal(-2.0, 0.4, (n, 3))), dtype=torch.float32)
    q = rng.normal(size=(n, 4))
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    s.quats = torch.tensor(q, dtype=torch.float32)
    s.opacities = torch.tensor(rng.uniform(0.02, 0.98, (n,)), dtype=torch.float32)
    s.sh0 = torch.tensor(rng.normal(0, 0.5, (n, 3)), dtype=torch.float32)
    s.shN = torch.tensor(rng.normal(0, 0.1, (n, 15, 3)), dtype=torch.float32)

    import tempfile
    for spec_name in ("c10_o8_sh3", "c8_o8_sh3", "vq12_c8_o8"):
        with tempfile.TemporaryDirectory() as td:
            rec = encode_model(s, spec_name, level=12, path=os.path.join(td, "m.gs1"))
            meta, streams = read_container(os.path.join(td, "m.gs1"))
            out = decode(meta, streams)
            # 1. the file round-trips byte for byte
            assert set(streams) == set(rec["streams"]), (set(streams) ^ set(rec["streams"]))
            for k, v in rec["streams"].items():
                assert v == streams[k], f"{spec_name}: stream {k} changed in the container"
            # 2. decoded shapes
            assert out["means"].shape == (n, 3), out["means"].shape
            assert out["scales"].shape == (n, 3)
            assert out["opacities"].shape == (n,)
            assert out["sh_dc"].shape == (n, 3)
            # 3. permutation-invariant agreement with the source model
            src = np.sort(np.asarray(s.means.numpy(), dtype=np.float64), axis=0)
            got = np.sort(out["means"], axis=0)
            span = float(s.means.numpy().max() - s.means.numpy().min())
            step = span / ((1 << 10) - 1) if "c10" in spec_name else span / ((1 << 8) - 1)
            assert np.abs(src - got).max() <= 2 * step + 1e-5, \
                f"{spec_name}: positions off by {np.abs(src - got).max():.3g} (step {step:.3g})"
            # 4. opacities within their grid
            assert np.abs(np.sort(out["opacities"]) - np.sort(s.opacities.numpy())).max() < 0.05
            # 5. the side information is small, present, and charged for
            assert len(rec["streams"]["geo_hdr"]) == 64, len(rec["streams"]["geo_hdr"])
            if "sh_scale" in rec["streams"]:            # the 3-bit ladder needs its references
                assert len(rec["streams"]["sh_hdr"]) == 8
            else:                                       # VQ carries min/step in sh_cb_hdr
                assert "sh_hdr" not in rec["streams"]
            # 6. damage is detected, stays local, and does not touch the other streams
            dmg = os.path.join(td, "dmg.gs1")
            target = "sh_rest" if "sh_rest" in rec["streams"] else "sh_index"
            damage_file(os.path.join(td, "m.gs1"), dmg, frac=0.01, stream=target)
            m2, s2 = read_container(dmg, tolerant=True)
            assert m2["damaged_bytes"] > 0, "a flipped bit should be detected by the frame CRC"
            out2 = decode(m2, s2)
            d = diff_decoded(out, out2)
            assert d["means"]["prims_changed_frac"] == 0.0, \
                "damage in the colour stream must not move a single position"

    # 7. rate-scalable files: same information, separable planes, and a prefix still decodes
    with tempfile.TemporaryDirectory() as td:
        full = os.path.join(td, "full.gs1")
        prog = os.path.join(td, "prog.gs1")
        a1 = encode_model(s, "c10_o8_sh3", level=12, path=full)
        a2 = encode_model(s, "c10_o8_sh3", level=12, path=prog, progressive=True)
        assert "sh_rest" not in a2["streams"] and all(k in a2["streams"] for k in SH_PLANES)
        # the same three bits per coefficient, in three separable planes
        codes = np.frombuffer(a1["streams"]["sh_rest"], dtype=np.uint8).astype(np.int64)
        rebuilt = np.zeros_like(codes)
        for i, name in enumerate(reversed(SH_PLANES)):
            rebuilt |= np.frombuffer(a2["streams"][name], dtype=np.uint8).astype(np.int64) << i
        assert np.array_equal(codes, rebuilt), "plane split lost a bit"
        m2, s2 = read_container(prog)
        out_p = decode(m2, s2)
        out_f = decode(*read_container(full))
        for key in ("means", "scales", "quats", "opacities", "sh_dc", "sh_rest"):
            assert np.allclose(out_p[key], out_f[key], atol=1e-6), f"progressive changed {key}"
        # a prefix that stops after one plane still decodes every primitive, just coarser
        cut = os.path.join(td, "cut.gs1")
        truncate_file(prog, cut, 0.5)
        m3, s3 = read_container(cut, tolerant=True)
        assert m3["damaged_bytes"] > 0
        out_c = decode(m3, s3)
        assert out_c["means"].shape == out_f["means"].shape
        assert np.array_equal(out_c["means"], out_f["means"]), "truncation moved positions"
        assert np.abs(out_c["sh_rest"]).mean() != np.abs(out_f["sh_rest"]).mean(), \
            "a truncated prefix must actually be coarser"
        # planes are written coarse-to-fine, so the first plane seen is p2
        names = [r["name"] for r in layer_table(prog)]
        assert names.index("sh_rest_p2") < names.index("sh_rest_p1") < names.index("sh_rest_p0")
    print("m19_codec selftest: ALL PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--archive")
    ap.add_argument("--scenes", default="bicycle")
    ap.add_argument("--specs", default="c10_o8_sh3,vq12_c8_o8")
    ap.add_argument("--out")
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--deck", action="store_true",
                    help="decode every file back and print decode time / peak RSS")
    ap.add_argument("--to-ply", help="decode an existing .gs1 to this INRIA PLY")
    ap.add_argument("--tolerant", action="store_true",
                    help="with --to-ply: decode a truncated or damaged file anyway")
    ap.add_argument("--damage", help="run the damage table on an existing .gs1")
    ap.add_argument("--verify", action="store_true",
                    help="encode+decode the archive PLY and compare attributes in memory")
    ap.add_argument("--progressive", action="store_true",
                    help="split the SH rest block into rate-scalable bit-planes (M21)")
    ap.add_argument("--ladder", help="report decode quality of prefixes of an existing .gs1")
    ap.add_argument("--fracs", default="0.33,0.67,1.0")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if a.to_ply:
        meta, streams = read_container(a.to_ply, tolerant=a.tolerant)
        info = to_ply(meta, streams, a.out or a.to_ply.replace(".gs1", ".ply"))
        print("PLY", info)
        return 0
    if a.damage:
        for r in damage_report(a.damage):
            print(f"damage {r['frac']*100:5.1f}% of {r['stream']} ({r['frames']} frames)  "
                  f"lost {r['lost_frac_of_stream']*100:6.2f}% of the stream  "
                  f"positions moved {r['means_changed']*100:6.2f}%  "
                  f"colour moved {r['sh_changed']*100:6.2f}%  max|dSH| {r['sh_max_abs']:.3f}",
                  flush=True)
        return 0
    if a.ladder:
        fracs = tuple(float(x) for x in a.fracs.split(",") if x.strip())
        for r in progressive_report(a.ladder, fracs):
            print(f"prefix {r['frac']*100:5.1f}%  {r['bytes']/1e6:8.2f} MB  "
                  f"planes {len(r['planes'])}/3  lost {r['damaged_bytes']/1e6:6.2f} MB  "
                  f"decode {r['decode_s']:5.2f} s  |sh_rest| {r['sh_rest_abs_mean']:.4f}",
                  flush=True)
        return 0
    if not a.archive:
        ap.error("--archive is required (or --selftest / --to-ply / --damage)")
    import resource
    import calib.gsrender as GR

    os.makedirs(a.out or ".", exist_ok=True)
    for scene in [s.strip() for s in a.scenes.split(",") if s.strip()]:
        ply = os.path.join(a.archive, "output", scene, "point_cloud", "iteration_40000",
                           "point_cloud.ply")
        t_load = time.time()
        splats = GR.load_splats(ply, device="cpu")
        print(f"{scene}: loaded in {time.time()-t_load:.1f} s", flush=True)
        for spec in [s.strip() for s in a.specs.split(",") if s.strip()]:
            if a.verify:
                res = verify_roundtrip(splats, spec, level=a.level)
                print(f"{scene} {spec:16s} " + "  ".join(
                    f"{k} max {v['max']:.4g}/mean {v['mean']:.3g}" for k, v in res.items()), flush=True)
                continue
            rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
            t0 = time.time()
            tag = f"{scene}_{spec}" + ("_p" if a.progressive else "")
            rec = encode_model(splats, spec, level=a.level,
                               path=os.path.join(a.out, f"{tag}.gs1"),
                               progressive=a.progressive)
            enc_s = time.time() - t0
            info = rec["info"]
            rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
            print(f"{scene} {spec:16s} file {info['bytes']/1e6:8.2f} MB  header {info['header']} B  "
                  f"encode {enc_s:6.1f} s  peak RSS {rss1:7.0f} MB (+{rss1-rss0:.0f})", flush=True)
            if a.deck:
                t1 = time.time()
                meta, streams = read_container(info["path"])
                out = decode(meta, streams)
                dec_s = time.time() - t1
                bpp = info["bytes"] / max(1, meta["n"])
                print(f"    decode {dec_s:6.2f} s  ({bpp:.2f} B/primitive, "
                      f"{meta['n']:,} primitives)  means {out['means'].shape}", flush=True)
                t2 = time.time()
                to_ply(meta, streams, os.path.join(a.out, f"{tag}.ply"))
                print(f"    decode+PLY write {time.time()-t2:6.2f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
