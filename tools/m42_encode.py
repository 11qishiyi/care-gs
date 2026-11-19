"""M42 -- the two encoding stages, measured the way M41 measured the write.

    python -m tools.m42_encode --ply /mnt/m35cache/bicycle.ply --jobs 4 --json /workspace/res/m42/enc.json

Runs the shipping build (``m24_alpha.build``) plus the container write in a fresh process and reports wall clock,
the container's size and md5, and peak RSS. The md5 is the criterion: M40's containers are the reference, so an
optimisation that changes a byte shows up here rather than in a footnote.
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


def _install_legacy(module):
    """Restore the whole-array implementations M42 replaced, for a same-node A/B.

    The comparison that matters is old against new on one machine, one process layout, one model: the previous
    round's numbers came from a different host, so they cannot be used as a baseline for a wall-clock claim.
    """
    import numpy as np

    def legacy_codes_published_sh_parts(block, bits, chunk=None):
        qmax = (1 << (int(bits) - 1)) - 1
        if qmax <= 0:
            raise ValueError(f"{bits}-bit SH has qmax=0 and cannot be coded")
        b = np.asarray(block, dtype=np.float64).reshape(block.shape[0], -1)
        scale = np.abs(b).max(axis=1, keepdims=True) / float(qmax)
        scale = np.where(scale > 0, scale, 1.0)
        codes = np.rint(b / scale)
        codes = np.clip(codes, -qmax - 1, qmax)
        return (codes + (qmax + 1)).astype(np.int64), scale[:, 0]

    def legacy_pack_bits(codes, bits, chunk=None):
        bits = int(bits)
        flat = np.asarray(codes, dtype=np.int64).reshape(-1)
        if bits == 8:
            return flat.astype(np.uint8).tobytes()
        if bits == 16:
            return flat.astype(np.uint16).tobytes()
        if bits == 32:
            return flat.astype(np.uint32).tobytes()
        planes = ((flat[:, None] >> np.arange(bits)[None, :]) & 1).astype(np.uint8)
        return np.packbits(planes.reshape(-1)).tobytes()

    module.codes_published_sh_parts = legacy_codes_published_sh_parts
    module.pack_bits = legacy_pack_bits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--spec", default="gp6-6-6_c8_sh3")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default="/workspace/res/m42")
    ap.add_argument("--json")
    ap.add_argument("--legacy", action="store_true",
                    help="run the pre-M42 whole-array quantiser and bit-packer (same-node baseline)")
    args = ap.parse_args()

    import m4_bytes as M
    import m19_codec as C
    import m20_model
    import m24_alpha as A

    if args.legacy:
        _install_legacy(M)
    variant = "legacy" if args.legacy else "sliced"

    os.makedirs(args.out, exist_ok=True)
    scene = os.path.basename(args.ply).replace(".ply", "")
    path = os.path.join(args.out, f"m42_{scene}_{variant}.gs1")

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

    row = {"scene": scene, "variant": variant, "n": int(splats.means.shape[0]), "spec": args.spec,
           "jobs": args.jobs,
           "load_s": round(t_load, 1), "build_s": round(t_build, 1), "write_s": round(t_write, 1),
           "total_s": round(t_load + t_build + t_write, 1), "bytes": info["bytes"],
           "md5": _md5(path), "peak_rss_gb": round(peak, 2)}
    print(json.dumps(row))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)


if __name__ == "__main__":
    main()
