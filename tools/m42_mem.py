"""M42 -- stage by stage, what the encoder's memory is spent on.

M41 measured 18.8 GB peak RSS for a 76.6 MB container. This probe runs the shipping build in one process and
prints current and peak RSS after every stage, so the round has a table before it has an opinion.

    python -m tools.m42_mem --ply /mnt/m35cache/bicycle.ply --json /workspace/res/m42/mem.json

``cur`` is resident memory now, ``peak`` is the high-water mark so far; ``delta`` is what the stage added.
"""
import argparse
import gc
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "experiments"), os.path.join(ROOT, "research", "code")):
    if p not in sys.path:
        sys.path.insert(0, p)


def _rss():
    """(current, peak) resident set in MB, from /proc -- Linux only, which is where this runs."""
    with open("/proc/self/status", encoding="ascii", errors="replace") as fh:
        cur = peak = 0.0
        for line in fh:
            if line.startswith("VmRSS:"):
                cur = float(line.split()[1]) / 1024.0
            elif line.startswith("VmHWM:"):
                peak = float(line.split()[1]) / 1024.0
    return cur, peak


class Probe:
    def __init__(self):
        self.rows = []
        self.t0 = time.time()

    def mark(self, stage, note=""):
        gc.collect()
        cur, peak = _rss()
        self.rows.append({"stage": stage, "cur_mb": round(cur, 1), "peak_mb": round(peak, 1),
                          "t": round(time.time() - self.t0, 1), "note": note})
        print(f"{stage:28s} cur {cur:9.1f} MB  peak {peak:9.1f} MB  t {time.time() - self.t0:6.1f} s  {note}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", default="/mnt/m35cache/bicycle.ply")
    ap.add_argument("--spec", default="gp6-6-6_c8_sh3")
    ap.add_argument("--json")
    args = ap.parse_args()

    import numpy as np

    import m4_bytes as M
    import m20_model
    import m22_basis as B
    import m24_alpha as A
    import qfp_rd as Q

    pr = Probe()
    pr.mark("start")
    splats = m20_model.load_model(args.ply)
    pr.mark("load_model", f"n={int(splats.means.shape[0]):,}")
    geo, sh = M._attribute_arrays(splats)
    pr.mark("attribute_arrays", f"rest={sh['rest'].nbytes/1e9:.2f} GB float64")
    spec = Q.parse_spec(args.spec)
    deg = int(splats.sh_degree)
    n = int(geo["means"].shape[0])
    order = M.morton_order(geo["means"])
    pr.mark("morton_order")

    cand = {}
    for lay in A.LAYOUTS:
        cand[lay] = M._encode(spec, geo, sh, deg, None, order, sh_layout=lay)[0]
        pr.mark(f"encode_layout[{lay}]", f"{sum(len(v) for v in cand[lay].values())/1e6:.0f} MB streams")
    res = A.choose(cand, [k for k in cand["bits"] if "sh" in k], 12, log=lambda *a: None)
    pr.mark("alphabet_choice", str(res["choice"]))
    use = res["choice"].get("sh_dc", "bits")

    rest = B.rest_matrix(sh)[np.asarray(order)]
    pr.mark("rest_matrix", f"{rest.nbytes/1e9:.2f} GB")
    f = B.fit(rest, 16)
    pr.mark("basis_fit", f"basis={f['basis'].shape}")
    q = B.quantise_alloc(f["coef"], f["comp"], 48)
    code_bytes = sum(np.asarray(c).nbytes for c in q["codes"]) if isinstance(q["codes"], (list, tuple)) \
        else q["codes"].nbytes
    pr.mark("quantise_alloc", f"codes {code_bytes/1e6:.1f} MB")
    streams = {k: v for k, v in cand[use].items() if "sh_rest" not in k}
    streams["sh_coef"] = B.pack_codes(q["codes"], q["bits"], "bits")
    pr.mark("pack_codes")

    import m19_codec as C

    meta = {"spec": args.spec, "n": n, "sh_degree": deg, "sh_layout": use, "deg_out": deg,
            "sh_basis_rank": 16, "sh_coef_bits_total": int(q["bits_total"]),
            "sh_coef_layout": "bits", "sh_rest_cols": int(rest.shape[1]),
            "sh_energy": f["energy"], "sh_bits_per_component": [int(x) for x in q["bits"]],
            "alphabet_mode": "auto", "alphabet_choice": res["choice"], "sh_scale_levels": 1,
            "min_frame": int(C.MIN_FRAME)}
    out = os.environ.get("M42_OUT", "/workspace/res/m42/probe.gs1")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    C.write_container(out, streams, meta, 12, jobs=4)
    pr.mark("write_container", f"{os.path.getsize(out):,} B")

    del cand, rest, q, streams
    pr.mark("after_free")
    if args.json:
        os.makedirs(os.path.dirname(args.json), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"ply": args.ply, "spec": args.spec, "rows": pr.rows}, fh, indent=1)


if __name__ == "__main__":
    main()
