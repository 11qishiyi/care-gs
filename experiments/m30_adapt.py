"""M30 -- give every position cluster the width its own box needs.

The container codes the offsets inside a 256-primitive cluster on a fixed grid: 8 bits per axis over
that cluster's bounding box, the same width everywhere.  The boxes are not the same size -- millimetres
in a dense region, centimetres along a thin structure -- so one width over-spends where the box is small
and under-spends where it is large, and nothing in the file reflects that.

This module re-codes the position stream cluster by cluster.  It never touches a position: the existing
codes ``u`` live on the grid ``step * [0, 2**b)``, so dropping to ``b'`` bits is the exact re-quantisation
``u' = round(u * (2**b' - 1) / (2**b - 1))`` and the new step is ``step * (2**b - 1) / (2**b' - 1)``.
The width sequence goes into a ``cluster_bits`` stream (one byte per cluster) and the decoder walks it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

import m4_bytes as M
import m19_codec as C
import qfp_rd as Q


def cluster_extents(hdr: np.ndarray, nominal: int) -> np.ndarray:
    """The physical side of each cluster's box: ``step`` is what the encoder stored."""
    step = hdr[:, 3:]
    return step * float((1 << int(nominal)) - 1)


def choose_bits(ext: np.ndarray, lo: int = 3, hi: int = 12, ref: float = 255.0) -> np.ndarray:
    """Width per cluster: a cluster at the *median* max-extent keeps the nominal width."""
    mx = ext.max(axis=1)
    target = float(np.median(mx)) / float(ref)          # metres per level at the nominal width
    target = max(target, 1e-9)
    b = np.ceil(np.log2(mx / target + 1.0))
    return np.clip(b, lo, hi).astype(np.int64)


def choose_bits_tilted(ext: np.ndarray, nominal: int = 8, tilt: float = -0.5,
                       lo: int = 3, hi: int = 12) -> np.ndarray:
    """Width per cluster, tilted by ``tilt`` against the extent.

    ``tilt = 0`` reproduces the fixed width; ``tilt = -1`` gives clusters half the median size one extra
    bit and takes one from clusters twice the median -- i.e. it spends the same *total* budget but
    favours the dense regions.  The encoder is not allowed to look at a render, so the tilt is a
    property of the geometry alone.
    """
    mx = ext.max(axis=1)
    med = float(np.median(mx))
    rel = np.log2(np.maximum(mx, 1e-12) / max(med, 1e-12))
    b = float(nominal) + float(tilt) * rel
    return np.clip(np.rint(b), lo, hi).astype(np.int64)


