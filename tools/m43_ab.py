"""M43 -- three encoder variants, one host, one process each: peak RSS, wall clock, md5.

    python -m tools.m43_ab --ply /mnt/m35cache/bicycle.ply --variant m43 --json ...
    python -m tools.m43_ab --ply ... --variant m42     # sliced, int64 codes, three candidates
    python -m tools.m43_ab --ply ... --variant legacy  # pre-M42 whole-array

The verdict is a same-node comparison, because the same code path has measured 58.9 s and 150.1 s on two hosts in
the same pool (M41 vs M42). Every variant writes its own file and every variant has to produce the same md5.
"""
import argparse
import hashlib
import json
import os
import resource
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "experiments"), os.path.join(ROOT, "research", "code")):
    if p not in sys.path:
        sys.path.insert(0, p)


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _legacy_whole_array(module):
    """Pre-M42: whole-array quantiser and whole-array bit planes."""
    import numpy as np

    def codes(block, bits, chunk=None):
        qmax = (1 << (bits - 1)) - 1
        b = np.asarray(block, dtype=np.float64).reshape(block.shape[0], -1)
        scale = np.abs(b).max(axis=1, keepdims=True) / float(qmax)
        scale = np.where(scale > 0, scale, 1.0)
        c = np.rint(b / scale)
        c = np.clip(c, -qmax - 1, qmax)
        return (c + (qmax + 1)).astype(np.int64), scale[:, 0]

    def pack(codes_arr, bits, chunk=None):
        bits = int(bits)
        flat = np.asarray(codes_arr, dtype=np.int64).reshape(-1)
        if bits == 8:
            return flat.astype(np.uint8).tobytes()
        if bits == 16:
            return flat.astype(np.uint16).tobytes()
        if bits == 32:
            return flat.astype(np.uint32).tobytes()
        planes = ((flat[:, None] >> np.arange(bits)[None, :]) & 1).astype(np.uint8)
        return np.packbits(planes.reshape(-1)).tobytes()

    module.codes_published_sh_parts = codes
    module.pack_bits = pack


def _m42_sliced_int64(module):
    """M42 as shipped: sliced, but the code array is int64 and the packer widens the whole array."""
    import numpy as np

    def codes(block, bits, chunk=1 << 20):
        qmax = (1 << (bits - 1)) - 1
        rows = int(block.shape[0])
        cols = int(np.prod(block.shape[1:]))
        out = np.empty((rows, cols), dtype=np.int64)
        scale = np.empty((rows, 1), dtype=np.float64)
        flat = block.reshape(rows, cols)
        for i in range(0, rows, chunk):
            seg = np.asarray(flat[i:i + chunk], dtype=np.float64)
            s = np.abs(seg).max(axis=1, keepdims=True) / float(qmax)
            s = np.where(s > 0, s, 1.0)
            c = seg / s
            np.rint(c, out=c)
            np.clip(c, -qmax - 1, qmax, out=c)
            out[i:i + chunk] = c + (qmax + 1)
            scale[i:i + chunk] = s
        return out, scale[:, 0]

    def pack(codes_arr, bits, chunk=1 << 24):
        flat = np.asarray(codes_arr, dtype=np.int64).reshape(-1)
        bits = int(bits)
        if bits == 8:
            return flat.astype(np.uint8).tobytes()
        if bits == 16:
            return flat.astype(np.uint16).tobytes()
        if bits == 32:
            return flat.astype(np.uint32).tobytes()
        dtype = np.uint8 if bits <= 8 else np.uint16
        shifts = np.arange(bits, dtype=dtype)
        step = max(8, (int(chunk) // bits // 8) * 8)
        out = []
        for i in range(0, max(1, flat.size), step):
            seg = flat[i:i + step].astype(dtype)
            planes = (seg[:, None] >> shifts[None, :]) & dtype(1)
            out.append(np.packbits(planes.reshape(-1)).tobytes())
        return b"".join(out)

    module.codes_published_sh_parts = codes
    module.pack_bits = pack


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--variant", default="m44", choices=("m44", "m43", "m42", "legacy"))
    ap.add_argument("--spec", default="gp6-6-6_c8_sh3")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default="/workspace/res/m43")
    ap.add_argument("--json")
    args = ap.parse_args()

    import m4_bytes as M
    import m19_codec as C
    import m20_model
    import m24_alpha as A

    if args.variant == "legacy":
        _legacy_whole_array(M)
    elif args.variant == "m42":
        _m42_sliced_int64(M)

    os.makedirs(args.out, exist_ok=True)
    scene = os.path.basename(args.ply).replace(".ply", "")
    path = os.path.join(args.out, f"m43_{scene}_{args.variant}.gs1")

    t0 = time.time()
    splats = m20_model.load_model(args.ply)
    t_load = time.time() - t0
    t1 = time.time()
    rec = A.build(splats, rank=16, bits_total=48, level=12, spec_name=args.spec, mode="auto",
                  log=lambda *a: None)
    t_build = time.time() - t1
    t2 = time.time()
    meta = dict(rec["meta"])
    meta["min_frame"] = int(C.MIN_FRAME)
    info = C.write_container(path, rec["streams"], meta, 12, jobs=args.jobs)
    t_write = time.time() - t2
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0

    row = {"scene": scene, "variant": args.variant, "n": int(splats.means.shape[0]), "spec": args.spec,
           "jobs": args.jobs, "load_s": round(t_load, 1), "build_s": round(t_build, 1),
           "write_s": round(t_write, 1), "total_s": round(t_load + t_build + t_write, 1),
           "bytes": info["bytes"], "md5": _md5(path), "peak_rss_gb": round(peak, 2)}
    print(json.dumps(row))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)


if __name__ == "__main__":
    main()
