"""One-shot revision battery, run ON the GPU node (rendering + analyses, JSON only out).

    python experiments/node_run.py diag    --archive ... --out /workspace/res/diag.json
    python experiments/node_run.py battery --archive ... --out /workspace/res/battery --pup-dir ...

diag     photometric diagnostic: one render, five GT conventions -> PSNR, residual scale,
         conformal q, fresh coverage, 30%-prune coverage drop.
battery  coverage (pixel + 64x64 block-max, 400 random cal/deploy splits, paired q growth),
         dose-response over prune ratios, patch re-localisation with a paired patch set and a
         (patch x search) sweep with a tol/peak grid, second task (pyramid block matching),
         PSNR table.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "research", "code"))

ALPHA = 0.10
VARIANTS = ("clean", "prune70", "prune50", "prune30", "prune10", "pup30", "shdeg1", "quant8")


# ------------------------------------------------------------------ statistics
def cq(scores, alpha=ALPHA):
    s = np.sort(np.asarray(scores).reshape(-1))
    n = s.size
    if n == 0:
        return float("nan")
    k = min(max(int(np.ceil((n + 1) * (1 - alpha))), 1), n)
    return float(s[k - 1])


def psnr(a, b):
    mse = float(np.mean((np.asarray(a, np.float64) - np.asarray(b, np.float64)) ** 2))
    return float("inf") if mse <= 1e-12 else float(10.0 * np.log10(1.0 / mse))


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
    qc, qe = np.asarray(qc), np.asarray(qe)
    d = stale - clean
    g = qe / np.clip(qc, 1e-9, None) - 1.0
    return dict(clean_mean=float(clean.mean()), clean_lo=float(np.percentile(clean, 2.5)),
                clean_hi=float(np.percentile(clean, 97.5)), stale_mean=float(stale.mean()),
                drop_mean=float(d.mean()), drop_lo=float(np.percentile(d, 2.5)),
                drop_hi=float(np.percentile(d, 97.5)),
                q_mean=float(qc.mean()), q_edit_mean=float(qe.mean()),
                q_growth_mean=float(g.mean()), q_growth_lo=float(np.percentile(g, 2.5)),
                q_growth_hi=float(np.percentile(g, 97.5)),
                n_views=int(n), n_cal=int(n_c))


def cluster_boot(per_view, n_boot=2000, seed=0):
    rng = np.random.default_rng(seed)
    v = np.asarray(per_view, dtype=np.float64)
    if v.size == 0:
        return (float("nan"), float("nan"))
    m = rng.choice(v, size=(n_boot, v.size), replace=True).mean(1)
    return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


# ------------------------------------------------------------------ NCC / tasks
def ncc_map(img, patch):
    H, W = img.shape
    P = patch.shape[0]
    if H < P or W < P:
        return np.zeros((0, 0), np.float32)
    win = np.lib.stride_tricks.sliding_window_view(img, (P, P))
    win = win.reshape(H - P + 1, W - P + 1, -1).astype(np.float32)
    win -= win.mean(axis=2, keepdims=True)
    den = np.sqrt((win ** 2).sum(axis=2))
    p = patch.reshape(-1).astype(np.float32)
    p = p - p.mean()
    pn = np.sqrt((p ** 2).sum())
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (win @ p) / (den * pn)
    out[~np.isfinite(out)] = 0.0
    return out


def ncc_peaks(img, gt, corners, size, search):
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


def sample_corners(gray, size, n, rng, min_std=0.02):
    H, W = gray.shape
    out = []
    for _ in range(n * 80):
        if len(out) >= n:
            break
        y = int(rng.integers(0, max(1, H - size)))
        x = int(rng.integers(0, max(1, W - size)))
        if gray[y:y + size, x:x + size].std() >= min_std:
            out.append((y, x))
    return out


def hit_rate(peaks, tol, min_peak):
    if not peaks:
        return float("nan")
    ok = sum(1 for dy, dx, pk in peaks if dy <= tol and dx <= tol and pk >= min_peak)
    return ok / len(peaks)


def flow_hit(gt_gray, img_gray, stride=6, win=9, rad=10):
    """Pyramid-free block matching: mean |disp| <= 1 px on a strided grid."""
    H, W = gt_gray.shape
    r = win // 2
    ok = tot = 0
    for y in range(r, H - r, stride):
        for x in range(r, W - r, stride):
            pa = gt_gray[y - r:y + r + 1, x - r:x + r + 1]
            if pa.std() < 1e-3:
                continue
            y0, y1 = max(0, y - rad), min(H, y + rad + win)
            x0, x1 = max(0, x - rad), min(W, x + rad + win)
            sub = img_gray[y0:y1, x0:x1]
            if sub.shape[0] < win or sub.shape[1] < win:
                continue
            m = ncc_map(sub, pa)
            if m.size == 0:
                continue
            iy, ix = np.unravel_index(np.argmax(m), m.shape)
            if abs((iy + y0) - y) <= 1 and abs((ix + x0) - x) <= 1:
                ok += 1
            tot += 1
    return float(ok / tot) if tot else float("nan")


# ------------------------------------------------------------------ scene / render
def build_scene(archive, scene, factor):
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images
    sc = load_archive_only_scene(archive, scene, factor=factor, cal_frac=0.5)
    W, H = sc["width"], sc["height"]
    gt = load_images(sc["image_paths"], factor, (W, H)).astype(np.float32) / 255.0
    return sc, gt, W, H


def find_ply(archive, scene):
    base = os.path.join(archive, "output", scene)
    for c in (os.path.join(base, "point_cloud", "iteration_40000", "point_cloud.ply"),
              os.path.join(base, "point_cloud", "iteration_30000", "point_cloud.ply")):
        if os.path.isfile(c):
            return c
    hits_ = [os.path.join(dp, f) for dp, _d, fn in os.walk(base) for f in fn if f.endswith(".ply")]
    if not hits_:
        raise SystemExit(f"no ply for {scene}")
    return sorted(hits_)[-1]


def make_variants(ply, pup_dir, scene, device):
    import torch
    from calib.gsrender import load_splats
    base = load_splats(ply, device=device)
    out = {"clean": base}
    for name, ratio in (("prune70", 0.7), ("prune50", 0.5), ("prune30", 0.3), ("prune10", 0.1)):
        k = max(1, int(round(ratio * base.n)))
        keep = torch.argsort(-base.opacities)[:k].sort().values
        out[name] = base.subset(keep)
    if base.shN is not None and base.shN.shape[1] > 4:
        d1 = base.clone()
        d1.shN[:, 4:, :] = 0.0
        out["shdeg1"] = d1
    q8 = base.clone()
    qmax = 127.0
    for nm in ("sh0", "shN"):
        t = getattr(q8, nm)
        if t is None:
            continue
        scale = t.abs().amax(dim=(1, 2), keepdim=True).clamp_min(1e-8) / qmax
        setattr(q8, nm, torch.round(t / scale).clamp(-qmax - 1, qmax) * scale)
    out["quant8"] = q8
    if pup_dir:
        # any <scene>_<name>.ply in this directory becomes a variant called <name>
        import glob as _glob
        for p in sorted(_glob.glob(os.path.join(pup_dir, f"{scene}_*.ply"))):
            name = os.path.basename(p)[len(scene) + 1:-4]
            out[name] = load_splats(p, device=device)
    return out


def render_chw(splats, c2w, K, W, H, device, chunk=4):
    import torch
    from calib.gsrender import render
    cols = []
    n = c2w.shape[0]
    with torch.no_grad():
        for s in range(0, n, chunk):
            it = torch.arange(s, min(n, s + chunk), device=device)
            cols.append(render(splats, c2w[it], K[it], W, H)["colors"].permute(0, 3, 1, 2).float().cpu())
    return torch.cat(cols, 0)


# ------------------------------------------------------------------ diag
def cmd_diag(args):
    import torch
    from calib.colmap_io import normalize_exposure
    from calib.gsrender import load_splats

    rows = []
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        sc, gt, W, H = build_scene(args.archive, scene, args.factor)
        gt_t = torch.from_numpy(gt).permute(0, 3, 1, 2)
        gt_norm = torch.from_numpy(normalize_exposure(gt * 255.0)).permute(0, 3, 1, 2)
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        base = load_splats(find_ply(args.archive, scene), device=args.device)
        k = max(1, int(round(0.3 * base.n)))
        keep = torch.argsort(-base.opacities)[:k].sort().values
        ren = {"clean": render_chw(base, c2w, K, W, H, args.device),
               "prune30": render_chw(base.subset(keep), c2w, K, W, H, args.device)}

        def stats(g, tag, rb=None):
            r = ren if rb is None else rb
            rc = (r["clean"] - g).abs().mean(1).numpy()
            rp = (r["prune30"] - g).abs().mean(1).numpy()
            return dict(tag=tag, psnr=psnr(r["clean"].numpy(), g.numpy()),
                        psnr30=psnr(r["prune30"].numpy(), g.numpy()),
                        resid_median=float(np.median(rc)), resid_mean=float(rc.mean()),
                        **split_stats(rc, rp, alpha=args.alpha))

        def mean_match(src, target):
            s = src.mean(dim=(1, 2, 3), keepdim=True).clamp_min(1e-6)
            t = target.mean(dim=(1, 2, 3), keepdim=True)
            return src * (t / s)

        def gain_fit(src, target):
            outs = []
            for i in range(src.shape[0]):
                a = float((src[i].reshape(-1) * target[i].reshape(-1)).sum()
                          / max(float((src[i].reshape(-1) ** 2).sum()), 1e-8))
                outs.append(src[i] * a)
            return torch.stack(outs, 0)

        prot = {
            "raw": stats(gt_t, "raw"),
            "norm_gt": stats(gt_norm, "norm_gt"),
            "norm_both": stats(gt_norm, "norm_both", {k2: mean_match(v, gt_norm) for k2, v in ren.items()}),
            "gain": stats(gt_t, "gain", {k2: gain_fit(v, gt_t) for k2, v in ren.items()}),
        }
        row = dict(scene=scene, n_primitives=int(base.n), n_views=int(len(gt)), W=W, H=H,
                   gt_mean=float(gt.mean()), render_mean=float(ren["clean"].mean()),
                   gt_view_means=[round(float(x), 3) for x in gt.reshape(len(gt), -1).mean(1)],
                   render_view_means=[round(float(x), 3) for x in ren["clean"].reshape(len(gt), -1).mean(1)],
                   protocols=prot)
        rows.append(row)
        print(f"\n=== {scene}: {base.n} primitives, {W}x{H}, {len(gt)} views ===")
        for name, p in prot.items():
            print(f"  {name:9s} PSNR {p['psnr']:6.2f}  med {p['resid_median']:.4f}  "
                  f"cov {p['clean_mean']:.3f}  drop30 {100*p['drop_mean']:+.1f}pp "
                  f"[{100*p['drop_lo']:+.1f},{100*p['drop_hi']:+.1f}]  qg {100*p['q_growth_mean']:+.1f}%")
        print(f"  gt means {row['gt_view_means'][:6]}\n  rn means {row['render_view_means'][:6]}", flush=True)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(rows, open(args.out, "w", encoding="utf-8"), indent=1)
    print("\nWROTE", args.out)


# ------------------------------------------------------------------ battery
def cmd_battery(args):
    import torch

    os.makedirs(args.out, exist_ok=True)
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        t0 = time.time()
        sc, gt, W, H = build_scene(args.archive, scene, args.factor)
        gt_t = torch.from_numpy(gt).permute(0, 3, 1, 2)
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        variants = make_variants(find_ply(args.archive, scene), args.pup_dir, scene, args.device)
        names = [n for n in VARIANTS if n in variants] + [n for n in variants if n not in VARIANTS]
        print(f"\n=== {scene}: {variants['clean'].n} prim pruned, {len(gt)} views, {names} ===", flush=True)

        resid, gray, psnr_tab = {}, {}, {}
        for name in names:
            img = render_chw(variants[name], c2w, K, W, H, args.device)
            resid[name] = (img - gt_t).abs().mean(1).numpy().astype(np.float32)
            gray[name] = img.mean(1).numpy().astype(np.float32)
            psnr_tab[name] = dict(psnr=psnr(img.numpy(), gt_t.numpy()),
                                  resid_mean=float(resid[name].mean()),
                                  resid_median=float(np.median(resid[name])),
                                  n_primitives=int(variants[name].n))
            del img
            torch.cuda.empty_cache()
            print(f"  {name:8s} PSNR {psnr_tab[name]['psnr']:6.2f}  med {psnr_tab[name]['resid_median']:.4f}"
                  f"  ({time.time()-t0:.0f}s)", flush=True)

        clean = resid["clean"]
        out = dict(scene=scene, n_views=int(len(gt)), W=W, H=H, alpha=args.alpha,
                   psnr=psnr_tab, coverage={}, block={}, task_sweep={}, flow={})
        for name in names:
            if name == "clean":
                continue
            out["coverage"][name] = split_stats(clean, resid[name], alpha=args.alpha)
            out["block"][name] = split_stats(block_max(clean), block_max(resid[name]), alpha=args.alpha)
            c, b = out["coverage"][name], out["block"][name]
            print(f"  cov {name:8s} pix {100*c['drop_mean']:+.1f}pp [{100*c['drop_lo']:+.1f},"
                  f"{100*c['drop_hi']:+.1f}]  blk {100*b['drop_mean']:+.1f}pp  qg {100*c['q_growth_mean']:+.1f}%",
                  flush=True)

        gt_gray = gt.mean(3)
        rng = np.random.default_rng(1234)
        for size, search in ((32, 24), (24, 16), (48, 24)):
            corners = [sample_corners(gt_gray[v], size, args.n_patches, rng) for v in range(len(gt_gray))]
            key = f"s{size}_w{search}"
            peaks = {}
            for name in names:
                acc = []
                for v in range(len(gt_gray)):
                    acc += ncc_peaks(gray[name][v], gt_gray[v], corners[v], size, search)
                peaks[name] = acc
            out["task_sweep"][key] = {
                f"tol{tol}_peak{pk}": {name: hit_rate(peaks[name], tol, pk) for name in names}
                for tol in (1, 2, 4) for pk in (0.30, 0.45, 0.60, 0.75)}
            print(f"  task {key}: " + "  ".join(
                f"{n}={out['task_sweep'][key]['tol2_peak0.6'][n]:.3f}" for n in names), flush=True)

        step = max(1, len(gt_gray) // 10)
        for name in names:
            vals = [flow_hit(gt_gray[v].astype(np.float32), gray[name][v].astype(np.float32))
                    for v in range(0, len(gt_gray), step)]
            lo, hi = cluster_boot([x for x in vals if x == x])
            out["flow"][name] = dict(hit_mean=float(np.nanmean(vals)), hit_lo=lo, hit_hi=hi,
                                     n_views=len(vals))
            print(f"  flow {name:8s} {out['flow'][name]['hit_mean']:.3f} "
                  f"[{lo:.3f},{hi:.3f}]", flush=True)

        p = os.path.join(args.out, f"{scene}.json")
        json.dump(out, open(p, "w", encoding="utf-8"), indent=1)
        print(f"WROTE {p} ({time.time()-t0:.0f}s)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["diag", "battery"])
    ap.add_argument("--archive", default="/workspace/data/official")
    ap.add_argument("--scenes", default="flowers,bicycle,treehill,stump")
    ap.add_argument("--out", default="/workspace/res")
    ap.add_argument("--pup-dir", default=None)
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--alpha", type=float, default=ALPHA)
    ap.add_argument("--n-patches", type=int, default=60)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    cmd_diag(args) if args.cmd == "diag" else cmd_battery(args)


if __name__ == "__main__":
    main()
