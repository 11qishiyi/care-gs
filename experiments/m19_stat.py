"""M19: order-free comparison of two PLYs (multiset statistics per attribute).

Rendering 10 dB where the tensors agree to 1e-2 means the pairing between positions and colour is
broken somewhere; matching rows by position is useless when the positions are quantised (ties
dominate a lexsort).  Comparing the *multisets* first says whether the values themselves survived.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib.gsrender as GR

QS = (0.0, 0.01, 0.5, 0.99, 1.0)


def stats(a: np.ndarray) -> np.ndarray:
    return np.quantile(a.reshape(-1), QS)


def main() -> int:
    a = GR.load_splats(sys.argv[1], device="cpu")
    b = GR.load_splats(sys.argv[2], device="cpu")
    attrs = (("means", 3), ("scales", 3), ("quats", 4), ("opacities", 1))
    for key, _ in attrs:
        x = np.asarray(getattr(a, key).detach().cpu().numpy(), dtype=np.float64)
        y = np.asarray(getattr(b, key).detach().cpu().numpy(), dtype=np.float64)
        qa, qb = stats(x), stats(y)
        print(f"{key:10s} ref {np.array2string(qa, precision=4)}  dec {np.array2string(qb, precision=4)}")
    for key in ("sh0", "shN"):
        x = np.asarray(getattr(a, key).detach().cpu().numpy(), dtype=np.float64)
        y = np.asarray(getattr(b, key).detach().cpu().numpy(), dtype=np.float64)
        print(f"{key:10s} ref shape {x.shape} dec {y.shape}")
        qa, qb = stats(x), stats(y)
        print(f"{'':10s} ref {np.array2string(qa, precision=5)}  dec {np.array2string(qb, precision=5)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
