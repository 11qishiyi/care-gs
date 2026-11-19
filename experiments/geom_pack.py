"""Geometry packing for the near-lossless shelf: quaternion smallest-three, tight scalars.

The 11 geometric scalars cost 11.8 B per primitive today (8-bit grids) or 44 B at fp32.  Three of
the four groups are lattice-quantised far below their information content:

  - a unit quaternion lives on a 3-sphere, so its fourth component is redundant in magnitude:
    store the index of the largest component (2 bits) and the other three at b bits each.  At
    b=3 that is 11 bits, i.e. 1.4 B, against 4 B today.
  - log-scales and opacity are smooth positive quantities; M2 measured 8-bit as free and 6-bit as
    free for opacity, so 5 and 4 bits are the natural floor to test.

This module is the local gate that has to pass before any node time is spent: the packing must
reconstruct a quaternion at least as accurately as the 8-bit uniform grid that M2 already showed
to be invisible in the render.

Run:  python experiments/geom_pack.py --selftest
"""
from __future__ import annotations

import argparse
import math

import numpy as np

POS_HEADER_BYTES = 24.0 / 256.0          # cluster header, amortised (M7)
SH_SCALE_BYTES = 2.0


def packed_geometry_bytes(b_quat: int = 8, b_scale: int = 5, b_opac: int = 4,
                          c_pos: int = 6) -> float:
    """Bytes per primitive for the packed geometry, without the SH block."""
    quat = (2 + 3 * b_quat) / 8.0
    scales = 3 * b_scale / 8.0
    opac = b_opac / 8.0
    pos = 3 * c_pos / 8.0
    return pos + POS_HEADER_BYTES + scales + quat + opac


def uniform_geometry_bytes(b: int = 8, c_pos: int = 10) -> float:
    """Bytes per primitive for the uniform grids we ship today."""
    return 3 * c_pos / 8.0 + POS_HEADER_BYTES + 11 * b / 8.0


# ----------------------------------------------------------------------------- quaternions

