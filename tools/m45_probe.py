"""M45 -- the alphabet search built the geometry three times.

``m24_alpha.build`` encodes the model once per SH layout (bits / bytes / coef-major) to pick the smallest
compressed colour block. The geometry streams are identical in all three, so two of the three geometry encodes are
pure waste -- and geometry is 64 % of the container. This probe times the phase both ways on one host, in one process
per configuration, and checks that the cheap path produces the same streams.

    python -m tools.m45_probe --ply /mnt/m35cache/bicycle.ply
"""
import argparse
import hashlib
import json
import os
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
    ap.add_argument("--spec", default="gp6-6-6_c8_sh3")
    ap.add_argument("--json")
    args = ap.parse_args()

    import numpy as np
    import m4_bytes as M
    import m24_alpha as A
    import m19_codec as C
    import qfp_rd as Q

    spec = Q.parse_spec(args.spec)
    t0 = time.time()
    import m20_model
    splats = m20_model.load_model(args.ply)
    geo, sh = M._attribute_arrays(splats)
    deg = int(splats.sh_degree)
    order = M.morton_order(geo["means"])
    t_load = time.time() - t0

    #: the old path: one full encode per layout
    t0 = time.time()
    old = {lay: M._encode(spec, geo, sh, deg, None, order, sh_layout=lay) for lay in A.LAYOUTS}
    t_old = time.time() - t0
    res = A.choose({k: v[0] for k, v in old.items()}, [k for k in old["bits"][0] if "sh" in k], 12,
                   log=lambda *a: None)
    use = res["choice"].get("sh_dc", "bits")

    #: the new path: geometry once, colour per layout
    t0 = time.time()
    geo_only, geo_pp = M._encode(spec, geo, sh, deg, None, order, sh_layout="bits", parts=("geo",))
    t_geo = time.time() - t0
    t0 = time.time()
    new = {lay: M._encode(spec, geo, sh, deg, None, order, sh_layout=lay, parts=("sh",)) for lay in A.LAYOUTS}
    t_sh = time.time() - t0
    geo_streams = {k: v for k, v in old[use][0].items() if not k.startswith("sh_")}
    merged = dict(geo_only)
    merged.update(new[use][0])

    same = _digest(geo_streams) == _digest({k: v for k, v in geo_only.items()})
    sh_same = _digest({k: v for k, v in old[use][0].items() if k.startswith("sh_")}) == _digest(new[use][0])
    per_prim_old = old[use][1]
    per_prim_new = geo_pp + new[use][1]

    t0 = time.time()
    rec = A.build(splats, rank=16, bits_total=48, level=12, spec_name=args.spec, mode="auto",
                  log=lambda *a: None)
    t_build = time.time() - t0
    path = os.path.join("/workspace/res/m43", f"m45_{os.path.basename(args.ply).replace('.ply','')}.gs1")
    meta = dict(rec["meta"])
    meta["min_frame"] = int(C.MIN_FRAME)
    t1 = time.time()
    info = C.write_container(path, rec["streams"], meta, 12, jobs=4)
    t_write = time.time() - t1

    row = {"ply": os.path.basename(args.ply), "n": int(geo["means"].shape[0]),
           "load_s": round(t_load, 1),
           "old_encodes_s": round(t_old, 1), "geo_once_s": round(t_geo, 1), "sh_three_s": round(t_sh, 1),
           "new_phase_s": round(t_geo + t_sh, 1),
           "phase_ratio": round((t_geo + t_sh) / t_old, 3),
           "geo_streams_identical": bool(same), "sh_streams_identical": bool(sh_same),
           "layout_chosen": use, "per_prim_old": round(per_prim_old, 4), "per_prim_new": round(per_prim_new, 4),
           "build_s": round(t_build, 1), "write_s": round(t_write, 1), "bytes": info["bytes"]}
    print(json.dumps(row))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)


if __name__ == "__main__":
    main()
