"""M41 -- how long the container takes to write, as a function of how many workers write frames.

The frames of a container are independent zstd calls, so this is a scheduling question. The driver builds the
streams once, then writes the *same* container with N = 1, 2, 4, 8 workers, timing each write and hashing each
file; a byte difference would make the speed-up meaningless, so the hash is printed next to the seconds.

    python -m experiments.m41_par --ply /data/bicycle.ply --jobs 1,2,4,8 --out /res/m41

Each worker count runs in its own process (``--one N``) so ``ru_maxrss`` is that write's peak and not the
encoder's whole history -- the same trap M25 hit when it measured decode RSS inside the encoder.
"""
import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.dirname(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

SPEC = "gp6-6-6_c8_sh3"


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build_streams(ply, spec=SPEC):
    """Build the shipping container's streams (M22 basis colour block), then measure only the write.

    Timing ``encode_model`` alone would time a *different* container: it writes the scalar 3-bit SH ladder,
    which is 126 MB on bicycle against the shipping 76.6 MB.  The shipping streams come from
    ``m24_alpha.build``, so that is what the pool has to be measured on.
    """
    import m20_model
    import m24_alpha as A

    splats = m20_model.load_model(ply)
    t0 = time.time()
    rec = A.build(splats, rank=16, bits_total=48, level=12, spec_name=spec, mode="auto", log=lambda *a: None)
    t1 = time.time()
    return splats, rec["streams"], rec["meta"], t1 - t0


def write_once(streams, meta, path, jobs):
    import m19_codec as C

    meta = dict(meta)
    meta.setdefault("min_frame", int(C.MIN_FRAME))
    t0 = time.time()
    info = C.write_container(path, streams, meta, 12, jobs=jobs)
    t1 = time.time()
    return {"jobs": jobs, "seconds": round(t1 - t0, 2), "bytes": info["bytes"],
            "md5": _md5(path), "rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply")
    ap.add_argument("--spec", default=SPEC)
    ap.add_argument("--jobs", default="1,2,4,8")
    ap.add_argument("--out", default="/workspace/res/m41")
    ap.add_argument("--json")
    ap.add_argument("--one", type=int, default=None, help="internal: write one container and print its row")
    ap.add_argument("--cache", default=None, help="npz with the built streams, so --one skips the build")
    args = ap.parse_args()

    if args.one:
        import numpy as np

        if not args.cache:
            raise SystemExit("--one needs --cache")
        z = np.load(args.cache, allow_pickle=True)
        streams = {k: z[k].tobytes() for k in z["__names__"]}
        meta = json.loads(str(z["__meta__"]))
        path = os.path.join(args.out, f"m41_j{args.one}.gs1")
        print(json.dumps(write_once(streams, meta, path, args.one)))
        return

    os.makedirs(args.out, exist_ok=True)
    splats, streams, meta, build_s = build_streams(args.ply, args.spec)
    n = int(meta["n"])
    print(f"{n:,} primitives, streams built in {build_s:.1f} s")

    import numpy as np

    cache = os.path.join(args.out, "streams.npz")
    payload = {k: np.frombuffer(v, dtype=np.uint8) for k, v in streams.items()}
    payload["__names__"] = np.array(sorted(streams), dtype=object)
    payload["__meta__"] = np.array(json.dumps(meta))
    np.savez(cache, **payload)

    rows = []
    for j in [int(x) for x in args.jobs.split(",")]:
        out = subprocess.run([sys.executable, "-m", "experiments.m41_par", "--one", str(j),
                              "--out", args.out, "--cache", cache],
                             capture_output=True, text=True)
        if out.returncode != 0:
            print(out.stderr[-400:])
            continue
        rows.append(json.loads(out.stdout.strip().splitlines()[-1]))
        r = rows[-1]
        print(f"jobs={r['jobs']:2d}  {r['seconds']:7.2f} s  {r['bytes']:12,} B  "
              f"rss {r['rss_mb']:6.1f} MB  md5 {r['md5']}")

    if rows:
        base = rows[0]
        print()
        for r in rows[1:]:
            print(f"jobs={r['jobs']:2d}: {r['seconds'] / base['seconds']:.3f}x wall, "
                  f"same file: {r['md5'] == base['md5']}, "
                  f"rss {r['rss_mb'] / base['rss_mb']:.2f}x")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"spec": args.spec, "n": n, "build_seconds": round(build_s, 2), "rows": rows}, fh, indent=1)


if __name__ == "__main__":
    main()
