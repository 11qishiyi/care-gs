"""Which reconstruction level should a truncated SH plane use?  Measured, not argued.

Compares three rules on the same model, at each truncation step:
  zero      -- missing bits mean "no directional colour" (value 0)
  midpoint  -- missing low bits are the middle of their bin
  measured  -- encoder stores the scale-weighted conditional mean of the code per (bin, column)

The winner is whatever minimises the error against the file as shipped, because that is what a
renderer sees.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m19_codec as C  # noqa: E402


def _model(n=4000, seed=0, sh_sd=0.1):
    rng = np.random.default_rng(seed)

    class S:
        pass

    s = S()
    s.sh_degree = 3
    s.means = torch.tensor(rng.normal(0, 1.0, (n, 3)), dtype=torch.float32)
    s.scales = torch.tensor(np.exp(rng.normal(-2.0, 0.4, (n, 3))), dtype=torch.float32)
    q = rng.normal(size=(n, 4))
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    s.quats = torch.tensor(q, dtype=torch.float32)
    s.opacities = torch.tensor(rng.uniform(0.02, 0.98, (n,)), dtype=torch.float32)
    s.sh0 = torch.tensor(rng.normal(0, 0.5, (n, 3)), dtype=torch.float32)
    s.shN = torch.tensor(rng.normal(0, sh_sd, (n, 15, 3)), dtype=torch.float32)
    return s


def value_from_codes(codes, scale, k, mode, lut=None):
    """``codes`` (n, ncols) with missing planes already zero; ``scale`` (n, 1)."""
    c = codes.astype(np.float64).copy()
    ncols = c.shape[1]
    if k >= 3:
        est = c
    elif mode == "zero":
        est = np.full_like(c, 4.0)
    elif mode == "midpoint":
        est = c + (2 ** (3 - k) - 1) / 2.0
    else:
        nb = 1 << k
        off = {0: 0, 1: 1, 2: 3}[k]
        tab = lut[off:off + nb]
        h = (c.astype(np.int64) >> (3 - k))
        est = tab[h, np.arange(ncols)[None, :]]
    return (est - 4.0) * scale


def main() -> int:
    for sh_sd in (0.1, 0.01, 0.3):
        s = _model(sh_sd=sh_sd)
        import tempfile
        td = tempfile.mkdtemp()
        prog = os.path.join(td, "p.gs1")
        C.encode_model(s, "c10_o8_sh3", level=12, path=prog, progressive=True)
        meta, streams = C.read_container(prog)
        full = C.decode(meta, streams)
        n = int(meta["n"])
        deg_out = int(meta["deg_out"])
        ncols = 3 * deg_out * (deg_out + 2)
        lvl = C.unpack_bits(streams["sh_scale"], 8, n * 2).reshape(n, 2).astype(np.float64)
        hdr = np.frombuffer(streams["sh_hdr"], dtype=np.float32)
        scale = (lvl[:, 1:2] / 255.0) * float(hdr[1])
        codes = np.zeros((n, ncols), dtype=np.uint8)
        for i, name in enumerate(C.SH_PLANES):
            bit = len(C.SH_PLANES) - 1 - i
            codes |= np.frombuffer(streams[name], np.uint8).reshape(n, ncols) << bit
        lut = np.frombuffer(streams["sh_lut"], dtype=np.float32).reshape(-1, ncols)
        truth = full["sh_rest"].reshape(n, -1)
        print(f"sh_sd={sh_sd}  |truth| mean {np.abs(truth).mean():.4f}")
        for k in (0, 1, 2):
            keep = ((0xFF << (3 - k)) & 0xFF) if k else 0
            masked = codes & np.uint8(keep) if k else np.zeros_like(codes)
            line = f"  k={k}"
            for mode in ("zero", "midpoint", "measured"):
                v = value_from_codes(masked, scale, k, mode, lut)
                line += f"   {mode:8s} L1 {np.abs(v - truth).mean():.5f}"
            print(line, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
