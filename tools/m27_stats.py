"""Print source and decoded distributions side by side, per attribute (M27 diagnosis)."""

from __future__ import annotations

import sys

import numpy as np


def stats(name, x):
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    q = np.percentile(x, [1, 25, 50, 75, 99])
    print(f"  {name:<12} min={x.min():+.4f} p1={q[0]:+.4f} p25={q[1]:+.4f} p50={q[2]:+.4f} "
          f"p75={q[3]:+.4f} p99={q[4]:+.4f} max={x.max():+.4f}")


def main() -> int:
    ply, gs1 = sys.argv[1], sys.argv[2]
    import m19_codec as C
    import m20_model
    import m27_anchor as A

    s = m20_model.load_model(ply)
    n = int(s.means.shape[0])
    meta, streams = C.read_container(gs1)
    out = A.decode(meta, streams)
    order = A.group(np.asarray(s.means, dtype=np.float32), float(meta["voxel"]))[0]

    print("source (anchor order)")
    stats("opacity", np.asarray(s.opacities)[order])
    stats("dc", np.asarray(s.sh0)[order])
    stats("rest", np.asarray(s.shN)[order])
    print("decoded")
    stats("opacity", out["opacities"])
    stats("dc", out["sh_dc"])
    stats("rest", out["sh_rest"])
    print("stream sizes", {k: len(v) for k, v in sorted(streams.items())})
    return 0


if __name__ == "__main__":
    sys.exit(main())
