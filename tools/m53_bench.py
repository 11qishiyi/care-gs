"""Does the anchor prototype survive a real model's size on CPU?

The node round is 40 minutes of rented time; a prototype that needs 40 GB to assign VQ codes to 1.5 M primitives
would waste it. This bench runs `m53_anchor.encode_geometry` on a synthetic model of the published bicycle's
primitive count, reports wall clock and peak RSS per stage, and is the check that has to pass before the prototype
is trusted with a rented GPU.

    python3 tools/m53_bench.py                    # 1.5 M primitives, VQ-64
    python3 tools/m53_bench.py --n 6100000 --vq 256
"""
from __future__ import annotations

import argparse
import sys
try:
    import resource  # POSIX only; the bench also runs on Windows, where RSS is reported as 0
except ImportError:  # pragma: no cover
    resource = None
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

import m53_anchor as A  # noqa: E402


def synth(n: int, seed: int = 0):
    """A clustered model with anchor-dependent attributes — closer to a real scene than i.i.d. noise."""
    rng = np.random.default_rng(seed)
    n_anchor = max(1, n // 12)
    centres = rng.normal(size=(n_anchor, 3)) * 4.0
    which = rng.integers(0, n_anchor, n)
    means = centres[which] + rng.normal(size=(n, 3)) * 0.05
    quats = rng.normal(size=(n, 4))
    quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    W = rng.normal(size=(3, 3)) * 0.05
    log_scales = (means - centres[which]) @ W + rng.normal(size=(n, 3)) * 0.01
    logit_opac = means[:, 0] * 0.2 + rng.normal(size=n) * 0.05
    return means, quats, log_scales, logit_opac


def _rss_gb() -> float:
    if resource is None:
        return 0.0
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6  # kB -> GB


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=1_532_988)
    ap.add_argument("--vq", type=int, default=64)
    ap.add_argument("--k", type=float, default=3.0)
    ap.add_argument("--offbits", type=int, default=4)
    a = ap.parse_args()

    t0 = time.time()
    means, quats, scales, opac = synth(a.n)
    print(f"synthetic model: n={a.n:,}  built in {time.time() - t0:.1f}s  rss={_rss_gb():.2f} GB")

    for vqk in (0, a.vq):
        t = time.time()
        try:
            out = A.encode_geometry(means, quats, scales, opac, k=a.k, offbits=a.offbits,
                                    attr_bits=6, mode="p1", vq_k=vqk)
        except MemoryError as exc:  # pragma: no cover - the failure this bench exists to catch
            print(f"  vq={vqk}: MemoryError after {time.time() - t:.1f}s -- {exc}")
            return 1
        dt = time.time() - t
        print(f"  vq={vqk or '-':>3}: {dt:6.1f}s  geometry {out['geometry_b_per_prim']:.2f} B/prim "
              f"(pos {out['pos_stream_b_per_prim']:.2f}, attr {out['attr_stream_b_per_prim']:.2f})  "
              f"anchors {out['anchors']:,}  rss={_rss_gb():.2f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
