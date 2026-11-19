"""Shared helpers for the revision measurement pipeline -- pure numpy.

Everything in ``experiments/`` is written so that the *analysis* half runs on a
CPU-only workstation with nothing but numpy (no torch, no cv2, no plyfile), while
the *rendering* half runs once on a GPU node and ships small ``.npz`` artifacts
back.

Protocol constants mirror ``research/code/scripts/many_splits.py`` exactly:

* per-pixel residual of a view = ``mean over colour channels of |render - gt|``
  (the "channel-mean abs residual" used for every coverage number in the paper);
* split-conformal quantile ``cq(scores, alpha)`` with the
  ``ceil((n+1)(1-alpha))`` order-statistic rule;
* 400 random calibration/deployment view splits drawn from
  ``np.random.default_rng(0)`` with ``n_C = max(2, n_views // 2)``;
* ``drop = coverage(edited) - coverage(clean)`` paired by split, so a negative
  drop is a degradation.  Task-level numbers keep the same sign convention
  (``delta = hit(edited) - hit(clean)``) and additionally expose the positive
  "degradation" form where that reads better.
"""
from __future__ import annotations

import json
import os
import sys
import time
import warnings

import numpy as np

# --------------------------------------------------------------------------
# protocol constants (keep in sync with research/code/scripts/many_splits.py)
# --------------------------------------------------------------------------
ALPHA = 0.1
N_SPLITS = 400
RNG_SEED = 0
RENDER_CHUNK = 4          # many_splits.py renders in chunks of 4 views
HELDOUT_HOLD = 8          # llffhold used by the released 3DGS archive split


def log(msg: str) -> None:
    print(msg, flush=True)


def stamp() -> str:
    return time.strftime("%H:%M:%S")


def cq(scores, alpha: float = ALPHA) -> float:
    """Split-conformal quantile, same value as ``many_splits.cq``.

    ``many_splits.py`` sorts and indexes; for long pixel vectors we use
    ``np.partition`` instead, which returns the *identical* k-th order statistic
    in O(n) (``tests/test_pipeline_cpu.py`` asserts the two agree).
    """
    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    n = s.size
    if n == 0:
        return float("inf")
    k = min(max(int(np.ceil((n + 1) * (1 - alpha))), 1), n)
    if n > 20000:
        return float(np.partition(s, k - 1)[k - 1])
    return float(np.sort(s)[k - 1])


