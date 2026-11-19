"""M20 probe: how many bytes does the 3-bit SH block actually need?

The SH block is 80 % of every file this series ships (18 B of codes + 2 B of per-primitive
scales, against 7.97 B of geometry), and it is currently handed to zstd as one bit-packed
stream.  Before writing an entropy coder, measure what is on the table: a handful of free
layout changes, and the conditional entropies that bound any coder built on the same codes.

Nothing here changes the model; it only re-arranges or re-encodes bytes that already exist.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m4_bytes as M  # noqa: E402
import qfp_rd as Q    # noqa: E402


def _z(data: bytes, level: int = 12) -> int:
    return len(M._zstd(data, level))


def _bits_per_prim(codes: np.ndarray) -> float:
    """Order-0 entropy of one coefficient column, in bits per element."""
    cnt = np.bincount(codes.ravel(), minlength=8).astype(np.float64)
    p = cnt / cnt.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def _cond_bits(col: np.ndarray, ctx: np.ndarray) -> float:
    """H(col | ctx) in bits per element."""
    joint = np.bincount(ctx.astype(np.int64) * 8 + col,
                        minlength=int(ctx.max()) * 8 + 8).astype(np.float64)
    joint = joint.reshape(-1, 8)
    marg = joint.sum(axis=1, keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        p = np.where(marg > 0, joint / np.maximum(marg, 1.0), 0.0)
    q = np.where(marg > 0, marg / marg.sum(), 0.0).ravel()
    ent = -(np.where(p > 0, p * np.log2(np.maximum(p, 1e-300)), 0.0)).sum(axis=1)
    return float((q * ent).sum())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/m360std")
    ap.add_argument("--models", default="/workspace/data/m20",
                    help="flat <scene>.ply layout; takes precedence when the file exists")
    ap.add_argument("--scenes", default="bicycle")
    ap.add_argument("--specs", default="c10_o8_sh3")
    ap.add_argument("--level", type=int, default=12)
    args = ap.parse_args()

    from m20_model import load_model

    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        path = os.path.join(args.models, f"{scene}.ply")
        if not os.path.exists(path):
            path = os.path.join(args.archive, scene, "point_cloud", "iteration_40000",
                                "point_cloud.ply")
        t0 = time.time()
        sp = load_model(path)
        n = int(sp.means.shape[0])
        print(f"[{scene}] {n:,} primitives loaded in {time.time() - t0:.1f} s", flush=True)
        geo, sh = M._attribute_arrays(sp)
        perm = M.morton_order(geo["means"])
        for name in [s.strip() for s in args.specs.split(",") if s.strip()]:
            spec = Q.parse_spec(name)
            t0 = time.time()
            streams, per_prim = M._encode(spec, geo, sh, deg=3, keep_idx=None, perm=perm)
            print(f"\n=== {name}  {sum(map(len, streams.values())) / 1e6:.2f} MB raw  "
                  f"{time.time() - t0:.1f} s ===", flush=True)
            for k in sorted(streams, key=lambda k: -len(streams[k])):
                print(f"  {k:18s} {len(streams[k]) / 1e6:8.2f} MB  "
                      f"zstd {_z(streams[k], args.level) / 1e6:8.2f} MB", flush=True)

            # --- the SH codes themselves, in the encoder's own Morton order ---
            rest = sh["rest"][perm]
            dc = sh["dc"][perm]
            bits = int(spec.sh_bits)
            if bits >= 32:
                print("  (fp32 SH: nothing to re-code)")
                continue
            codes, scale = M.codes_published_sh_parts(rest, bits)
            codes = codes.astype(np.uint8)          # already 0 .. 2**bits - 1
            ncol = codes.shape[1]
            print(f"  codes ({n:,} x {ncol}) value range "
                  f"{codes.min()}..{codes.max()}", flush=True)

            base = _z(M.pack_bits(codes, bits), args.level)
            print(f"\n  V0 current (coef-minor, 1 frame)     {base / 1e6:8.2f} MB "
                  f"{base / n:6.2f} B/prim", flush=True)

            variants = {}
            variants["V1 coef-major"] = _z(M.pack_bits(codes.T, bits), args.level)
            variants["V2 one frame per coef"] = sum(
                _z(M.pack_bits(codes[:, c], bits), args.level) for c in range(ncol))
            planes = [np.packbits((((codes >> b) & 1).astype(np.uint8)).reshape(-1)).tobytes()
                      for b in range(bits)]
            variants["V3 split by bit-plane"] = sum(_z(p, args.level) for p in planes)
            variants["V4 plane x coef frames"] = sum(
                _z(np.packbits(((codes[:, c] >> b) & 1).astype(np.uint8)).tobytes(),
                   args.level) for c in range(ncol) for b in range(bits))
            delta = ((codes.astype(np.int16) - np.roll(codes, 1, axis=0)) % (1 << bits)
                     ).astype(np.uint8)
            variants["V5 delta vs previous prim"] = _z(M.pack_bits(delta, bits), args.level)
            band = codes.copy()
            if ncol >= 3:
                band[:, 3:] = ((codes[:, 3:].astype(np.int16)
                                - codes[:, :-3].astype(np.int16)) % (1 << bits)).astype(np.uint8)
            variants["V6 delta vs coef-3 (band)"] = _z(M.pack_bits(band, bits), args.level)
            # Byte-per-code layouts: zstd's FSE/Huffman stage models *symbols*, so handing it
            # bit-planes throws the 8-symbol structure away.  These are free (no new coder).
            variants["V7 bytes, prim-major"] = _z(codes.tobytes(), args.level)
            variants["V8 bytes, coef-major"] = _z(np.ascontiguousarray(codes.T).tobytes(),
                                                 args.level)
            variants["V9 bytes, coef-major frames"] = sum(
                _z(np.ascontiguousarray(codes[:, c]).tobytes(), args.level)
                for c in range(ncol))
            variants["V10 bytes, delta vs prev"] = _z(delta.astype(np.uint8).tobytes(),
                                                      args.level)
            variants["V11 bytes, band delta"] = _z(band.tobytes(), args.level)
            for k, v in variants.items():
                print(f"  {k:34s} {v / 1e6:8.2f} MB {v * 8 / n:6.2f} B/prim "
                      f"{100.0 * (1 - v / base):+6.1f} %", flush=True)

            # --- entropy bounds: what a context coder could reach on these codes ---
            dcq = np.clip(dc.reshape(n, -1).mean(axis=1) * 0.5 + 0.5, 0, 0.999)
            dcb = (dcq * 8).astype(np.int64)
            prev = np.roll(codes, 1, axis=0)
            h0 = sum(_bits_per_prim(codes[:, c]) for c in range(ncol))
            h1 = sum(_cond_bits(codes[:, c], prev[:, c]) for c in range(ncol))
            h2 = sum(_cond_bits(codes[:, c], prev[:, c] * 8 + dcb) for c in range(ncol))
            h3 = 0.0
            for c in range(ncol):
                for b in range(bits):
                    bit = ((codes[:, c] >> b) & 1).astype(np.int64)
                    pbit = ((prev[:, c] >> b) & 1).astype(np.int64)
                    h3 += _cond_bits(bit, pbit)
            h4 = 0.0
            for c in range(ncol):
                ctx = codes[:, c - 3] if c >= 3 else np.zeros(n, dtype=np.uint8)
                h4 += _cond_bits(codes[:, c], ctx)
            print(f"\n  H0 per-coefficient order-0        {h0 / 8.0:6.2f} B/prim")
            print(f"  H1 | previous primitive (Morton)  {h1 / 8.0:6.2f} B/prim")
            print(f"  H2 | prev + DC bucket             {h2 / 8.0:6.2f} B/prim")
            print(f"  H3 per plane | prev same bit      {h3 / 8.0:6.2f} B/prim")
            print(f"  H4 | coef-3 (adjacent band)       {h4 / 8.0:6.2f} B/prim")
            print(f"  (payload before coding is {ncol * bits / 8.0:6.2f} B/prim; "
                  f"zstd V0 is {base / n:6.2f} B/prim)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
