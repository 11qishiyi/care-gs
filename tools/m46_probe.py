"""M46 -- the three colour alphabets are independent passes; price the pool.

    python -m tools.m46_probe --ply /mnt/m35cache/bicycle.ply --jobs 1,3

Sequential and pooled on one host in one session. Reports the phase time, the peak RSS and the container md5 for each
worker count, plus the digest of the streams, so the pooled run can be shown to be the same run.
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


def _digest(streams):
    h = hashlib.md5()
    for k in sorted(streams):
        h.update(k.encode())
        h.update(streams[k])
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--jobs", default="1,3")
    ap.add_argument("--spec", default="gp6-6-6_c8_sh3")
    ap.add_argument("--out", default="/workspace/res/m46")
    ap.add_argument("--json")
    args = ap.parse_args()

    import m4_bytes as M
    import m20_model
    import m24_alpha as A
    import qfp_rd as Q

    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    splats = m20_model.load_model(args.ply)
    geo, sh = M._attribute_arrays(splats)
    deg = int(splats.sh_degree)
    order = M.morton_order(geo["means"])
    spec = Q.parse_spec(args.spec)
    t_load = time.time() - t0

    rows = []
    for jobs in [int(x) for x in args.jobs.split(",")]:
        t0 = time.time()
        geo_streams, _ = M._encode(spec, geo, sh, deg, None, order, sh_layout=A.LAYOUTS[0], parts=("geo",))
        t_geo = time.time() - t0

        def colour(lay):
            return M._encode(spec, geo, sh, deg, None, order, sh_layout=lay, parts=("sh",))[0]

        t0 = time.time()
        if jobs > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(jobs, len(A.LAYOUTS))) as pool:
                cand = dict(zip(A.LAYOUTS, pool.map(colour, A.LAYOUTS)))
        else:
            cand = {lay: colour(lay) for lay in A.LAYOUTS}
        t_colour = time.time() - t0

        res = A.choose(cand, [k for k in cand[A.LAYOUTS[0]] if "sh" in k], 12, log=lambda *a: None)
        use = res["choice"].get("sh_dc", A.LAYOUTS[0])
        merged = dict(geo_streams)
        merged.update(cand[use])
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
        rows.append({"ply": os.path.basename(args.ply), "jobs": jobs, "load_s": round(t_load, 1),
                     "geo_s": round(t_geo, 1), "colour_s": round(t_colour, 1),
                     "phase_s": round(t_geo + t_colour, 1), "layout": use,
                     "streams_md5": _digest(merged), "peak_rss_gb": round(peak, 2)})
        print(json.dumps(rows[-1]), flush=True)
        del cand, merged

    if len(rows) > 1:
        base = rows[0]["phase_s"]
        for row in rows[1:]:
            row["phase_ratio_vs_seq"] = round(row["phase_s"] / base, 3)
            row["same_streams"] = row["streams_md5"] == rows[0]["streams_md5"]
            print(f"VERDICT jobs={row['jobs']}: phase {row['phase_ratio_vs_seq']:.3f}x  "
                  f"peak +{row['peak_rss_gb'] - rows[0]['peak_rss_gb']:+.2f} GB  "
                  f"same_streams={row['same_streams']}", flush=True)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    main()
