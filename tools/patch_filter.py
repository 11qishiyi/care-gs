# -*- coding: utf-8 -*-
"""Add per-view COLMAP quality filtering to the scene loader."""
import io
p = r"D:\3dsg_1\research\code\calib\colmap_io.py"
s = io.open(p, encoding="utf-8").read()

helper = '''

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
                if c in (b"\\x00", b""):
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
'''

s = s.replace("\n\ndef load_colmap_scene(", helper + "\n\ndef load_colmap_scene(")

s = s.replace('''    idx = np.arange(len(paths))
    if split == "interleaved":''',
'''    idx = np.arange(len(paths))
    if filter_views:
        q = per_view_quality(sparse)
        keep = (q["n2d"] >= min_n2d) & (q["med_err"] <= max_med_err)
        idx = idx[keep]
        camtoworlds = [camtoworlds[i] for i in idx]
        Ks = [Ks[i] for i in idx]
        paths = [paths[i] for i in idx]
        print(f"[scene] kept {keep.sum()}/{len(keep)} views "
              f"(n2d>={min_n2d}, med_err<={max_med_err})", flush=True)

    if split == "interleaved":''')

s = s.replace('''                      split: str = "interleaved", cal_frac: float = 0.12,
                      train_frac: float = 0.65):''',
'''                      split: str = "interleaved", cal_frac: float = 0.12,
                      train_frac: float = 0.65, filter_views: bool = True,
                      min_n2d: int = 150, max_med_err: float = 2.5):''')

io.open(p, "w", encoding="utf-8").write(s)
print("patched colmap_io")