def split_perms(n_views: int, n_splits: int = N_SPLITS, seed: int = RNG_SEED):
    """Calibration/deployment view splits, generated exactly as ``many_splits.py``.

    Returns a list of ``(cal_idx, dep_idx)`` index arrays.  Regenerating the same
    generator with the same seed reproduces the paper's splits (rng is created
    once, permutations are drawn in order).
    """
    rng = np.random.default_rng(seed)
    n_c = max(2, n_views // 2)
    out = []
    for _ in range(n_splits):
        perm = rng.permutation(n_views)
        out.append((perm[:n_c], perm[n_c:]))
    return out


def to_gray(rgb: np.ndarray) -> np.ndarray:
    """(..., H, W, 3) -> (..., H, W) channel-mean grey, as in voxel_and_task.py."""
    a = np.asarray(rgb, dtype=np.float32)
    return a.mean(axis=-1)


def psnr_np(a, b) -> float:
    """PSNR of arrays in [0, 1] with the same clamp as ``gsrender.psnr``."""
    mse = max(float(np.mean((np.asarray(a, np.float64) - np.asarray(b, np.float64)) ** 2)),
              1e-12)
    return float(-10.0 * np.log10(mse))


def downsample_mean(arr: np.ndarray, f: int) -> np.ndarray:
    """Box-average the last two axes by an integer factor ``f`` (crops the remainder)."""
    if f <= 1:
        return arr
    h, w = arr.shape[-2], arr.shape[-1]
    h2, w2 = (h // f) * f, (w // f) * f
    a = arr[..., :h2, :w2]
    shp = a.shape[:-2] + (h2 // f, f, w2 // f, f)
    return a.reshape(shp).mean(axis=(-3, -1))


def scale_K(K: np.ndarray, f: int) -> np.ndarray:
    """Intrinsics for a box-averaged image (pixel-centre convention)."""
    if f <= 1:
        return np.asarray(K, dtype=np.float32).copy()
    K = np.asarray(K, dtype=np.float64).copy()
    K[..., 0, 0] /= f
    K[..., 1, 1] /= f
    K[..., 0, 2] = (K[..., 0, 2] + 0.5) / f - 0.5
    K[..., 1, 2] = (K[..., 1, 2] + 0.5) / f - 0.5
    return K.astype(np.float32)


def json_dump(path: str, obj) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=_json_default)
        f.write("\n")


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return float(o)


def as_float(x):
    """JSON-safe float or None."""
    if x is None:
        return None
    x = float(x)
    return x if np.isfinite(x) else None


# --------------------------------------------------------------------------
# artifact loading
# --------------------------------------------------------------------------
def load_npz_scene(path: str) -> dict:
    """Load one ``dump_artifacts`` artifact.

    Keys: ``gray_render`` (V,m,H,W) f16, ``resid`` (V,m,H,W) f16, ``gray_gt``
    (m,H,W) f16, ``views`` (m,) i32, ``c2w`` (m,4,4), ``K`` (m,3,3),
    ``variant_names`` (V,), ``meta`` (json string).
    """
    with np.load(path, allow_pickle=False) as z:
        d = {k: z[k] for k in z.files}
    d["meta"] = json.loads(str(d["meta"]) if np.ndim(d["meta"]) == 0 else str(d["meta"][0]))
    d["variant_names"] = [str(v) for v in d["variant_names"]]
    d["path"] = path
    return d


def discover_npz(paths: str):
    """Accept a directory, a single .npz, or a comma-separated list of either."""
    out = []
    for p in str(paths).split(","):
        p = p.strip()
        if not p:
            continue
        if os.path.isdir(p):
            out += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith(".npz")]
        elif os.path.isfile(p):
            out.append(p)
        else:
            raise FileNotFoundError(p)
    return out


def variant_index(scene: dict, name: str) -> int:
    if name not in scene["variant_names"]:
        raise KeyError(f"variant {name!r} not in {scene['path']} "
                       f"(have {scene['variant_names']})")
    return scene["variant_names"].index(name)


# --------------------------------------------------------------------------
# INRIA 3DGS PLY I/O (no plyfile / no torch -- works on the CPU workstation)
# --------------------------------------------------------------------------
_PLY_TYPES = {"char": "i1", "uchar": "u1", "int16": "i2", "short": "i2",
              "ushort": "u2", "int": "i4", "uint": "u4", "float": "f4",
              "double": "f8", "int32": "i4", "uint8": "u1", "float32": "f4",
              "float64": "f8"}


def write_inria_ply(path: str, means, scales, quats, opacities, sh0, shN,
                    comment: str = "") -> str:
    """Write an INRIA-format 3DGS PLY that ``calib.gsrender.load_splats`` can read.

    ``scales`` are **log** scales and ``opacities`` are **logit** opacities (the
    on-disk 3DGS convention).  ``shN`` is (N, K-1, 3) basis-major and is written
    channel-major (all R, then G, then B), which is what ``calib/plyio.py``
    expects.  Pure numpy so the local CPU test can round-trip it.
    """
    means = np.asarray(means, np.float32).reshape(-1, 3)
    n = means.shape[0]
    scales = np.asarray(scales, np.float32).reshape(n, 3)
    quats = np.asarray(quats, np.float32).reshape(n, 4)
    opac = np.asarray(opacities, np.float32).reshape(n, 1)
    sh0 = np.asarray(sh0, np.float32).reshape(n, 3)
    shN = np.asarray(shN, np.float32)
    if shN.size == 0:
        shN = np.zeros((n, 0, 3), np.float32)
    shN = shN.reshape(n, -1, 3)
    k1 = shN.shape[1]
    f_rest = shN.transpose(0, 2, 1).reshape(n, 3 * k1)   # channel-major

    names = ["x", "y", "z", "nx", "ny", "nz",
             "f_dc_0", "f_dc_1", "f_dc_2"]
    names += [f"f_rest_{i}" for i in range(3 * k1)]
    names += ["opacity", "scale_0", "scale_1", "scale_2",
              "rot_0", "rot_1", "rot_2", "rot_3"]

    cols = [means[:, 0], means[:, 1], means[:, 2],
            np.zeros(n, np.float32), np.zeros(n, np.float32), np.zeros(n, np.float32),
            sh0[:, 0], sh0[:, 1], sh0[:, 2]]
    cols += [f_rest[:, i] for i in range(3 * k1)]
    cols += [opac[:, 0], scales[:, 0], scales[:, 1], scales[:, 2],
             quats[:, 0], quats[:, 1], quats[:, 2], quats[:, 3]]
    data = np.stack([np.asarray(c, np.float32) for c in cols], axis=1)

    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        head = ["ply", "format binary_little_endian 1.0"]
        if comment:
            head.append("comment " + comment.replace("\n", " "))
        head.append(f"element vertex {n}")
        head += [f"property float {nm}" for nm in names]
        head.append("end_header")
        f.write(("\n".join(head) + "\n").encode("ascii"))
        f.write(data.astype("<f4").tobytes(order="C"))
    return path


def read_inria_ply(path: str) -> dict:
    """Read an INRIA 3DGS PLY with numpy only; returns the *on-disk* values.

    ``scales`` are log scales, ``opacities`` are logit opacities (call
    ``np.exp`` / ``sigmoid`` to get the model values, exactly like
    ``calib/plyio.load_inria_ply`` does).
    """
    with open(path, "rb") as f:
        if f.readline().strip() != b"ply":
            raise ValueError(f"{path}: not a PLY file")
        fmt = None
        n = None
        prop_names, prop_types = [], []
        while True:
            line = f.readline()
            if not line:
                raise ValueError(f"{path}: truncated header")
            tok = line.decode("ascii", "replace").strip().split()
            if not tok:
                continue
            if tok[0] == "format":
                fmt = tok[1]
            elif tok[0] == "element":
                if tok[1] != "vertex":
                    raise ValueError(f"{path}: only vertex elements supported")
                n = int(tok[2])
            elif tok[0] == "property":
                prop_names.append(tok[2])
                prop_types.append(_PLY_TYPES[tok[1]])
            elif tok[0] == "end_header":
                break
        if fmt != "binary_little_endian":
            raise ValueError(f"{path}: need binary_little_endian, got {fmt}")
        if n is None:
            raise ValueError(f"{path}: no vertex element")
        dt = np.dtype([(nm, "<" + tp) for nm, tp in zip(prop_names, prop_types)])
        raw = np.frombuffer(f.read(dt.itemsize * n), dtype=dt, count=n)

    idx = {nm: i for i, nm in enumerate(prop_names)}

    def col(name):
        return np.asarray(raw[name], np.float32)

    out = dict(
        means=np.stack([col("x"), col("y"), col("z")], 1),
        scales=np.stack([col(f"scale_{i}") for i in range(3)], 1),
        opacities=col("opacity"),
        quats=np.stack([col(f"rot_{i}") for i in range(4)], 1),
        sh0=np.stack([col(f"f_dc_{i}") for i in range(3)], 1)[:, None, :],
    )
    k_rest = sum(1 for nm in prop_names if nm.startswith("f_rest_"))
    if k_rest:
        fr = np.stack([col(f"f_rest_{i}") for i in range(k_rest)], 1)
        k1 = k_rest // 3
        out["shN"] = fr.reshape(n, 3, k1).transpose(0, 2, 1).copy()
    else:
        out["shN"] = np.zeros((n, 0, 3), np.float32)
    out["n"] = int(n)
    out["properties"] = prop_names
    out["index"] = idx
    return out


def ply_means(path: str):
    """(N,3) world-space primitive centres + probability opacities."""
    d = read_inria_ply(path)
    opac = 1.0 / (1.0 + np.exp(-d["opacities"]))
    return d["means"], opac


# --------------------------------------------------------------------------
# world-space voxels (hash identical to research/code/calib/voxel_cert.py)
# --------------------------------------------------------------------------
def voxel_ids(pts: np.ndarray, voxel: float) -> np.ndarray:
    q = np.floor(np.asarray(pts, np.float64) / float(voxel)).astype(np.int64)
    return (q[..., 0] * 73856093) ^ (q[..., 1] * 19349663) ^ (q[..., 2] * 83492791)


def voxel_size_from_extent(means: np.ndarray, per_axis: int = 32) -> float:
    ext = float(np.max(np.ptp(np.asarray(means, np.float64), axis=0)))
    return max(ext / float(per_axis), 1e-6)


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def bootstrap_mean_ci(per_unit: np.ndarray, n_boot: int = 2000, seed: int = RNG_SEED,
                      alpha: float = 0.05):
    """Cluster bootstrap over independent units (views).

    ``per_unit`` is (n_units,) of a per-view statistic; the bootstrap resamples
    *views* with replacement, so the interval reflects view-to-view variance --
    the same view-level cluster bootstrap the paper uses for coverage.
    """
    v = np.asarray(per_unit, np.float64)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return dict(mean=None, lo=None, hi=None, n=int(0))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    means = v[idx].mean(axis=1)
    return dict(mean=float(v.mean()),
                lo=float(np.percentile(means, 100 * alpha / 2)),
                hi=float(np.percentile(means, 100 * (1 - alpha / 2))),
                n=int(v.size), n_boot=int(n_boot))


def paired_bootstrap_ci(a_per_unit, b_per_unit, n_boot: int = 2000, seed: int = RNG_SEED,
                        alpha: float = 0.05):
    """Cluster bootstrap of ``mean(b) - mean(a)`` with the same resampled views."""
    a = np.asarray(a_per_unit, np.float64)
    b = np.asarray(b_per_unit, np.float64)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    if a.size == 0:
        return dict(mean=None, lo=None, hi=None, n=int(0))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a.size, size=(n_boot, a.size))
    d = b[idx].mean(axis=1) - a[idx].mean(axis=1)
    return dict(mean=float(b.mean() - a.mean()),
                lo=float(np.percentile(d, 100 * alpha / 2)),
                hi=float(np.percentile(d, 100 * (1 - alpha / 2))),
                n=int(a.size), n_boot=int(n_boot))


