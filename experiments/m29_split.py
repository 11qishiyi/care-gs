"""M29 -- the streams in the shipped shelf, with a context split and a matching container path.

The probe (`m29_entropy.py`) says whether a decoder-computable context beats plain zstd on an attribute
stream.  This module is the other half: it *wires* the winning split, so the byte count and the render
can be measured on a real container rather than projected.

Mechanism, kept deliberately small:

* a stream is split into ``k`` buckets by a context the decoder already holds -- the primitive's coarse
  spatial band (its 256-primitive block index modulo ``k``) or its own first scale code;
* each bucket is bit-packed and zstd-ed independently;
* the container carries ``<stream>#<k>`` and a 1-byte ``split_hdr`` marker; the decoder concatenates the
  buckets back in primitive order, so the reconstructed codes are bit-identical to the unsplit stream.

That is all: no new quantiser, no changed code, no model.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

import m4_bytes as M
import m19_codec as C
import qfp_rd as Q

SPLITS = {"pos": 8, "scale": 8}


def zlen(buf: bytes, level: int = 12) -> int:
    import zstandard as zstd
    return len(zstd.ZstdCompressor(level=level).compress(buf))


def buckets_for(kind: str, n: int, k: int, streams: dict, spec) -> np.ndarray:
    """The bucket of every primitive, computed from data the decoder holds at that point.

    ``pos`` needs nothing (the block order is the Morton order of the stored positions, so the
    256-primitive block index is ``arange(n) // 256``), and ``scale`` needs only the scale stream,
    which the container decodes before rotation and opacity.
    """
    if kind == "pos":
        blk = np.repeat(np.arange((n + 255) // 256), 256)[:n]
        return (blk % int(k)).astype(np.int64)
    if kind == "scale":
        bits = int(spec.geo.get("scales", 8))
        codes = C.unpack_bits(streams["geo_scales"], bits, n * 3, dtype=np.uint16).reshape(n, 3)
        return np.clip((codes[:, 0].astype(np.int64) * int(k)) >> bits, 0, int(k) - 1)
    raise SystemExit(f"unknown split {kind}")


def _buckets(kind: str, n: int, meta: dict, streams: dict, spec) -> np.ndarray:
    return buckets_for(kind, n, SPLITS[kind], streams, spec)


def split_stream(stream_name: str, bits: int, dims: int, kind: str, n: int, meta: dict,
                 streams: dict, spec, level: int = 12) -> tuple:
    """Return ``(new_streams, plain_bytes, split_bytes)`` for one stream."""
    codes = C.unpack_bits(streams[stream_name], bits, n * dims, dtype=np.uint16).reshape(n, dims)
    buckets = _buckets(kind, n, meta, streams, spec)
    k = int(buckets.max()) + 1
    out, total = {}, 0
    for b in range(k):
        sel = np.ascontiguousarray(codes[buckets == b].reshape(-1))
        buf = M.pack_bits(sel, bits)
        out[f"{stream_name}#{b}"] = buf
        total += zlen(buf, level)
    return out, zlen(streams[stream_name], level), total


def build(gs1: str, out_gs1: str, plan: dict, level: int = 12, log=print) -> dict:
    """Copy a container, replacing the streams named in ``plan`` with context-split versions."""
    meta, streams = C.read_container(gs1)
    spec = Q.parse_spec(str(meta["spec"]))
    n = int(meta["n"])
    new = {k: v for k, v in streams.items()}
    raw_len = {}
    rows = []
    for name, (kind, bits, dims) in plan.items():
        parts, before, after = split_stream(name, bits, dims, kind, n, meta, streams, spec, level)
        del new[name]
        new.update(parts)
        raw_len[name] = len(streams[name])
        rows.append({"stream": name, "split": kind, "k": len(parts),
                     "plain": before, "split": after,
                     "saved": before - after,
                     "saved_pct": round(100.0 * (before - after) / max(1, before), 2)})
        log(f"  {name:<16} {kind:<6} {before/1e6:8.3f} -> {after/1e6:8.3f} MB "
            f"({rows[-1]['saved_pct']:+.1f} %)")
    meta = dict(meta)
    meta["split_plan"] = {k: {"kind": v[0], "bits": int(v[1]), "dims": int(v[2]),
                              "raw": int(raw_len.get(k, 0))}
                          for k, v in plan.items()}
    C.write_container(out_gs1, new, meta, level=level)
    size_before, size_after = os.path.getsize(gs1), os.path.getsize(out_gs1)
    return {"before": size_before, "after": size_after, "rows": rows,
            "saved": size_before - size_after,
            "saved_pct": round(100.0 * (size_before - size_after) / max(1, size_before), 2)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gs1", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--json")
    a = ap.parse_args()

    def log(msg: str) -> None:
        print(msg, flush=True)

    q = Q.parse_spec(str(C.read_container(a.gs1)[0]["spec"]))
    plan = {
        "cluster_off": ("pos", int(q.means_cluster_bits), 3),
        "geo_scales": ("pos", int(q.geo.get("scales", 8)), 3),
    }
    if getattr(q, "quat_st3", None) is not None:
        plan["geo_quat_abc"] = ("scale", int(q.quat_st3), 3)
        plan["geo_quat_which"] = ("pos", 2, 1)
    plan["geo_opacities"] = ("scale", int(q.geo.get("opacities", 8)), 1)

    log(f"splitting {a.gs1}")
    res = build(a.gs1, a.out, plan, level=a.level, log=log)
    log(f"file {res['before']/1e6:.2f} MB -> {res['after']/1e6:.2f} MB "
        f"({res['saved_pct']:+.2f} %)")
    #: the decoder must reproduce the codes exactly; check the whole model, not a stream
    m0, s0 = C.read_container(a.gs1)
    m1, s1 = C.read_container(a.out)
    a0, a1 = C.decode(m0, s0), C.decode(m1, s1)
    same = all(np.array_equal(a0[k], a1[k]) for k in a0)
    log(f"decoded model identical: {same}")
    row = {"in": a.gs1, "out": a.out, "before": res["before"], "after": res["after"],
           "saved_pct": res["saved_pct"], "rows": res["rows"], "identical": bool(same),
           "n": int(m0["n"])}
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
