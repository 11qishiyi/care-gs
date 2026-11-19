"""Minimal COLMAP binary reader + scene loader (no pycolmap dependency).

Reading the binary format directly keeps the pipeline deterministic across
pycolmap versions, which matters because every experiment downstream depends on
the camera convention being exactly right.
"""
from __future__ import annotations

import os
import struct

import numpy as np

# COLMAP camera model ids -> (name, num_params, has_distortion)
CAMERA_MODELS = {
    0: ("SIMPLE_PINHOLE", 3),
    1: ("PINHOLE", 4),
    2: ("SIMPLE_RADIAL", 4),
    3: ("RADIAL", 5),
    4: ("OPENCV", 8),
    5: ("OPENCV_FISHEYE", 8),
    6: ("FULL_OPENCV", 12),
    7: ("FOV", 5),
    8: ("SIMPLE_RADIAL_FISHEYE", 4),
    9: ("RADIAL_FISHEYE", 5),
    10: ("THIN_PRISM_FISHEYE", 12),
}


def _read(fid, fmt):
    size = struct.calcsize(fmt)
    return struct.unpack(fmt, fid.read(size))


def read_cameras_bin(path: str) -> dict:
    cams = {}
    with open(path, "rb") as f:
        n = _read(f, "<Q")[0]
        for _ in range(n):
            cam_id, model_id, w, h = _read(f, "<iiQQ")
            nparams = CAMERA_MODELS[model_id][1]
            params = _read(f, "<" + "d" * nparams)
            cams[cam_id] = dict(model_id=model_id, width=int(w), height=int(h),
                                params=np.array(params, dtype=np.float64))
    return cams


def read_images_bin(path: str) -> list:
    imgs = []
    with open(path, "rb") as f:
        n = _read(f, "<Q")[0]
        for _ in range(n):
            img_id = _read(f, "<i")[0]
            qvec = np.array(_read(f, "<dddd"), dtype=np.float64)  # w x y z
            tvec = np.array(_read(f, "<ddd"), dtype=np.float64)
            cam_id = _read(f, "<i")[0]
            name = b""
            while True:
                c = f.read(1)
                if c == b"\x00" or c == b"":
                    break
                name += c
            npts = _read(f, "<Q")[0]
            f.read(24 * npts)  # x, y (double), point3D_id (int64)
            imgs.append(dict(id=img_id, qvec=qvec, tvec=tvec, cam_id=cam_id,
                             name=name.decode("utf-8", "replace")))
    return imgs


def read_points3D_bin(path: str):
    xyz, rgb = [], []
    with open(path, "rb") as f:
        n = _read(f, "<Q")[0]
        for _ in range(n):
            _pid = _read(f, "<Q")[0]
            p = _read(f, "<ddd")
            c = _read(f, "<BBB")
            _err = _read(f, "<d")[0]
            track_len = _read(f, "<Q")[0]
            f.read(track_len * 8)
            xyz.append(p)
            rgb.append(c)
    return np.asarray(xyz, dtype=np.float64), np.asarray(rgb, dtype=np.uint8)


def qvec2rotmat(q):
    w, x, y, z = q
    n = w * w + x * x + y * y + z * z
    if n < 1e-12:
        return np.eye(3)
    s = 2.0 / n
    return np.array([
        [1 - s * (y * y + z * z), s * (x * y - w * z), s * (x * z + w * y)],
        [s * (x * y + w * z), 1 - s * (x * x + z * z), s * (y * z - w * x)],
        [s * (x * z - w * y), s * (y * z + w * x), 1 - s * (x * x + y * y)],
    ])


def intrinsic_matrix(cam: dict, scale: float) -> np.ndarray:
    """3x3 K for the supported models, rescaled by `scale` (1/factor)."""
    p = cam["params"]
    mid = cam["model_id"]
    if mid in (0, 2, 3, 8, 9):      # f, cx, cy, ...
        f, cx, cy = p[0], p[1], p[2]
        fx = fy = f
    elif mid in (1, 4, 5, 6, 10):   # fx, fy, cx, cy, ...
        fx, fy, cx, cy = p[0], p[1], p[2], p[3]
    elif mid == 7:                  # FOV: fx, fy, cx, cy, omega
        fx, fy, cx, cy = p[0], p[1], p[2], p[3]
    else:
        raise ValueError(f"unsupported camera model {mid}")
    K = np.array([[fx * scale, 0.0, cx * scale],
                  [0.0, fy * scale, cy * scale],
                  [0.0, 0.0, 1.0]], dtype=np.float64)
    return K