# --------------------------------------------------------------------------
# coverage helpers shared by region_coverage.py / task_sweep.py
# --------------------------------------------------------------------------
def pixel_split_coverage(clean_flat, edited_flat, splits, alpha: float = ALPHA, qs=None):
    """The paper's per-pixel protocol (``many_splits.py``), vectorised over splits.

    ``clean_flat`` / ``edited_flat`` are (n_views, n_pixels) arrays; for every
    split the threshold is the split-conformal quantile of the **clean**
    calibration pixels and coverage is the fraction of *deployment* pixels below
    it -- for the clean model and for the edited model, so the difference is
    paired by split exactly as in ``many_splits.py``.
    """
    clean_flat = np.asarray(clean_flat)
    edited_flat = np.asarray(edited_flat)
    if qs is None:
        qs = [cq(clean_flat[cal].reshape(-1), alpha) for cal, _ in splits]
    clean_cov, stale_cov = [], []
    for q, (cal, dep) in zip(qs, splits):
        dep = np.asarray(dep)
        clean_cov.append(float((clean_flat[dep] <= q).mean()))
        stale_cov.append(float((edited_flat[dep] <= q).mean()))
    clean_cov = np.asarray(clean_cov)
    stale_cov = np.asarray(stale_cov)
    return clean_cov, stale_cov, stale_cov - clean_cov, np.asarray(qs, np.float64)


