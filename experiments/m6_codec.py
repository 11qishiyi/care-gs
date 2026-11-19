#!/usr/bin/env python3
"""M6: how much of the code's own entropy does the shipped format actually reach?

M4/M5 measured one codec -- bit-packing -> Morton order -> zstd-12 -- and found it beats the
analytic byte model everywhere.  The next question is whether that codec is near the floor or
whether a better one would move the rate axis substantially.  If a cheaper coder exists, every
equal-byte comparison in M1/M3/M5 was made at a *pessimistic* price, and the RD curves have to
be re-drawn on the better axis before the paper quotes a rate.

Coders, all lossless on the same quantised integer codes:

  c0_packed        fixed-width bit packing, Morton order, no entropy coding  (== the model)
  c1_zstd          c0 + zstd
  c2_delta         modular first difference along Morton order, packed, zstd
  c3_delta_planes  c2 transposed to bit planes, zstd  (byte-shuffle for the code domain)
  c9_entropy       order-0 bound: sum over bit planes of H(p_k) * n  -- not encodable, a floor

float32 attributes are handled by reinterpreting them as uint32 bit patterns, so the same four
coders apply; ``c3`` is then the usual byte-shuffle filter and ``c9`` is the per-plane bound.

Usage (node):
  python experiments/m6_codec.py --archive /workspace/data/out3dgs \
      --scenes bicycle,flowers --specs clean,p30,m16_o8_sh3 --out /workspace/res/m6/m6.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

C.add_code_root()

import m4_bytes as M4  # noqa: E402

CODECS = ("c0_packed", "c1_zstd", "c2_delta", "c3_delta_planes", "c9_entropy")
FP32_BITS = 32


# --------------------------------------------------------------------------------------- #
# code extraction (mirror of m4_bytes._encode, but keeping the integers)
# --------------------------------------------------------------------------------------- #
def streams_for(spec, geo, sh, deg: int, keep_idx=None, perm=None) -> dict:
    """``{stream_name: (codes (N,C) uint32, bits)}`` in the shipping layout."""
    def take(a):
        a = a if keep_idx is None else a[keep_idx]
        return a if perm is None else a[perm]

    out = {}
    for attr in M4.GEO_ORDER:
        bits = int(spec.geo.get(attr, FP32_BITS))
        arr = take(np.asarray(geo[attr]))
        if bits >= FP32_BITS:
            codes = np.ascontiguousarray(arr.astype(np.float32)).view(np.uint32)
        else:
            codes = M4.codes_grid(arr, bits).astype(np.uint32)
        out[f"geo_{attr}"] = (np.ascontiguousarray(codes), bits)

    sh_bits = int(spec.sh_bits)
    deg_out = int(spec.out_degree(deg))
    scales = []
    blocks = [("sh_dc", sh["dc"])]
    if deg_out >= 1:
        rest = sh["rest"]
        if deg_out < deg:
            rest = rest[:, : (deg_out + 1) ** 2 - 1, :]
        blocks.append(("sh_rest", rest))
    for key, block in blocks:
        block = take(np.asarray(block))
        n = block.shape[0]
        cols = int(np.prod(block.shape[1:]))
        flat = block.reshape(n, cols)
        if sh_bits >= FP32_BITS:
            codes = np.ascontiguousarray(flat.astype(np.float32)).view(np.uint32).reshape(n, cols)
        else:
            codes, scale = M4.codes_published_sh_parts(block, sh_bits)
            codes = codes.astype(np.uint32).reshape(n, cols)
            scales.append(scale)
        out[key] = (np.ascontiguousarray(codes), sh_bits)
    if scales:
        # one byte per SH block, normalised by a scene-wide reference (as in m4_bytes)
        sc = np.stack(scales, axis=1)
        ref = np.maximum(sc.max(axis=0, keepdims=True), 1e-12)
        out["sh_scale"] = (np.clip(np.rint(sc / ref * 255.0), 0, 255).astype(np.uint32), 8)
    return out


# --------------------------------------------------------------------------------------- #
# coders
# --------------------------------------------------------------------------------------- #
CHUNK = 4_000_000          # codes per chunk: keeps a 32-plane stack under ~128 MB


def delta_codes(codes: np.ndarray, bits: int) -> np.ndarray:
    """Modular first difference along axis 0; primitives are already in Morton order.

    Done in uint32 so the subtraction wraps modulo 2**32; masking with ``2**bits-1``
    afterwards is exact, because ``(a-b) mod 2**32 mod 2**bits == (a-b) mod 2**bits``.
    """
    out = np.array(codes, dtype=np.uint32, copy=True)
    if codes.shape[0] > 1:
        np.subtract(codes[1:], codes[:-1], out=out[1:], dtype=np.uint32)
        if int(bits) < 32:
            out[1:] &= np.uint32((1 << int(bits)) - 1)
    return out


def _plane_slices(n: int, chunk: int = CHUNK):
    for start in range(0, n, chunk):
        yield start, min(n, start + chunk)


def to_planes(codes: np.ndarray, bits: int) -> np.ndarray:
    """(N, C) codes -> (bits, N*C) uint8 bit planes, most significant plane first.

    Only used for modest streams (tests); the coders below work chunk-wise.
    """
    flat = np.asarray(codes).reshape(-1)
    planes = np.empty((int(bits), flat.size), dtype=np.uint8)
    for k in range(int(bits)):
        planes[bits - 1 - k] = ((flat >> np.uint64(k)) & np.uint64(1)).astype(np.uint8)
    return planes


def _plane_bytes_streams(codes: np.ndarray, bits: int, level: int) -> int:
    """zstd over the packed bit planes, worked out chunk by chunk to bound memory."""
    flat = np.asarray(codes).reshape(-1)
    total = 0
    for lo, hi in _plane_slices(flat.size):
        seg = flat[lo:hi]
        planes = np.empty((int(bits), seg.size), dtype=np.uint8)
        for k in range(int(bits)):
            planes[bits - 1 - k] = ((seg >> np.uint64(k)) & np.uint64(1)).astype(np.uint8)
        raw = b"".join(np.packbits(p).tobytes() for p in planes)
        total += len(M4._zstd(raw, level))
    return total


def entropy_bound(codes: np.ndarray, bits: int) -> int:
    """Order-0 bound in bytes for the bit-plane decomposition (binary entropy per plane)."""
    flat = np.asarray(codes).reshape(-1)
    total_bits = 0.0
    for k in range(int(bits)):
        ones = 0
        for lo, hi in _plane_slices(flat.size):
            ones += int(np.count_nonzero((flat[lo:hi] >> np.uint64(k)) & np.uint64(1)))
        p = ones / float(max(1, flat.size))
        if 0.0 < p < 1.0:
            total_bits += flat.size * (-(p * np.log2(p) + (1 - p) * np.log2(1 - p)))
    return int(np.ceil(total_bits / 8.0))


def encode_stream(codes: np.ndarray, bits: int, codec: str, level: int = 12) -> int:
    if codec == "c0_packed":
        return len(M4.pack_bits(codes, bits))
    if codec == "c1_zstd":
        return len(M4._zstd(M4.pack_bits(codes, bits), level))
    if codec == "c9_entropy":
        return entropy_bound(codes, bits)
    d = delta_codes(codes, bits)
    if codec == "c2_delta":
        return len(M4._zstd(M4.pack_bits(d, bits), level))
    if codec == "c3_delta_planes":
        return _plane_bytes_streams(d, bits, level)
    raise ValueError(f"unknown codec {codec!r}")


def encode_spec(geo, sh, spec, deg: int, keep_idx=None, perm=None, level: int = 12,
                codecs=CODECS) -> dict:
    """Bytes per stored primitive under every coder, for one variant of one asset."""
    streams = streams_for(spec, geo, sh, deg, keep_idx, perm)
    n_stored = next(iter(streams.values()))[0].shape[0]
    out = {"n_stored": int(n_stored), "codecs": {},
           "model_bytes_per_prim": float(spec.bytes_per_prim(deg)),
           "rate_vs_fp32_model": float(spec.rate_vs_fp32(deg))}
    for codec in codecs:
        total, per_stream = 0, {}
        for name, (codes, bits) in streams.items():
            b = encode_stream(codes, bits, codec, level)
            per_stream[name] = {"bits": int(bits), "bytes": int(b)}
            total += b
        # the sh_scale stream already charges 2 bytes per primitive (see streams_for)
        out["codecs"][codec] = {"bytes": int(total),
                                "bytes_per_prim": total / max(1, n_stored),
                                "streams": per_stream}
    return out


SHIPPED = "c1_zstd"  # M6 verdict: delta+planes wins on fp32 payloads only (2-5%) and loses
# 12-26% on quantised payloads, so the shipped stream stays Morton+zstd.  Kept as a
# constant because the row schema below reports this coder as `zstd_morton_*`.


def measure_scene(splats, specs, level: int = 12, log=print) -> dict:
    """One dict per spec: the M4/M5 row schema (so ``m1_analyse --bytes-json`` reads it
    directly) plus a ``detail`` table with every coder."""
    geo, sh = M4._attribute_arrays(splats)
    deg = int(splats.sh_degree)
    n = geo["means"].shape[0]
    full_order = M4.morton_order(geo["means"])
    rows = []
    for spec in specs:
        keep = float(spec.keep)
        keep_idx = None if keep >= 1.0 else np.arange(max(1, int(round(keep * n))))
        perm = full_order if keep_idx is None else M4.morton_order(geo["means"][keep_idx])
        enc = encode_spec(geo, sh, spec, deg, keep_idx, perm, level)
        stored = int(enc["n_stored"])
        cc = enc["codecs"]
        # Same row schema as m4_bytes.measure_scene, but the "shipped" number is the
        # best coder measured here rather than Morton+zstd, so the M5 analysis script
        # can be pointed at this file unchanged.
        rows.append(dict(
            spec=spec.name, keep=keep, stored=stored, n=n,
            model_bytes_per_prim=enc["model_bytes_per_prim"],
            packed_bytes_per_prim=cc["c0_packed"]["bytes_per_prim"],
            zstd_bytes_per_prim=cc["c1_zstd"]["bytes_per_prim"],
            zstd_morton_bytes_per_prim=cc[SHIPPED]["bytes_per_prim"],
            streams=dict(cc[SHIPPED]["streams"]),
            detail={c: {"bytes": cc[c]["bytes"], "bytes_per_prim": cc[c]["bytes_per_prim"]}
                    for c in CODECS},
            entropy_gap_pct=100.0 * (cc[SHIPPED]["bytes_per_prim"] /
                                     max(1e-9, cc["c9_entropy"]["bytes_per_prim"]) - 1.0),
        ))
        log(f"  {spec.name:<18} model {rows[-1]['model_bytes_per_prim']:7.2f}  " +
            "  ".join(f"{c} {cc[c]['bytes_per_prim']:6.2f}" for c in CODECS) +
            f"   gap {rows[-1]['entropy_gap_pct']:+.1f}%")
    return rows


# --------------------------------------------------------------------------------------- #
# self test
# --------------------------------------------------------------------------------------- #
class _FakeSplats:
    """Synthetic asset with a spatially coherent lattice (so Morton/delta have something to find)."""

    def __init__(self, n: int = 4096, degree: int = 3, seed: int = 0):
        rng = np.random.default_rng(seed)
        grid = int(np.ceil(n ** (1 / 3)))
        xyz = np.stack(np.meshgrid(*[np.arange(grid)] * 3, indexing="ij"), -1).reshape(-1, 3)[:n]
        xyz = xyz.astype(np.float32) / grid + rng.normal(0, 0.004, (len(xyz), 3)).astype(np.float32)
        self.means = xyz
        self.scales = (np.full((len(xyz), 3), 0.01, np.float32) *
                       np.exp(rng.normal(0, 0.2, (len(xyz), 3))).astype(np.float32))
        q = rng.normal(0, 1, (len(xyz), 4)).astype(np.float32)
        self.quats = (q / np.linalg.norm(q, axis=1, keepdims=True)).astype(np.float32)
        self.opacities = rng.uniform(0.1, 0.9, (len(xyz), 1)).astype(np.float32)
        self.sh0 = rng.normal(0, 0.5, (len(xyz), 1, 3)).astype(np.float32)
        self.shN = rng.normal(0, 0.1, (len(xyz), 3 * ((degree + 1) ** 2 - 1) // 3, 3)).astype(np.float32)
        self.sh_degree = degree
        self.n = len(xyz)


class _FakeSplatsTorch(_FakeSplats):
    """Same asset, but exposing the ``.detach().cpu().numpy()`` surface m4_bytes expects."""

    class _T:
        def __init__(self, a):
            self._a = a

        def detach(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self._a

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        for name in ("means", "scales", "quats", "opacities", "sh0", "shN"):
            setattr(self, name, self._T(getattr(self, name)))


def selftest() -> int:
    import qfp_rd as Q

    fails = []

    def chk(name, cond, extra=""):
        print(f"[{'ok' if cond else 'FAIL'}] {name}{(' ' + extra) if extra else ''}")
        if not cond:
            fails.append(name)

    codes = np.array([[0, 1], [1, 3], [3, 4], [4, 4]], dtype=np.uint32)
    d = delta_codes(codes, 4)
    chk("delta keeps first row", np.array_equal(d[0], codes[0]))
    chk("delta is modular", int(d.max()) < 16)
    chk("delta round-trips",
        np.array_equal(np.cumsum(d.astype(np.int64), axis=0) % 16, codes.astype(np.int64) % 16))
    planes = to_planes(codes, 4)
    chk("plane count", planes.shape == (4, 8), str(planes.shape))
    packed_planes = sum(len(np.packbits(p).tobytes()) for p in planes)
    chk("plane packing size matches the model", packed_planes == codes.size * 4 // 8,
        f"{packed_planes} vs {codes.size * 4 // 8}")
    chk("entropy of a constant plane is 0", entropy_bound(np.zeros((64, 1), np.uint32), 8) == 0)
    chk("entropy of a uniform plane is about n/8 bytes",
        abs(entropy_bound(np.arange(256, dtype=np.uint32).reshape(-1, 1), 8) -
            256 * 8 / 8.0) <= 8,
        str(entropy_bound(np.arange(256, dtype=np.uint32).reshape(-1, 1), 8)))

    sp = _FakeSplatsTorch()
    specs = [Q.parse_spec(n) for n in ("clean", "p30", "m16_o8_sh3", "m16_o6_sh2", "d1_m16_o8_sh4")]
    geo, sh = M4._attribute_arrays(sp)
    order = M4.morton_order(geo["means"])
    for spec in specs:
        keep = float(spec.keep)
        keep_idx = None if keep >= 1.0 else np.arange(max(1, int(round(keep * sp.n))))
        perm = order if keep_idx is None else M4.morton_order(geo["means"][keep_idx])
        row = encode_spec(geo, sh, spec, sp.sh_degree, keep_idx, perm, level=6)
        cc = row["codecs"]
        chk(f"{spec.name}: c0 matches the model",
            abs(cc["c0_packed"]["bytes_per_prim"] - row["model_bytes_per_prim"]) <= 1.0,
            f"{cc['c0_packed']['bytes_per_prim']:.2f} vs {row['model_bytes_per_prim']:.2f}")
        chk(f"{spec.name}: zstd never costs more than the model",
            cc["c1_zstd"]["bytes_per_prim"] <= row["model_bytes_per_prim"] + 1e-9,
            f"{cc['c1_zstd']['bytes_per_prim']:.2f}")
        # Per-plane order-0 entropy is a lower bound for coding each plane alone; zstd on
        # packed planes can still beat it by using the correlation *between* planes, so the
        # gap is reported, not asserted.
        print(f"[info] {spec.name}: delta+planes {cc['c3_delta_planes']['bytes_per_prim']:.2f} "
              f"B/prim, order-0 floor {cc['c9_entropy']['bytes_per_prim']:.2f}, "
              f"gap {100.0 * (cc['c3_delta_planes']['bytes_per_prim'] / max(1e-9, cc['c9_entropy']['bytes_per_prim']) - 1):+.1f}%")
        chk(f"{spec.name}: entropy bound is under the packed size",
            cc["c9_entropy"]["bytes_per_prim"] <= cc["c0_packed"]["bytes_per_prim"] + 1e-9,
            f"{cc['c9_entropy']['bytes_per_prim']:.2f} vs {cc['c0_packed']['bytes_per_prim']:.2f}")

    # delta coding must pay off on a stream with a constant slope (what Morton order buys)
    ramp = np.cumsum(np.full((4096, 1), 7, np.uint32), axis=0) % 256
    noise = np.random.default_rng(0).integers(0, 256, (4096, 1)).astype(np.uint32)
    for label, arr in (("ramp", ramp), ("noise", noise)):
        d_ok = encode_stream(arr, 8, "c3_delta_planes", 9)
        z_ok = encode_stream(arr, 8, "c1_zstd", 9)
        print(f"[info] {label}: delta+planes {d_ok} B, plain zstd {z_ok} B")
    chk("delta coding wins on a ramp",
        encode_stream(ramp, 8, "c3_delta_planes", 9) < encode_stream(ramp, 8, "c1_zstd", 9))
    print(f"\n{'ALL PASS' if not fails else 'FAILURES: ' + ', '.join(fails)}")
    return 0 if not fails else 1


# --------------------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M6 entropy-coder comparison")
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill")
    ap.add_argument("--specs", default="clean,p30,m16_o8_sh8,m16_o8_sh4,m16_o8_sh3,"
                                       "m16_o6_sh3,m16_o6_sh2,d1_m16_o8_sh4")
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--out", default="/workspace/res/m6/m6_codec.json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    import qfp_rd as Q  # noqa: WPS433
    from calib.gsrender import load_splats  # noqa: WPS433

    specs = [Q.parse_spec(s.strip()) for s in args.specs.split(",") if s.strip()]
    scenes = [s.strip() for s in args.scenes.split(",") if s.strip()]
    out = {"level": args.level, "codecs": list(CODECS), "shipped": SHIPPED,
           "backend": M4.ZSTD_BACKEND, "includes_scale_bytes": True,
           "specs": [s.name for s in specs], "scenes": []}
    for scene in scenes:
        path = args.ply_pattern.format(archive=args.archive, scene=scene)
        print(f"== {scene}")
        if not os.path.exists(path):
            print(f"  [skip] no ply at {path}")
            continue
        sp = load_splats(path, device="cpu")
        rows = measure_scene(sp, specs, args.level)
        out["scenes"].append({"scene": scene, "ply": path, "n": int(sp.n),
                              "n_primitives": int(sp.n),
                              "sh_degree": int(sp.sh_degree), "rows": rows})
        del sp
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
    print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