def per_view_quality(sparse_dir: str, model: str = "x"):
    """Per-view registration quality from COLMAP's own 2D observations.

    Returns dict with arrays ``n2d`` (number of 2D observations with a 3D point)
    and ``med_err`` (median reprojection error in pixels).  Views whose errors are
    large or whose support is tiny are effectively unregistered, and including
    them makes multi-view training fight itself.
    """
    cams = read_cameras_bin(os.path.join(sparse_dir, "cameras.bin"))
    xyz, _ = read_points3D_bin(os.path.join(sparse_dir, "points3D.bin"))
    ids = []
    with open(os.path.join(sparse_dir, "points3D.bin"), "rb") as f:
        n = _read(f, "<Q")[0]
        for _ in range(n):
            pid = _read(f, "<Q")[0]
            f.read(24 + 3 + 8)
            tl = _read(f, "<Q")[0]
            f.read(8 * tl)
            ids.append(pid)
    pid2idx = {p: i for i, p in enumerate(ids)}

    imgs = []
    with open(os.path.join(sparse_dir, "images.bin"), "rb") as f:
        n = _read(f, "<Q")[0]
        for _ in range(n):
            iid = _read(f, "<i")[0]
            q = np.array(_read(f, "<dddd"))
            t = np.array(_read(f, "<ddd"))
            cid = _read(f, "<i")[0]
            name = b""
            while True:
                c = f.read(1)
                if c in (b"\x00", b""):
                    break
                name += c
            m = _read(f, "<Q")[0]
            pts = [struct.unpack("<ddq", f.read(24)) for _ in range(m)]
            imgs.append(dict(id=iid, q=q, t=t, cam=cid, name=name.decode(), pts=pts))
    imgs.sort(key=lambda d: d["name"])

    n2d, med = [], []
    for d in imgs:
        cam = cams[d["cam"]]
        pp = cam["params"]
        if cam["model_id"] in (0, 2, 3):
            fx = fy = pp[0]; cx, cy = pp[1], pp[2]
        else:
            fx, fy, cx, cy = pp[0], pp[1], pp[2], pp[3]
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        R = qvec2rotmat(d["q"]); t = d["t"]
        errs = []
        for (x, y, pid) in d["pts"]:
            if pid < 0 or pid not in pid2idx:
                continue
            X = xyz[pid2idx[pid]]
            Xc = R @ X + t
            if Xc[2] <= 1e-6:
                continue
            uvh = K @ np.array([Xc[0] / Xc[2], Xc[1] / Xc[2], 1.0])
            uv = uvh[:2] / uvh[2]
            errs.append(np.hypot(uv[0] - x, uv[1] - y))
        n2d.append(len(errs))
        med.append(float(np.median(errs)) if errs else float("inf"))
    return dict(n2d=np.array(n2d), med_err=np.array(med), names=[d["name"] for d in imgs])


