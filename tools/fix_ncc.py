import io
p = r"D:\3dsg_1\research\code\calib\downstream_task.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''def task_success(render_gray: np.ndarray, gt_gray: np.ndarray, corners, size: int,
                 tol: int = 2, min_peak: float = 0.6):
    """Fraction of patches that a correlation matcher can still localise in the render."""
    hits, peaks = 0, []
    for (y, x) in corners:
        patch = gt_gray[y:y + size, x:x + size]
        pos, peak = localise(render_gray, patch)
        peaks.append(peak)
        if pos is None:
            continue
        dy = abs(pos[0] - y)
        dx = abs(pos[1] - x)
        if dy <= tol and dx <= tol and peak >= min_peak:
            hits += 1
    n = max(1, len(corners))
    return dict(hit_rate=hits / n, mean_peak=float(np.mean(peaks)) if peaks else 0.0,
                n_patches=int(len(corners)))''',
'''def task_success(render_gray: np.ndarray, gt_gray: np.ndarray, corners, size: int,
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
                n_patches=int(len(corners)))''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("search window added")
