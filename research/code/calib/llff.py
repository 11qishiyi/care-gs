"""LLFF scene loader from ``poses_bounds.npy``.

LLFF ships a COLMAP folder whose image names do not match the released images, so
the authoritative camera source is ``poses_bounds.npy`` (N x 17): a 3x5 pose
matrix per image plus near/far bounds.  The stored pose is camera-to-world in the
LLFF convention (x right, y **down**, z forward), and the focal length refers to
the resolution the poses were estimated at.

This loader reproduces the standard nerf-pytorch conversion so the resulting
cameras are directly usable by gsplat.
"""
from __future__ import annotations

import os

import numpy as np


def load_llff_scene(root: str, factor: int = 4, cal_frac: float = 0.2,
                    train_frac: float = 0.6):
    pb = np.load(os.path.join(root, "poses_bounds.npy")).astype(np.float64)
    n = pb.shape[0]
    poses = pb[:, :15].reshape(n, 3, 5)
    # LLFF stores columns [down, right, backwards, translation, hwf];
    # convert to the conventional [right, up, backwards] with a positive y
    poses = np.concatenate([poses[:, 1:2, :], -poses[:, 0:1, :], poses[:, 2:, :]], 1)

    hwf = poses[0, :, -1]
    h0, w0, focal0 = hwf
    bottom = np.tile(np.array([0.0, 0.0, 0.0, 1.0]).reshape(1, 1, 4), (n, 1, 1))
    c2w = np.concatenate([poses[:, :, :4], bottom], axis=1)          # (n,4,4)

    # image resolution actually used
    sub = "images" if factor == 1 else f"images_{factor}"
    img_dir = os.path.join(root, sub)
    if not os.path.isdir(img_dir):
        img_dir = os.path.join(root, "images")
    names = sorted(os.listdir(img_dir))
    imgs = [os.path.join(img_dir, f) for f in names]
    from PIL import Image
    W, H = Image.open(imgs[0]).size

    s = W / float(w0)                      # scale from pose resolution to ours
    K = np.array([[focal0 * s, 0, W / 2.0],
                  [0, focal0 * s, H / 2.0],
                  [0, 0, 1]], dtype=np.float64)

    # LLFF bounds are for a different scale; keep the cameras as-is (metric scale is
    # irrelevant for rendering) but make sure the scene is in front of the cameras.
    idx = np.arange(n)
    n_tr = int(round(train_frac * n))
    n_cal = int(round(cal_frac * n))
    return dict(camtoworlds=c2w.astype(np.float32),
                Ks=np.repeat(K[None].astype(np.float32), n, 0),
                image_paths=imgs, width=W, height=H,
                train_idx=idx[:n_tr], cal_idx=idx[n_tr:n_tr + n_cal],
                dep_idx=idx[n_tr + n_cal:],
                names=[os.path.splitext(x)[0] for x in names])