def pooled_coverage_splits(clean_E, edited_E, splits, alpha: float = ALPHA,
                           pool="max", unseen_uncovered: bool = True,
                           return_info: bool = False):
    """Region-level split-conformal coverage, ``voxel_and_task.py`` style.

    ``clean_E`` / ``edited_E`` are (m_views, n_regions) matrices with NaN where a
    region is not observed in that view.  For every split:

    * per-region calibration score = pooled (max or mean) over calibration views;
    * ``q`` = conformal quantile of the calibration scores;
    * deployment score = pooled over deployment views;
    * coverage = fraction of deployment regions with score <= q;
      regions seen in deployment but never in calibration count as **uncovered**
      (the certificate makes no claim about them) unless
      ``unseen_uncovered=False``, in which case they are dropped.

    Returns ``(clean_cov, stale_cov, drops)`` as arrays over splits.
    """
    m = clean_E.shape[0]
    clean_cov, stale_cov, drops = [], [], []
    n_dep, n_fresh, n_cal_seen = [], [], []
    for cal, dep in splits:
        cal = np.asarray(cal)
        dep = np.asarray(dep)
        if cal.size == 0 or dep.size == 0 or m == 0:
            continue
        cal_s = _pool(clean_E[cal], pool)
        ok = np.isfinite(cal_s)
        if not ok.any():
            continue
        q = cq(cal_s[ok], alpha)
        cl = _pool(clean_E[dep], pool)
        st = _pool(edited_E[dep], pool)
        seen_cal = np.isfinite(clean_E[cal]).any(axis=0)
        seen_dep = np.isfinite(cl)
        if unseen_uncovered:
            # a region observed in deployment but never in calibration carries an
            # infinite score -> automatically uncovered (voxel_cert.py's docstring)
            fresh = seen_dep & ~seen_cal
            cl = np.where(np.isfinite(cl), cl, np.inf)
            st = np.where(np.isfinite(st), st, np.inf)
        else:
            fresh = np.zeros_like(seen_dep)
            seen_dep = seen_dep & np.isfinite(st)
        if not seen_dep.any():
            continue
        clean_cov.append(float(np.mean(cl[seen_dep] <= q)))
        stale_cov.append(float(np.mean(st[seen_dep] <= q)))
        drops.append(stale_cov[-1] - clean_cov[-1])
        n_dep.append(int(seen_dep.sum()))
        n_fresh.append(int(np.sum(seen_dep & ~seen_cal)))
        n_cal_seen.append(int(np.sum(seen_cal)))
        del fresh
    out = (np.asarray(clean_cov), np.asarray(stale_cov), np.asarray(drops))
    if return_info:
        info = dict(n_dep_mean=float(np.mean(n_dep)) if n_dep else None,
                    n_fresh_mean=float(np.mean(n_fresh)) if n_fresh else None,
                    n_fresh_frac_mean=float(np.mean(np.asarray(n_fresh, float)
                                                     / np.maximum(np.asarray(n_dep, float), 1)))
                    if n_dep else None,
                    n_cal_seen_mean=float(np.mean(n_cal_seen)) if n_cal_seen else None)
        return out + (info,)
    return out