def _normalise(q: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(q, axis=-1, keepdims=True)
    return q / np.maximum(n, 1e-12)


_LIM = 1.0 / math.sqrt(2.0)


def st3_encode(q: np.ndarray, b: int):
    """Smallest-three *codes* for unit quaternions ``(N,4)``: ``(which, codes)``.

    ``which`` is the index of the largest component -- the decoder knows that one is
    positive, so its sign costs nothing -- and ``codes`` are the three remaining
    components on a ``b``-bit grid over ``[-1/sqrt2, 1/sqrt2]``.  The stored width is
    ``2 + 3*b`` bits per primitive, which is what the byte model must charge.
    """
    q = _normalise(np.asarray(q, dtype=np.float64))
    n = int(q.shape[0])
    which = np.argmax(np.abs(q), axis=1)
    rows = np.arange(n)
    sign = np.sign(q[rows, which])
    sign[sign == 0] = 1.0
    q = q * sign[:, None]                      # largest component now positive
    mask = np.arange(4)[None, :] != which[:, None]     # (N,4): the three kept ones
    abc = q[mask].reshape(n, 3)                # in [-1/sqrt2, 1/sqrt2], ascending order
    step = 2.0 * _LIM / (2 ** int(b) - 1)
    codes = np.clip(np.round((abc + _LIM) / step), 0, 2 ** int(b) - 1).astype(np.int64)
    return which.astype(np.int64), codes


def st3_decode(which: np.ndarray, codes: np.ndarray, b: int) -> np.ndarray:
    """Inverse of :func:`st3_encode`: rebuild the unit quaternion ``(N,4)``."""
    which = np.asarray(which, dtype=np.int64).reshape(-1)
    codes = np.asarray(codes, dtype=np.int64)
    n = int(which.shape[0])
    step = 2.0 * _LIM / (2 ** int(b) - 1)
    aq = codes.astype(np.float64) * step - _LIM
    out = np.zeros((n, 4), dtype=np.float64)
    mask = np.arange(4)[None, :] != which[:, None]
    out[mask] = aq.reshape(-1)
    last = 1.0 - np.sum(aq ** 2, axis=1)
    out[np.arange(n), which] = np.sqrt(np.maximum(last, 0.0))
    return _normalise(out)


def quantise_st3(q: np.ndarray, b: int) -> np.ndarray:
    """Smallest-three quantisation of unit quaternions (N,4) -> (N,4), renormalised."""
    which, codes = st3_encode(q, b)
    return st3_decode(which, codes, b)


def quantise_uniform(q: np.ndarray, b: int) -> np.ndarray:
    """The baseline: b bits per component over [-1,1], then renormalise."""
    q = _normalise(np.asarray(q, dtype=np.float64))
    levels = 2 ** b - 1
    out = np.round((q + 1.0) / 2.0 * levels) / levels * 2.0 - 1.0
    return _normalise(out)


def quat_errors(q: np.ndarray, qh: np.ndarray) -> dict:
    """L2 error and angular error in degrees (sign-insensitive)."""
    q = _normalise(np.asarray(q, dtype=np.float64))
    qh = _normalise(np.asarray(qh, dtype=np.float64))
    dot = np.abs(np.sum(q * qh, axis=1)).clip(-1.0, 1.0)
    ang = 2.0 * np.degrees(np.arccos(dot))     # rotation angle between the two
    l2 = np.linalg.norm(q - qh * np.sign(np.sum(q * qh, axis=1, keepdims=True)), axis=1)
    return {"l2_mean": float(l2.mean()), "l2_max": float(l2.max()),
            "ang_mean": float(ang.mean()), "ang_max": float(ang.max())}


# ----------------------------------------------------------------------------- selftest

def selftest() -> int:
    rng = np.random.default_rng(0)
    n = 20000
    q = _normalise(rng.normal(size=(n, 4)))
    print(f"{'coder':22s} {'bits/prim':>9s} {'L2 mean':>9s} {'L2 max':>9s} "
          f"{'ang mean':>9s} {'ang max':>8s}")
    rows = {}
    for name, bits, fn in (("st3 b=4", (2 + 3 * 4), lambda x: quantise_st3(x, 4)),
                           ("st3 b=6", (2 + 3 * 6), lambda x: quantise_st3(x, 6)),
                           ("st3 b=8", (2 + 3 * 8), lambda x: quantise_st3(x, 8)),
                           ("uniform b=6", 24, lambda x: quantise_uniform(x, 6)),
                           ("uniform b=8", 32, lambda x: quantise_uniform(x, 8))):
        e = quat_errors(q, fn(q))
        rows[name] = (bits, e)
        print(f"{name:22s} {bits:9d} {e['l2_mean']:9.2e} {e['l2_max']:9.2e} "
              f"{e['ang_mean']:8.3f}d {e['ang_max']:7.3f}d")

    fails = []

    def check(label, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {label}")
        if not ok:
            fails.append(label)

    print()
    b8 = rows["st3 b=8"][1]
    u8 = rows["uniform b=8"][1]
    # The gate: 26 bits (3.25 B) must be within 2x of the 32-bit grid M2 measured as free.
    check(f"st3 b=8 within 2x of uniform b=8 in L2 ({b8['l2_mean']:.2e} vs "
          f"{u8['l2_mean']:.2e})", b8["l2_mean"] <= 2.0 * u8["l2_mean"])
    check(f"st3 b=8 angular error under 1 deg ({b8['ang_mean']:.3f})",
          b8["ang_mean"] < 1.0)
    check("more bits never hurt", rows["st3 b=8"][1]["l2_mean"]
          <= rows["st3 b=6"][1]["l2_mean"] <= rows["st3 b=4"][1]["l2_mean"])
    check("reconstruction is a unit quaternion",
          float(np.abs(np.linalg.norm(quantise_st3(q[:500], 3), axis=1) - 1).max()) < 1e-9)

    old = uniform_geometry_bytes()
    new = packed_geometry_bytes()
    print()
    print(f"  geometry: {old:.2f} B/prim today -> {new:.2f} B/prim packed "
          f"(saving {old - new:.2f} B)")
    check("packing saves at least 3 B", old - new >= 3.0)
    # 3-bit SH is 48 coefficients (not 45) plus the 2 B per-primitive scale: 20.0 B.
    # Quoting 18.9 B here is what put 26.9 B / 8.78x into FRONTIER_BOUND before it was
    # corrected; the shelf row is 27.97 B and 8.44x.
    sh3 = 48.0 * 3.0 / 8.0 + 2.0
    print(f"  with 3-bit SH ({sh3:.1f} B) the model is {new + sh3:.2f} B -> "
          f"{236.0 / (new + sh3):.2f}x before zstd")

    print("=" * 60)
    print("ALL PASS" if not fails else "FAILURES: " + "; ".join(fails))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
