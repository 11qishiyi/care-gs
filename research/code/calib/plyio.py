"""Read INRIA-format 3DGS PLY files without relying on gsplat's exporter module.

The released 3DGS checkpoints store **log** scales and **logit** opacities and put
the higher-order SH coefficients in channel-major order (all R, then all G, then
all B).  We convert to the "actual value" convention used by ``Splats``.
"""
from __future__ import annotations

import numpy as np


def load_inria_ply(path: str) -> dict:
    from plyfile import PlyData

    ply = PlyData.read(str(path))
    v = ply.elements[0]
    names = {p.name for p in v.properties}
    n = len(v)

    means = np.stack([np.asarray(v["x"]), np.asarray(v["y"]), np.asarray(v["z"])], 1).astype(np.float32)
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1)).astype(np.float32)
    opac = (1.0 / (1.0 + np.exp(-np.asarray(v["opacity"])))).astype(np.float32)
    quats = np.stack([np.asarray(v[f"rot_{i}"]) for i in range(4)], 1).astype(np.float32)
    quats /= np.linalg.norm(quats, axis=1, keepdims=True).clip(1e-12)
    sh0 = np.stack([np.asarray(v[f"f_dc_{i}"]) for i in range(3)], 1).astype(np.float32)[:, None, :]

    rest = [f"f_rest_{i}" for i in range(64) if f"f_rest_{i}" in names]
    if rest:
        fr = np.stack([np.asarray(v[k]) for k in rest], 1).astype(np.float32)   # (N, 3*(K-1))
        k_minus_1 = fr.shape[1] // 3
        # channel-major -> basis-major
        shN = fr.reshape(n, 3, k_minus_1).transpose(0, 2, 1).copy()             # (N, K-1, 3)
    else:
        shN = np.zeros((n, 0, 3), dtype=np.float32)
    return dict(means=means, scales=scales, opacities=opac, quats=quats, sh0=sh0, shN=shN)


def save_inria_ply(path: str, means, scales, quats, opacities, sh0, shN=None) -> None:
    """Write an INRIA-format 3DGS PLY (the layout ``load_inria_ply`` reads back).

    ``scales`` are the actual (already exponentiated) scales and ``opacities`` the actual
    (already sigmoid'ed) opacities; they are stored in log / logit form, as the reference
    implementation does.
    """
    import numpy as np
    from plyfile import PlyData, PlyElement

    means = np.asarray(means, np.float32)
    scales = np.log(np.clip(np.asarray(scales, np.float32), 1e-12, None))
    opac = np.asarray(opacities, np.float32).reshape(-1, 1)
    opac = np.log(np.clip(opac, 1e-6, 1 - 1e-6) / (1 - np.clip(opac, 1e-6, 1 - 1e-6)))
    sh0 = np.asarray(sh0, np.float32).reshape(len(means), 3)
    quats = np.asarray(quats, np.float32)

    fields = [("x", "f4"), ("y", "f4"), ("z", "f4"), ("nx", "f4"), ("ny", "f4"), ("nz", "f4")]
    fields += [(f"f_dc_{i}", "f4") for i in range(3)]
    n_rest = 0 if shN is None else np.asarray(shN).shape[1]
    fields += [(f"f_rest_{i}", "f4") for i in range(n_rest * 3)]
    fields += [("opacity", "f4")]
    fields += [(f"scale_{i}", "f4") for i in range(3)]
    fields += [(f"rot_{i}", "f4") for i in range(4)]

    arr = np.zeros(len(means), dtype=fields)
    arr["x"], arr["y"], arr["z"] = means[:, 0], means[:, 1], means[:, 2]
    for i in range(3):
        arr[f"f_dc_{i}"] = sh0[:, i]
    if n_rest:
        rest = np.asarray(shN, np.float32).transpose(0, 2, 1).reshape(len(means), -1)
        for i in range(rest.shape[1]):
            arr[f"f_rest_{i}"] = rest[:, i]
    arr["opacity"] = opac[:, 0]
    for i in range(3):
        arr[f"scale_{i}"] = scales[:, i]
    for i in range(4):
        arr[f"rot_{i}"] = quats[:, i]

    el = PlyElement.describe(arr, "vertex")
    PlyData([el], text=False).write(path)