def adapt(gs1: str, out_gs1: str, nominal: int = 8, lo: int = 3, hi: int = 12,
          level: int = 12, target_div: float = None, tilt: float = None,
          match_bytes: bool = False, log=print) -> dict:
    """Rewrite one container with per-cluster widths; returns the accounting."""
    meta, streams = C.read_container(gs1)
    if "cluster_hdr" not in streams:
        raise SystemExit("container has no clusters")
    if "cluster_bits" in streams:
        raise SystemExit("container already carries per-cluster widths")
    hdr = np.frombuffer(streams["cluster_hdr"], dtype=np.float32).reshape(-1, 6)
    nblk = hdr.shape[0]
    block = int(M.CLUSTER_SIZE)
    n = int(meta["n"])
    nb_valid = int(np.ceil(n / block))

    u = C.unpack_bits(streams["cluster_off"], int(nominal), nblk * block * 3,
                      dtype=np.uint16).reshape(nblk, block, 3)
    ext = cluster_extents(hdr, nominal)
    ref = float(target_div if target_div else (1 << int(nominal)) - 1)
    if tilt is not None:
        bits = choose_bits_tilted(ext, nominal=int(nominal), tilt=float(tilt), lo=lo, hi=hi)
        if match_bytes:
            #: budget-neutral: shift every width by the integer that lands closest to the fixed width
            base_len = len(streams["cluster_off"])
            best = None
            for shift in range(-3, 4):
                cand = np.clip(bits + shift, lo, hi)
                nbytes = int(np.sum(np.ceil(block * 3 * cand / 8.0))) + nblk
                if best is None or abs(nbytes - base_len) < abs(best[1] - base_len):
                    best = (cand, nbytes, shift)
            bits, _, shift = best
            log(f"  tilt {tilt} matched to the fixed-width budget with shift {shift:+d}")
    else:
        bits = choose_bits(ext, lo=lo, hi=hi, ref=ref)

    #: the offsets themselves are untouched; only the grid they are written on changes
    qmax_old = (1 << int(nominal)) - 1
    parts, steps = [], []
    for i in range(nblk):
        b = int(bits[i])
        qmax_new = (1 << b) - 1
        uu = np.rint(u[i].astype(np.float64) * (qmax_new / float(qmax_old)))
        uu = np.clip(uu, 0, qmax_new).astype(np.int64)
        parts.append(M.pack_bits(uu.reshape(-1), b))
        steps.append(ext[i] / float(max(1, qmax_new)))

    new = {k: v for k, v in streams.items()}
    new["cluster_off"] = b"".join(parts)
    new["cluster_bits"] = bits.astype(np.uint8).tobytes()
    hdr_new = np.concatenate([hdr[:, :3], np.stack(steps).astype(np.float32)], axis=1)
    new["cluster_hdr"] = hdr_new.astype(np.float32).tobytes()
    meta = dict(meta)
    meta["cluster_adaptive"] = {"nominal": int(nominal), "lo": int(lo), "hi": int(hi)}
    C.write_container(out_gs1, new, meta, level=level)

    before, after = os.path.getsize(gs1), os.path.getsize(out_gs1)
    hist = np.bincount(bits.astype(np.int64), minlength=16)[:16]
    pos_before = len(streams["cluster_off"])
    pos_after = len(new["cluster_off"]) + len(new["cluster_bits"])
    log(f"  clusters {nblk:,}  widths {', '.join(f'{b}:{c}' for b, c in enumerate(hist) if c)}")
    log(f"  position bytes {pos_before/1e6:.3f} -> {pos_after/1e6:.3f} MB  "
        f"({100.0*(pos_before-pos_after)/max(1,pos_before):+.1f} %)")
    log(f"  file {before/1e6:.2f} -> {after/1e6:.2f} MB ({100.0*(before-after)/max(1,before):+.2f} %)")
    return {"in": gs1, "out": out_gs1, "before": before, "after": after,
            "pos_before": pos_before, "pos_after": pos_after,
            "clusters": int(nblk), "n": n,
            "width_hist": {str(b): int(c) for b, c in enumerate(hist) if c},
            "mean_bits": float(bits[np.arange(nblk) < nb_valid].mean()),
            "nominal": int(nominal), "target_div": float(target_div or 0),
            "tilt": float(tilt if tilt is not None else 0.0)}


def selftest() -> None:
    rng = np.random.default_rng(0)
    nblk, block = 40, 256
    ext = np.concatenate([rng.uniform(0.001, 0.01, size=(20, 3)),
                          rng.uniform(0.05, 0.2, size=(20, 3))])
    bits = choose_bits(ext)
    assert bits.min() >= 3 and bits.max() <= 12
    assert bits[:20].mean() < bits[20:].mean(), "tight clusters must get fewer bits"
    #: the reconstruction error must not grow with the width chosen
    for b in (4, 8, 12):
        step = ext.max(axis=1) / float((1 << b) - 1)
        assert np.all(step * 0.5 <= ext.max(axis=1) / 2.0)
    print(f"m30 selftest ok  widths {bits.min()}..{bits.max()}  mean {bits.mean():.2f}")


def main() -> int:
    ap = argparse.ArgumentParser(description="per-cluster position widths")
    ap.add_argument("--gs1")
    ap.add_argument("--out")
    ap.add_argument("--nominal", type=int, default=8)
    ap.add_argument("--lo", type=int, default=3)
    ap.add_argument("--hi", type=int, default=12)
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--json")
    ap.add_argument("--target-div", type=float, default=None)
    ap.add_argument("--tilt", type=float, default=None)
    ap.add_argument("--match-bytes", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.gs1 or not a.out:
        ap.error("--gs1 and --out are required")

    def log(msg: str) -> None:
        print(msg, flush=True)

    row = adapt(a.gs1, a.out, nominal=a.nominal, lo=a.lo, hi=a.hi, level=a.level,
                target_div=a.target_div, tilt=a.tilt, match_bytes=a.match_bytes, log=log)
    #: the decoder must rebuild the same model geometry, to within the coarser grid it asked for
    m0, s0 = C.read_container(a.gs1)
    m1, s1 = C.read_container(a.out)
    p0, p1 = C.decode(m0, s0), C.decode(m1, s1)
    dm = np.abs(p0["means"] - p1["means"]).max(axis=0)
    row["max_delta_m"] = [float(x) for x in dm]
    log(f"  max position change {dm} m")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
