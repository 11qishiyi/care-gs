"""Load an INRIA PLY into the little object ``m4_bytes._attribute_arrays`` expects.

``calib.gsrender`` is the usual loader on a node, but it imports ``gsplat``, which the M20 image
does not have and which needs a CUDA build to install.  The byte work needs no renderer, so this
reads the PLY directly and hands back torch tensors in the same domains (linear scales, sigmoid
opacities, channel-major ``shN``).
"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if os.path.join(ROOT, "research", "code") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "research", "code"))


def degree_from_shn(shn: np.ndarray) -> int:
    """SH degree whose rest block is ``shn`` wide (``45 -> 3``)."""
    k = int(shn.shape[1])
    return int(round((k / 3.0 + 1.0) ** 0.5)) - 1


def load_model(path: str) -> SimpleNamespace:
    from calib.plyio import load_inria_ply

    d = load_inria_ply(path)
    shn = np.asarray(d["shN"], dtype=np.float32)
    return SimpleNamespace(means=torch.from_numpy(np.asarray(d["means"], dtype=np.float32)),
                           scales=torch.from_numpy(np.asarray(d["scales"], dtype=np.float32)),
                           quats=torch.from_numpy(np.asarray(d["quats"], dtype=np.float32)),
                           opacities=torch.from_numpy(np.asarray(d["opacities"],
                                                                dtype=np.float32).reshape(-1)),
                           sh0=torch.from_numpy(np.asarray(d["sh0"], dtype=np.float32)),
                           shN=torch.from_numpy(shn),
                           sh_degree=degree_from_shn(shn))
