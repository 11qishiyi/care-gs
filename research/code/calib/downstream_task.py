"""A downstream task that uses only RGB: patch localisation in the rendered view.

The report's metric is coverage of a residual threshold.  A reviewer will ask: does
that number correspond to anything a *consumer* of the asset cares about?  This
module answers with a task-level measurement that needs no extra annotations:

    task: given a small patch cut from the ground-truth image, can a simple
          cross-correlation matcher still locate it inside the rendered image?

Patch localisation is what visual odometry / relocalisation / template-based
inspection actually do, so "the render still supports localisation" is a defensible
proxy for "the asset is still usable".  The matcher is deliberately dumb (normalised
cross-correlation on grayscale) so that the number measures the *render*, not the
matcher.

Per patch we record, for the clean and the edited model:
  * hit@tol  -- the best match lands within `tol` pixels of the true location
  * peak     -- the normalised correlation at that location
and we report how the hit rate degrades under an edit.
"""
from __future__ import annotations

import numpy as np


def ncc_map(img: np.ndarray, patch: np.ndarray) -> np.ndarray:
    """Normalised cross-correlation of `patch` over `img` (both 2-D float arrays).

    Returns an array of the valid positions, i.e. shape (H-P+1, W-P+1).
    """
    H, W = img.shape
    P = patch.shape[0]
    if img.shape[0] < P or img.shape[1] < P:
        return np.zeros((0, 0), dtype=np.float32)
    win = np.lib.stride_tricks.sliding_window_view(img, (P, P))     # (H-P+1, W-P+1, P, P)
    win = win.reshape(H - P + 1, W - P + 1, -1).astype(np.float32)
    win = win - win.mean(axis=2, keepdims=True)
    denom = np.sqrt((win ** 2).sum(axis=2))
    p = patch.reshape(-1).astype(np.float32)
    p = p - p.mean()
    pn = np.sqrt((p ** 2).sum())
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (win @ p) / (denom * pn)
    out[~np.isfinite(out)] = 0.0
    return out.astype(np.float32)


def localise(img: np.ndarray, patch: np.ndarray):
    """Best matching top-left position and its correlation."""
    m = ncc_map(img, patch)
    if m.size == 0:
        return None, 0.0
    idx = np.unravel_index(np.argmax(m), m.shape)
    return idx, float(m[idx])


def sample_patches(gray: np.ndarray, size: int, n: int, rng, min_texture: float = 0.02):
    """Sample patch top-left corners at textured locations of the ground-truth image."""
    H, W = gray.shape
    if H < size + 2 or W < size + 2:
        return []
    gx = np.abs(np.diff(gray, axis=1)).mean()
    out = []
    for _ in range(n * 40):
        if len(out) >= n:
            break
        y = int(rng.integers(0, H - size))
        x = int(rng.integers(0, W - size))
        p = gray[y:y + size, x:x + size]
        if p.std() >= min_texture:
            out.append((y, x))
    return out


def task_success(render_gray: np.ndarray, gt_gray: np.ndarray, corners, size: int,
                 tol: int = 2, min_peak: float = 0.6, search: int = 24):
    """Fraction of patches a correlation matcher can still re-localise in the render.

    The search is confined to a window of +/- `search` pixels around the true
    location: full-frame matching is both meaningless (the asset is already
    registered) and 10^3x more expensive.  A hit means "re-localised within `tol`
    pixels with a confident peak".
    """
    H, W = render_gray.shape
    hits, peaks = 0, []
    for (y, x) in corners:
        patch = gt_gray[y:y + size, x:x + size]
        y0, y1 = max(0, y - search), min(H, y + search + size)
        x0, x1 = max(0, x - search), min(W, x + search + size)
        win = render_gray[y0:y1, x0:x1]
        if win.shape[0] < size or win.shape[1] < size:
            peaks.append(0.0)
            continue
        pos, peak = localise(win, patch)
        peaks.append(peak)
        if pos is None:
            continue
        dy = abs((pos[0] + y0) - y)
        dx = abs((pos[1] + x0) - x)
        if dy <= tol and dx <= tol and peak >= min_peak:
            hits += 1
    n = max(1, len(corners))
    return dict(hit_rate=hits / n, mean_peak=float(np.mean(peaks)) if peaks else 0.0,
                n_patches=int(len(corners)))
