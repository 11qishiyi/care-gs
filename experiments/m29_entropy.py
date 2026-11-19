"""M29 -- where the last 13.6 bytes go: the entropy of every stream in the shipped shelf.

The shelf codes every attribute at a *fixed* width over a *global* range and lets zstd do the rest.  The
question this probe answers is whether the codes carry structure that a decoder could exploit and zstd
cannot see -- the cluster a primitive belongs to, its own scale, its predecessor in Morton order.

Three numbers per stream, all on the codes the file actually carries:

* ``H0``      order-0 entropy per component (bits), against the width that is paid;
* ``H(ctx)``  the same conditioned on a context the decoder already holds;
* ``bucket``  the practical size: split the codes by that context, pack and zstd each bucket.

Nothing here changes a file; if a context wins, wiring it is a separate, measured step.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

import m19_codec as C
import qfp_rd as Q


def zlen(buf: bytes, level: int = 12) -> int:
    import zstandard as zstd
    return len(zstd.ZstdCompressor(level=level).compress(buf))


def entropy(codes: np.ndarray, bits: int) -> float:
    """Order-0 entropy of an integer code array, in bits per component."""
    k = 1 << int(bits)
    if codes.size == 0:
        return 0.0
    counts = np.bincount(codes.reshape(-1).astype(np.int64), minlength=k)
    p = counts / codes.size
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def cond_entropy(codes: np.ndarray, buckets: np.ndarray, bits: int, n_bucket: int) -> float:
    """``H(code | bucket)`` in bits per component, weighted by the bucket sizes."""
    k = 1 << int(bits)
    total, acc = float(codes.size), 0.0
    flat = codes.reshape(-1).astype(np.int64)
    if buckets.shape[0] != flat.shape[0]:
        buckets = np.repeat(buckets, codes.shape[1])
    bk = buckets
    for b in range(n_bucket):
        sel = flat[bk == b]
        if sel.size == 0:
            continue
        counts = np.bincount(sel, minlength=k)
        p = counts / sel.size
        p = p[p > 0]
        acc += float(sel.size) * float(-(p * np.log2(p)).sum())
    return acc / total if total else 0.0


def order1_entropy(codes: np.ndarray, bits: int) -> float:
    """``H(code_t | code_{t-1})`` per component, i.e. what a Markov coder could reach."""
    k = 1 << int(bits)
    flat = codes.reshape(-1).astype(np.int64)
    if flat.size < 2:
        return 0.0
    prev, cur = flat[:-1], flat[1:]
    #: a 2**bits x 2**bits table is 64 k entries at 8 bits and 1 M at 10 bits -- both fine
    tab = np.bincount(prev * k + cur, minlength=k * k).reshape(k, k).astype(np.float64)
    tot = tab.sum(axis=1, keepdims=True)
    p = np.divide(tab, np.maximum(tot, 1.0), out=np.zeros_like(tab), where=tot > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -np.where(p > 0, p * np.log2(np.maximum(p, 1e-300)), 0.0)
    w = tot[:, 0] / max(1.0, tot.sum())
    return float((h.sum(axis=1) * w).sum())


def bucket_bytes(codes: np.ndarray, buckets: np.ndarray, bits: int, n_bucket: int,
                 m: "M", level: int = 12) -> int:
    """Bytes after splitting by bucket, packing each bucket, and zstd-ing each."""
    total = 0
    for b in range(n_bucket):
        sel = codes[buckets == b] if codes.ndim == 1 else codes[buckets == b]
        if sel.size == 0:
            continue
        total += zlen(m.pack_bits(np.ascontiguousarray(sel.reshape(-1)), int(bits)), level)
    return total


def stream_codes(streams: dict, meta: dict, spec, name: str, dims: int, bits: int):
    buf = streams.get(name)
    if buf is None:
        return None
    n = int(meta["n"])
    return C.unpack_bits(buf, int(bits), n * dims, dtype=np.uint16).reshape(n, dims)


def main() -> int:
    ap = argparse.ArgumentParser(description="M29 entropy probe over a shipped container")
    ap.add_argument("--gs1", required=True)
    ap.add_argument("--json")
    ap.add_argument("--level", type=int, default=12)
    a = ap.parse_args()

    import importlib
    m = importlib.import_module("m4_bytes")
    meta, streams = C.read_container(a.gs1)
    spec = Q.parse_spec(str(meta["spec"]))
    n = int(meta["n"])
    size = os.path.getsize(a.gs1)
    print(f"file {a.gs1}  {size/1e6:.2f} MB  n={n:,}  spec={meta['spec']}  "
          f"B/prim={size/n:.2f}")

    rows = []
    #: the streams that carry per-primitive attributes, in the decoder's order
    plan = []
    cbits = getattr(spec, "means_cluster_bits", None)
    if cbits:
        plan.append(("cluster_off", 3, int(cbits)))
    plan.append(("geo_scales", 3, int(spec.geo.get("scales", 8))))
    bq = getattr(spec, "quat_st3", None)
    if bq is not None:
        plan.append(("geo_quat_which", 1, 2))
        plan.append(("geo_quat_abc", 3, int(bq)))
    plan.append(("geo_opacities", 1, int(spec.geo.get("opacities", 8))))

    #: contexts the decoder already holds when it reaches each stream
    pos_bucket = None
    if "cluster_off" in streams and cbits:
        off = stream_codes(streams, meta, spec, "cluster_off", 3, int(cbits))
        blk = np.repeat(np.arange((n + 255) // 256), 256)[:n]
        pos_bucket = (blk % 16).astype(np.int64)          # 16 coarse spatial bands, Morton order
    scale_bucket = None

    for name, dims, bits in plan:
        codes = stream_codes(streams, meta, spec, name, dims, bits)
        if codes is None:
            continue
        raw = len(streams[name])
        packed = zlen(streams[name], a.level)
        h0 = entropy(codes, bits)
        row = {"stream": name, "dims": dims, "bits": bits, "raw": raw, "zstd": packed,
               "H0": round(h0, 3), "fixed_bits": bits, "n": int(codes.shape[0]),
               "H1": round(order1_entropy(codes, bits), 3),
               "bits_via_zstd": round(8.0 * packed / max(1, codes.size), 3)}
        #: context 1: coarse spatial band
        if pos_bucket is not None:
            hc = cond_entropy(codes, pos_bucket, bits, 16)
            bc = bucket_bytes(codes, pos_bucket, bits, 16, m, a.level)
            row.update({"H_pos": round(hc, 3), "bytes_pos": bc})
        #: context 2: the primitive's own first scale component (available for everything after scales)
        if scale_bucket is not None:
            hc = cond_entropy(codes, scale_bucket, bits, 8)
            bc = bucket_bytes(codes, scale_bucket, bits, 8, m, a.level)
            row.update({"H_scale": round(hc, 3), "bytes_scale": bc})
        rows.append(row)
        if name == "geo_scales":
            s0 = codes[:, 0]
            scale_bucket = np.clip((s0.astype(np.int64) * 8) >> int(bits), 0, 7)

    #: bytes now vs the best practical alternative, per stream
    print(f"\n{'stream':>16}{'dims':>5}{'bits':>5}{'zstd MB':>9}{'B/prim':>8}{'b/code':>8}"
          f"{'H0':>7}{'H1':>7}{'H(pos)':>8}{'pos MB':>8}{'H(scl)':>8}{'scl MB':>8}")
    tot_now = tot_best = 0
    for r in rows:
        now = r["zstd"]
        best = min([r.get("bytes_pos", 1 << 60), r.get("bytes_scale", 1 << 60), now])
        tot_now += now
        tot_best += best
        print(f"{r['stream']:>16}{r['dims']:>5}{r['bits']:>5}{now/1e6:>9.3f}"
              f"{now/r['n']:>8.3f}{r['bits_via_zstd']:>8.2f}{r['H0']:>7.2f}{r['H1']:>7.2f}"
              f"{r.get('H_pos', float('nan')):>8.2f}{r.get('bytes_pos', 0)/1e6:>8.3f}"
              f"{r.get('H_scale', float('nan')):>8.2f}{r.get('bytes_scale', 0)/1e6:>8.3f}")
    print(f"\nattribute streams now {tot_now/1e6:.2f} MB, best practical {tot_best/1e6:.2f} MB "
          f"({100.0*(tot_now-tot_best)/max(1,tot_now):.1f} % saved)")
    print(f"whole file {size/1e6:.2f} MB -> projected "
          f"{(size - tot_now + tot_best)/1e6:.2f} MB ({size/1e6*1000.0/1.0/ (size/n) /1e0:.2f} B/prim now)")

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"file": a.gs1, "bytes": size, "n": n, "rows": rows,
                       "attr_now": tot_now, "attr_best": tot_best}, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