def load_colmap_scene(root: str, factor: int = 1, test_every: int = 8,
                      split: str = "interleaved", cal_frac: float = 0.12,
                      train_frac: float = 0.65, filter_views: bool = True,
                      min_n2d: int = 150, max_med_err: float = 2.5):
    """Load a COLMAP scene.

    Returns dict with camtoworlds (N,4,4) float32, Ks (N,3,3) float32,
    image_paths, and index arrays.

    Splits
    ------
    ``interleaved`` : ``i % test_every == 0`` -> test (gsplat/3DGS convention).
    ``chrono``      : views sorted by name (capture order); the first
        ``train_frac`` are training, the next ``cal_frac`` are calibration
        (held out from training), and the remaining tail is *deployment*.
        This is the realistic setting: you calibrate on the trajectory you have
        and then deploy past its end.
    """
    sparse = os.path.join(root, "sparse", "0")
    if not os.path.isdir(sparse):
        sparse = os.path.join(root, "sparse")
    cams = read_cameras_bin(os.path.join(sparse, "cameras.bin"))
    imgs = read_images_bin(os.path.join(sparse, "images.bin"))
    imgs.sort(key=lambda d: d["name"])

    # images may live in images/, images_2/, images_4/ ... depending on factor
    sub = "" if factor == 1 else f"_{factor}"
    img_dir = os.path.join(root, f"images{sub}")
    if not os.path.isdir(img_dir):
        img_dir = os.path.join(root, "images")

    camtoworlds, Ks, paths = [], [], []
    for d in imgs:
        R = qvec2rotmat(d["qvec"])
        t = d["tvec"]
        w2c = np.eye(4)
        w2c[:3, :3] = R
        w2c[:3, 3] = t
        c2w = np.linalg.inv(w2c)
        cam = cams[d["cam_id"]]
        scale = 1.0 / factor
        Ks.append(intrinsic_matrix(cam, scale).astype(np.float32))
        camtoworlds.append(c2w.astype(np.float32))
        paths.append(os.path.join(img_dir, d["name"]))

    idx = np.arange(len(paths))
    # mirrors sometimes ship only a subset of the images; drop cameras whose file is missing
    missing = np.array([not os.path.isfile(p) for p in paths])
    if missing.any():
        print(f"[scene] dropping {int(missing.sum())} views whose image file is absent",
              flush=True)
        keep = ~missing
        idx = idx[keep]
        camtoworlds = [camtoworlds[i] for i in idx]
        Ks = [Ks[i] for i in idx]
        paths = [paths[i] for i in idx]
    if filter_views:
        q_full = per_view_quality(sparse)
        sel = np.asarray(idx, dtype=int)
        q = {k: np.asarray(v)[sel] for k, v in q_full.items()}
        keep = (q["n2d"] >= min_n2d) & (q["med_err"] <= max_med_err)
        idx = idx[keep]
        camtoworlds = [camtoworlds[i] for i in idx]
        Ks = [Ks[i] for i in idx]
        paths = [paths[i] for i in idx]
        print(f"[scene] kept {keep.sum()}/{len(keep)} views "
              f"(n2d>={min_n2d}, med_err<={max_med_err})", flush=True)

    if split == "interleaved":
        test = idx[idx % test_every == 0]
        cal = test
        dep = np.array([], dtype=int)
        train = idx[idx % test_every != 0]
    elif split == "chrono":
        n = len(paths)
        n_tr = int(round(train_frac * n))
        n_cal = int(round(cal_frac * n))
        train = idx[:n_tr]
        cal = idx[n_tr:n_tr + n_cal]
        dep = idx[n_tr + n_cal:]
    else:
        raise ValueError(split)

    return dict(
        camtoworlds=np.stack(camtoworlds, 0),
        Ks=np.stack(Ks, 0),
        image_paths=paths,
        image_names=[d["name"] for d in imgs],
        width=int(round(cams[imgs[0]["cam_id"]]["width"] / factor)),
        height=int(round(cams[imgs[0]["cam_id"]]["height"] / factor)),
        train_idx=train,
        cal_idx=cal,
        dep_idx=dep,
        test_idx=cal if split == "interleaved" else np.concatenate([cal, dep]),
        sparse_dir=sparse,
        factor=factor,
    )


def load_image(path: str, factor: int, size=None) -> np.ndarray:
    from PIL import Image
    im = Image.open(path)
    if size is not None and (im.width, im.height) != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im.convert("RGB"))


def load_images(paths, factor: int, size, verbose: bool = False) -> np.ndarray:
    out = []
    for i, p in enumerate(paths):
        out.append(load_image(p, factor, size))
        if verbose and i % 25 == 0:
            print(f"  loaded {i+1}/{len(paths)}", flush=True)
    return np.stack(out, 0)


def normalize_exposure(imgs: np.ndarray, target: float = 0.40) -> np.ndarray:
    """Scale each image so its mean intensity equals ``target``.

    Mip-NeRF 360 captures are auto-exposed: per-image brightness varies by up to
    ~2.3x, which a shared radiance field cannot represent.  Normalising removes
    that nuisance *deterministically*, so training, calibration and deployment
    all see the same transform (no per-view parameters to leak information).
    """
    out = imgs.astype(np.float32) / 255.0
    m = out.reshape(out.shape[0], -1).mean(axis=1).clip(1e-3, None)
    out = out * (target / m)[:, None, None, None]
    return np.clip(out, 0.0, 1.0)
