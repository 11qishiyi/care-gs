"""One-pass evaluation used by the second measurement round.

Per scene, this renders four variants of the same asset exactly once and reports

  * coverage under 400 random calibration/deployment splits for each variant (pixel and block),
  * the paired quantile growth, so the criterion comparison is like-for-like,
  * a reduced task sweep (one (patch, search) configuration over the 12-cell threshold grid),
  * per-view residual diagnostics that explain a heavy tail: residual percentiles, the fraction
    of pixels beyond the clean quantile, and the fraction of saturated pixels.

Variants: clean, opacity prune to 30%, Fisher-sensitivity prune to 30% (calibration views only),
and an opacity-times-volume prune to 30% (the classic "importance" heuristic).

    python experiments/stage9_eval.py --archive /workspace/data/out3dgs \
        --scenes bicycle,flowers,stump,treehill --out /workspace/res/stage9
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "research", "code"))
sys.path.insert(0, os.path.join(REPO, "experiments"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ALPHA = 0.10


def now():
    return time.strftime("%H:%M:%S")


def cq(scores, alpha=ALPHA):
    s = np.sort(np.asarray(scores).reshape(-1))
    n = s.size
    if n == 0:
        return float("nan")
    k = min(max(int(np.ceil((n + 1) * (1 - alpha))), 1), n)
    return float(s[k - 1])


def block_max(r, blk=64):
    m, H, W = r.shape
    Hb, Wb = H // blk, W // blk
    if Hb == 0 or Wb == 0:
        return r.reshape(m, -1)
    return r[:, :Hb * blk, :Wb * blk].reshape(m, Hb, blk, Wb, blk).max(axis=(2, 4)).reshape(m, -1)


def split_stats(rc, re_, n_splits=400, seed=0, alpha=ALPHA):
    rng = np.random.default_rng(seed)
    n = rc.shape[0]
    n_c = max(2, n // 2)
    clean, stale, qc, qe = [], [], [], []
    for _ in range(n_splits):
        perm = rng.permutation(n)
        ci, vi = perm[:n_c], perm[n_c:]
        q_cal = cq(rc[ci], alpha)
        q_ed = cq(re_[ci], alpha)
        clean.append(float((rc[vi] <= q_cal).mean()))
        stale.append(float((re_[vi] <= q_cal).mean()))
        qc.append(q_cal)
        qe.append(q_ed)
    clean, stale = np.asarray(clean), np.asarray(stale)
    g = np.asarray(qe) / np.clip(np.asarray(qc), 1e-9, None) - 1.0
    d = stale - clean
    return dict(clean_mean=float(clean.mean()), clean_lo=float(np.percentile(clean, 2.5)),
                clean_hi=float(np.percentile(clean, 97.5)), stale_mean=float(stale.mean()),
                drop_mean=float(d.mean()), drop_lo=float(np.percentile(d, 2.5)),
                drop_hi=float(np.percentile(d, 97.5)),
                q_growth_mean=float(g.mean()), q_growth_lo=float(np.percentile(g, 2.5)),
                q_growth_hi=float(np.percentile(g, 97.5)),
                n_views=int(n), n_cal=int(n_c))


# ------------------------------------------------------------------ variants
def top_k(scores, ratio):
    import torch
    k = max(1, int(round(ratio * scores.numel())))
    return torch.argsort(-scores)[:k].sort().values


def make_variants(base, scene_data, ratio, use_fisher):
    """Return {name: splats} for clean, opacity, fisher, opacity*volume."""
    import torch
    out = {"clean": base}
    out["opacity30"] = base.subset(top_k(base.opacities, ratio))

    vol = (4.0 / 3.0 * np.pi) * base.scales.prod(dim=1)
    opv = base.opacities * vol
    out["opv30"] = base.subset(top_k(opv, ratio))

    if use_fisher:
        try:
            t0 = time.time()
            from calib.sensitivity import sensitivity_scores
            cal = [int(i) for i in scene_data["cal_idx"]]
            gt_t = torch.as_tensor(np.ascontiguousarray(scene_data["gt"]),
                                   dtype=torch.float32, device=scene_data["device"])
            scores = sensitivity_scores(base, scene_data["c2w"], scene_data["K"], gt_t, cal,
                                        scene_data["W"], scene_data["H"], n_views=4,
                                        device=scene_data["device"])
            out["fisher30"] = base.subset(top_k(torch.as_tensor(scores), ratio))
            print(f"  fisher scores in {time.time()-t0:.0f}s", flush=True)
            del gt_t, scores
            torch.cuda.empty_cache()
        except Exception as e:                                   # noqa: BLE001
            print("  fisher variant failed:", repr(e), flush=True)
            traceback.print_exc()
    return out


def render_np(splats, c2w, K, W, H, device, chunk=4):
    import torch
    from calib.gsrender import render
    cols = []
    n = c2w.shape[0]
    with torch.no_grad():
        for s in range(0, n, chunk):
            it = torch.arange(s, min(n, s + chunk), device=device)
            cols.append(render(splats, c2w[it], K[it], W, H)["colors"].permute(0, 3, 1, 2).float().cpu())
    return torch.cat(cols, 0).numpy()          # (m,3,H,W)


def ncc_peaks_local(img, gt, corners, size, search):
    from second_task2 import ncc_map
    H, W = img.shape
    out = []
    for (y, x) in corners:
        patch = gt[y:y + size, x:x + size]
        if patch.shape[0] != size or patch.shape[1] != size:
            continue
        y0, y1 = max(0, y - search), min(H, y + search + size)
        x0, x1 = max(0, x - search), min(W, x + search + size)
        win = img[y0:y1, x0:x1]
        if win.shape[0] < size or win.shape[1] < size:
            continue
        m = ncc_map(win, patch)
        if m.size == 0:
            continue
        iy, ix = np.unravel_index(np.argmax(m), m.shape)
        out.append((int(abs((iy + y0) - y)), int(abs((ix + x0) - x)), float(m[iy, ix])))
    return out


def hit_rate(peaks, tol, min_peak):
    if not peaks:
        return float("nan")
    ok = sum(1 for dy, dx, pk in peaks if dy <= tol and dx <= tol and pk >= min_peak)
    return ok / len(peaks)


def eval_scene(args, scene):
    import torch
    from second_task2 import build_scene, find_ply
    from node_run import sample_corners
    from calib.gsrender import load_splats

    t_start = time.time()
    sc, gt, W, H = build_scene(args.archive, scene, args.factor)
    c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
    K = torch.from_numpy(sc["Ks"]).to(args.device)
    base = load_splats(find_ply(args.archive, scene), device=args.device)
    scene_data = dict(c2w=c2w, K=K, gt=gt, cal_idx=sc["cal_idx"], W=W, H=H, device=args.device)
    print(f"[{now()}] {scene}: {base.n} primitives, {len(gt)} views, {W}x{H}, "
          f"{time.time()-t_start:.0f}s to load", flush=True)
    variants = make_variants(base, scene_data, args.ratio, not args.no_fisher)
    print(f"[{now()}] {scene}: variants {sorted(variants)}", flush=True)

    resid, gray, psnr = {}, {}, {}
    gt_chw = np.transpose(gt, (0, 3, 1, 2))
    for name, sp in variants.items():
        img = render_np(sp, c2w, K, W, H, args.device)
        resid[name] = np.abs(img - gt_chw).mean(1).astype(np.float32)
        gray[name] = img.mean(1).astype(np.float32)
        mse = float(np.mean((img - gt_chw) ** 2))
        psnr[name] = float(10 * np.log10(1.0 / mse)) if mse > 0 else float("inf")
        print(f"  rendered {name:10s} n={sp.n:8d}  PSNR {psnr[name]:5.2f}  "
              f"median resid {np.median(resid[name]):.4f}  ({time.time()-t_start:.0f}s)", flush=True)
        del img
        torch.cuda.empty_cache()

    clean = resid["clean"]
    q_clean = cq(clean[: len(clean) // 2], ALPHA)
    out = dict(scene=scene, n_views=int(len(gt)), W=W, H=H, ratio=args.ratio,
               n_primitives={k: int(v.n) for k, v in variants.items()},
               psnr=psnr, coverage={}, block={}, resid_diag={}, task={})

    gt_means = gt.reshape(len(gt), -1).mean(1)
    for name in variants:
        r = resid[name]
        ren_means = np.mean(gray[name].reshape(len(gt), -1), axis=1)
        out["resid_diag"][name] = dict(
            p50=[float(np.percentile(v, 50)) for v in r],
            p90=[float(np.percentile(v, 90)) for v in r],
            p99=[float(np.percentile(v, 99)) for v in r],
            beyond_q=[float((v > q_clean).mean()) for v in r],
            sat_white=[float((v > 0.98).mean()) for v in r],
            brightness_ratio=[float(a / max(b, 1e-6)) for a, b in zip(ren_means, gt_means)])

    for name in variants:
        if name == "clean":
            continue
        out["coverage"][name] = split_stats(clean, resid[name], alpha=ALPHA)
        out["block"][name] = split_stats(block_max(clean), block_max(resid[name]), alpha=ALPHA)
        c, b = out["coverage"][name], out["block"][name]
        print(f"  cov {name:10s} pix {100*c['drop_mean']:+6.1f}pp "
              f"[{100*c['drop_lo']:+6.1f},{100*c['drop_hi']:+6.1f}]  blk {100*b['drop_mean']:+6.1f}pp"
              f"  q {100*c['q_growth_mean']:+6.0f}%", flush=True)

    if not args.skip_task:
        rng = np.random.default_rng(1234)
        gt_gray = gt.mean(3)
        size, search = 32, 24
        corners = [sample_corners(gt_gray[v], size, args.n_patches, rng) for v in range(len(gt_gray))]
        peaks = {}
        for name in variants:
            acc = []
            for v in range(len(gt_gray)):
                acc += ncc_peaks_local(gray[name][v], gt_gray[v], corners[v], size, search)
            peaks[name] = acc
        out["task"] = {f"tol{tol}_peak{pk}": {n: hit_rate(peaks[n], tol, pk) for n in variants}
                       for tol in (1, 2, 4) for pk in (0.30, 0.45, 0.60, 0.75)}
        print("  task(clean, tol2/peak.6) = "
              f"{out['task']['tol2_peak0.6']['clean']:.3f}", flush=True)

    out["seconds"] = round(time.time() - t_start, 1)
    p = os.path.join(args.out, f"{scene}.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1)
    print(f"[{now()}] WROTE {p} ({out['seconds']}s)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill")
    ap.add_argument("--out", default="/workspace/res/stage9")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--ratio", type=float, default=0.3)
    ap.add_argument("--n-patches", type=int, default=60)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--no-fisher", action="store_true")
    ap.add_argument("--skip-task", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        try:
            eval_scene(args, scene)
        except Exception:                                     # noqa: BLE001
            print(f"[{now()}] SCENE FAILED {scene}", flush=True)
            traceback.print_exc()
            continue


if __name__ == "__main__":
    main()
