"""Build one M38 container: the M35 shipping configuration with the four attribute streams VQ'd.

    python tools/m38_build.py --ply /workspace/data/m20/bicycle.ply --k 65536 --out /workspace/res/m38/k65536.gs1

Reports the byte ledger per stream (so the codebook's cost is visible next to what it replaced) and the
distortion of the codebook itself, in the units the attributes live in.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--spec", default="gp6-6-6_c8_sh3")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--bits", type=int, default=48)
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--iters", type=int, default=15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    import m19_codec as C
    import m20_model
    import m38_vq as V

    t0 = time.time()
    splash = m20_model.load_model(a.ply)
    n = int(splash.means.shape[0])
    print(f"model: {n} primitives ({time.time()-t0:.0f}s)", flush=True)

    t1 = time.time()
    rec = V.build(splash, a.k, spec_name=a.spec, rank=a.rank, bits_total=a.bits, level=a.level,
                  iters=a.iters, seed=a.seed, log=print)
    print(f"encode: {time.time()-t1:.0f}s", flush=True)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    meta_sizes = C.write_container(a.out, rec["streams"], rec["meta"], a.level)
    size = os.path.getsize(a.out)

    sizes = {e["name"]: {"raw": int(e["raw"]), "comp": int(e["comp"])}
             for e in meta_sizes["streams"]}
    #: the scalar cost of what the codebook replaced, from the same build (streams popped above)
    ref = json.load(open(a.json.replace(".json", "_scalar.json"))) if os.path.exists(
        a.json.replace(".json", "_scalar.json")) else {}

    x = np.asarray(rec["x"], np.float32)
    recon = np.asarray(rec["recon"], np.float32)
    d = recon - x
    report = {
        "k": a.k, "n": n, "bytes": size, "bytes_per_prim": size / n,
        "bits_index": int(rec["meta"]["geo_vq_bits"]),
        "codebook_bytes": int(rec["meta"]["geo_vq_cb_bytes"]),
        "streams": sizes,
        "distortion": {
            "mse_total": float((d ** 2).mean()),
            "rel_rmse": float(np.sqrt((d ** 2).mean()) / (np.sqrt((x ** 2).mean()) + 1e-12)),
            "per_dim_mse": {name: float((d[:, i] ** 2).mean()) for i, name in enumerate(V.DIMS)},
        },
        "scalar_reference": ref,
        "spec": a.spec, "rank": a.rank, "bits": a.bits,
    }
    idx = np.asarray(rec["idx"])
    counts = np.bincount(idx, minlength=a.k)
    report["index_stats"] = {"used": int((counts > 0).sum()), "max_count": int(counts.max())}
    print(f"file {size} B = {size/n:.3f} B/prim; codebook {report['codebook_bytes']} B; "
          f"indices used {report['index_stats']['used']}/{a.k}", flush=True)
    for name, v in sizes.items():
        print(f"  {name:18s} raw {v['raw']:>12,}  comp {v['comp']:>12,}")
    if a.json:
        json.dump(report, open(a.json, "w"), indent=1)
        print("wrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