def _pool(E, pool):
    E = np.asarray(E, np.float64)
    if E.shape[0] == 0:
        return np.zeros(E.shape[1])
    fin = np.isfinite(E)
    if not fin.any():
        return np.full(E.shape[1], np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)      # all-NaN columns
        if pool == "max":
            out = np.nanmax(np.where(fin, E, np.nan), axis=0)
            return np.where(np.isfinite(out), out, np.nan)
        if pool == "mean":
            cnt = fin.sum(axis=0)
            s = np.nansum(np.where(fin, E, 0.0), axis=0)
            return np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)
    raise ValueError(pool)


def summarise_drops(drops, clean_cov=None, stale_cov=None, alpha: float = 0.05):
    """Mean / percentile summary of the paired per-split coverage drops."""
    d = np.asarray(drops, np.float64)
    d = d[np.isfinite(d)]
    out = dict(n_splits=int(d.size),
               drop_mean=as_float(d.mean()) if d.size else None,
               drop_lo=as_float(np.percentile(d, 100 * alpha / 2)) if d.size else None,
               drop_hi=as_float(np.percentile(d, 100 * (1 - alpha / 2))) if d.size else None,
               degradation_pp=as_float(-100.0 * d.mean()) if d.size else None)
    if clean_cov is not None and np.size(clean_cov):
        c = np.asarray(clean_cov, np.float64)
        out.update(clean_mean=as_float(c.mean()),
                   clean_lo=as_float(np.percentile(c, 2.5)),
                   clean_hi=as_float(np.percentile(c, 97.5)))
    if stale_cov is not None and np.size(stale_cov):
        s = np.asarray(stale_cov, np.float64)
        out.update(stale_mean=as_float(s.mean()),
                   stale_lo=as_float(np.percentile(s, 2.5)),
                   stale_hi=as_float(np.percentile(s, 97.5)))
    return out


def add_code_root():
    """Put ``research/code`` on sys.path so ``calib.*`` imports resolve."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(os.path.dirname(here), "research", "code")
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def default_out(name: str) -> str:
    return os.path.join(script_dir(), "artifacts", name)


def sizeof_fmt(nbytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024.0:
            return f"{nbytes:.1f}{unit}"
        nbytes /= 1024.0
    return f"{nbytes:.1f}TB"


def read_struct_head(path: str, n: int = 4096) -> bytes:  # pragma: no cover - debugging aid
    with open(path, "rb") as f:
        return f.read(n)
