"""Second downstream task: dense local *displacement* between render and GT (pure CPU).

Why a second task at all
------------------------
The paper's existing downstream task is patch localisation by normalised
cross-correlation: one global discrete search per patch, and correlation is
invariant to brightness/contrast scaling.  A reviewer can reasonably ask whether
the measured "usability drop" is an artefact of that one matcher.  This script
measures a different family of consumer:

    **block-matching flow** -- 3-level image pyramid, 9x9 zero-mean NCC windows,
    coarse-to-fine integer search.  For every textured sample point we estimate
    the displacement that best aligns the *rendered* frame onto the *ground
    truth* frame, and count a sample as usable when the estimated displacement is
    within ``--tol`` pixels of the truth (the truth is zero: the asset is already
    registered to the camera).

Where this bites in practice
----------------------------
Temporal reprojection / "swimming" in a viewer, frame-to-frame tracking on top of
rendered frames, and flow-warping error (the standard NVS-evaluation use of
optical flow) all consume exactly this quantity: per-pixel local geometric
displacement, not a per-patch yes/no.  Because the matcher is *not* normalised
away from photometry and operates on dense local windows, it is sensitive to the
kinds of error pruning and quantisation actually introduce (structure moving,
edges softening, alpha bleeding), which is what makes it a complementary rather
than a re-labelled measurement.

Output (same shape as the patch-localisation task)
--------------------------------------------------
per scene x variant: hit rate = fraction of sample points with
``max(|dy|,|dx|) <= tol`` after coarse-to-fine refinement, averaged over views,
with a **view-level cluster bootstrap** interval, plus the paired
``delta = hit(edited) - hit(clean)`` bootstrap interval and the flow magnitude
distribution.  Everything is numpy only (no cv2, no torch).

Usage
-----
    python experiments/second_task.py --npz experiments/artifacts/dump \
        --out experiments/artifacts/second_task.json
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Second downstream task: pyramid block-matching displacement.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--npz", default=C.default_out("dump"))
    ap.add_argument("--out", default=C.default_out("second_task.json"))
    ap.add_argument("--variants", default="", help="default: all non-clean variants in the npz")
    ap.add_argument("--levels", type=int, default=3, help="pyramid levels (default 3)")
    ap.add_argument("--win", type=int, default=9, help="matching window (default 9x9)")
    ap.add_argument("--search", type=int, default=4, help="coarsest-level search radius (px)")
    ap.add_argument("--refine", type=int, default=2, help="per-level refinement radius (px)")
    ap.add_argument("--stride", type=int, default=8, help="sample-point grid stride (px)")
    ap.add_argument("--max-points", type=int, default=200, help="cap sample points per view")
    ap.add_argument("--min-texture", type=float, default=0.02,
                    help="minimum window std for a sample point to count as textured")
    ap.add_argument("--tol", type=float, default=1.0, help="usable if |flow|_inf <= tol px")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--max-scenes", type=int, default=0)
    ap.add_argument("--max-views", type=int, default=0)
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    return ap


# ---------------------------------------------------------------------------
# block matching
# ---------------------------------------------------------------------------


def pyramid(img: np.ndarray, levels: int):
    """2x2 box-mean pyramid, ``levels`` images (level 0 = original)."""
    out = [np.asarray(img, np.float32)]
    for _ in range(levels - 1):
        a = out[-1]
        h, w = (a.shape[0] // 2) * 2, (a.shape[1] // 2) * 2
        if h < 8 or w < 8:
            break
        out.append(a[:h, :w].reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3)))
    return out


def _sample_points(gray: np.ndarray, stride: int, min_texture: float, max_points: int,
                   margin: int, rng):
    """Grid sample points with enough texture, deterministically thinned."""
    H, W = gray.shape
    ys = np.arange(margin, max(margin + 1, H - margin), stride)
    xs = np.arange(margin, max(margin + 1, W - margin), stride)
    pts = []
    for y in ys:
        for x in xs:
            w = gray[y:y + 9, x:x + 9]
            if w.shape != (9, 9) or w.std() < min_texture:
                continue
            pts.append((int(y), int(x)))
    if not pts:
        return np.zeros((0, 2), np.int32)
    pts = np.asarray(pts, np.int32)
    if pts.shape[0] > max_points:
        sel = np.sort(rng.choice(pts.shape[0], size=max_points, replace=False))
        pts = pts[sel]
    return pts


def _match_level(gt_img, ren_img, pts, win, search, init):
    """One block-matching pass: ZNCC over a ``+/-search`` neighbourhood of ``init``.

    Returns integer flow per point in this level's pixel units and the best
    correlation.  Zero-mean normalised cross-correlation on 9x9 windows is the
    standard block-matching cost; ``init`` carries the coarser level's estimate
    so the search stays small.
    """
    n = pts.shape[0]
    flow = np.array(init, np.int32).reshape(n, 2).copy()
    peak = np.zeros(n, np.float32)
    H, W = ren_img.shape
    for i in range(n):
        y, x = int(pts[i, 0]), int(pts[i, 1])
        patch = gt_img[y:y + win, x:x + win]
        if patch.shape != (win, win):
            continue
        dy, dx = int(init[i, 0]), int(init[i, 1])
        y0, x0 = y + dy - search, x + dx - search
        # clamp the candidate window into the image
        ay0, ax0 = max(0, y0), max(0, x0)
        ay1 = min(H, y0 + 2 * search + win)
        ax1 = min(W, x0 + 2 * search + win)
        win_img = ren_img[ay0:ay1, ax0:ax1]
        if win_img.shape[0] < win or win_img.shape[1] < win:
            continue
        sw = np.lib.stride_tricks.sliding_window_view(win_img, (win, win))
        ha, wa = sw.shape[0], sw.shape[1]
        cand = sw.reshape(ha * wa, win * win).astype(np.float32)
        p = patch.reshape(-1).astype(np.float32)
        p = p - p.mean()
        pn = float(np.sqrt((p ** 2).sum()))
        cand = cand - cand.mean(axis=1, keepdims=True)
        cn = np.sqrt((cand ** 2).sum(axis=1))
        with np.errstate(divide="ignore", invalid="ignore"):
            score = (cand @ p) / (cn * pn)
        score[~np.isfinite(score)] = -1.0
        k = int(np.argmax(score))
        a, b = divmod(k, wa)
        flow[i, 0] = (ay0 + a) - y
        flow[i, 1] = (ax0 + b) - x
        peak[i] = float(score[k])
    return flow, peak


def block_match_flow(gt_gray, ren_gray, pts, levels=3, win=9, search=4, refine=2):
    """Coarse-to-fine block-matching flow for ``pts`` (full-resolution coordinates)."""
    pgt = pyramid(gt_gray, levels)
    pren = pyramid(ren_gray, levels)
    L = min(len(pgt), len(pren), levels)
    flow = np.zeros((pts.shape[0], 2), np.int32)
    peak = np.zeros(pts.shape[0], np.float32)
    for li in range(L - 1, -1, -1):
        s = 2 ** li
        pts_l = (pts // s).astype(np.int32)
        init = (flow // s) if li < L - 1 else flow          # flow in level-li units
        cur_search = search if li == L - 1 else refine
        flow_l, peak = _match_level(pgt[li], pren[li], pts_l, win, cur_search, init)
        flow = flow_l * s
    return flow.astype(np.float32), peak


# ---------------------------------------------------------------------------
# per-scene evaluation
# ---------------------------------------------------------------------------


def evaluate_scene(sc, variants, args):
    """Per-view hit rate / flow magnitude for every variant of one scene."""
    name = sc["name"]
    m = sc["m"]
    gt = sc["gt"]
    rng = np.random.default_rng([args.seed, zlib.crc32(name.encode()) % 100003])
    margin = args.search * (2 ** (args.levels - 1)) + args.win
    pts_per_view = [_sample_points(gt[i], args.stride, args.min_texture,
                                  args.max_points, margin, rng) for i in range(m)]
    out = {}
    for v in ["clean"] + variants:
        if v not in sc["renders"]:
            continue
        hit, med, p90, np_ = [], [], [], []
        for i in range(m):
            pts = pts_per_view[i]
            if pts.shape[0] == 0:
                continue
            flow, peak = block_match_flow(gt[i], sc["renders"][v][i], pts,
                                          levels=args.levels, win=args.win,
                                          search=args.search, refine=args.refine)
            mag = np.abs(flow).max(axis=1)                 # |flow|_inf in px
            hit.append(float(np.mean(mag <= args.tol)))
            med.append(float(np.median(mag)))
            p90.append(float(np.percentile(mag, 90)))
            np_.append(int(pts.shape[0]))
        out[v] = dict(hit_per_view=hit, median_flow_per_view=med,
                      p90_flow_per_view=p90, n_points_per_view=np_)
        C.log(f"    {name:12s} {v:8s} hit@<={args.tol:.0f}px="
              f"{np.mean(hit) if hit else float('nan'):.3f} "
              f"median|flow|={np.median(med) if med else float('nan'):.2f}px "
              f"({sum(np_)} point-matches)")
    return out


def main(argv=None):
    args = build_parser().parse_args(argv)
    t0 = time.time()
    files = C.discover_npz(args.npz)
    if not files:
        raise SystemExit(f"no npz artifacts under {args.npz}")
    if args.max_scenes:
        files = files[: args.max_scenes]

    scenes_raw = []
    for path in files:
        sc = C.load_npz_scene(path)
        m = sc["gray_gt"].shape[0]
        if args.max_views:
            m = min(m, args.max_views)
        vnames = sc["variant_names"]
        variants = ([v.strip() for v in args.variants.split(",") if v.strip()]
                    if args.variants else [v for v in vnames if v != "clean"])
        scenes_raw.append(dict(
            name=sc["meta"]["scene"], vnames=vnames, edited=variants, m=m,
            gt=sc["gray_gt"][:m].astype(np.float32),
            renders={v: sc["gray_render"][vnames.index(v)][:m].astype(np.float32)
                     for v in ["clean"] + variants if v in vnames},
            meta=sc["meta"], path=path))

    C.log(f"[{C.stamp()}] second_task (block-matching flow): {len(scenes_raw)} scenes, "
          f"levels={args.levels} win={args.win} search={args.search} "
          f"refine={args.refine} stride={args.stride} tol={args.tol}px")

    per_scene, per_view_all = {}, {}
    for sc in scenes_raw:
        C.log(f"  --- {sc['name']}")
        res = evaluate_scene(sc, sc["edited"], args)
        per_scene[sc["name"]] = res
        for v, d in res.items():
            per_view_all.setdefault(v, []).extend(d["hit_per_view"])

    edited = []
    for sc in scenes_raw:
        for v in sc["edited"]:
            if v not in edited:
                edited.append(v)

    summary = {}
    per_view_out = {}
    for v in ["clean"] + edited:
        pv = np.asarray(per_scene.get(scenes_raw[0]["name"], {}).get(v, {})
                        .get("hit_per_view", []), np.float64)
        # pool per-view hit rates over all scenes for the bootstrap
        pooled = []
        for sc in scenes_raw:
            d = per_scene[sc["name"]].get(v)
            if d:
                pooled.extend(d["hit_per_view"])
        pooled = np.asarray(pooled, np.float64)
        if pooled.size == 0:
            continue
        ci = C.bootstrap_mean_ci(pooled, n_boot=args.n_boot, seed=args.seed)
        entry = dict(hit_rate=ci["mean"], hit_lo=ci["lo"], hit_hi=ci["hi"],
                     n_views=int(pooled.size),
                     per_scene_mean={sc["name"]: float(np.mean(
                         per_scene[sc["name"]][v]["hit_per_view"]))
                         for sc in scenes_raw if v in per_scene[sc["name"]]})
        if v != "clean":
            deltas, clean_pv, edit_pv = [], [], []
            for sc in scenes_raw:
                if v not in per_scene[sc["name"]] or "clean" not in per_scene[sc["name"]]:
                    continue
                c = per_scene[sc["name"]]["clean"]["hit_per_view"]
                e = per_scene[sc["name"]][v]["hit_per_view"]
                n = min(len(c), len(e))
                clean_pv.extend(c[:n])
                edit_pv.extend(e[:n])
            if clean_pv:
                dci = C.paired_bootstrap_ci(clean_pv, edit_pv,
                                            n_boot=args.n_boot, seed=args.seed)
                entry.update(delta=dci["mean"], delta_lo=dci["lo"], delta_hi=dci["hi"],
                             degradation_pp=-100.0 * dci["mean"] if dci["mean"] is not None else None,
                             n_views_paired=dci["n"])
        summary[v] = entry
        per_view_out[v] = {sc["name"]: per_scene[sc["name"]][v]["hit_per_view"]
                           for sc in scenes_raw if v in per_scene[sc["name"]]}

    res = dict(
        meta=dict(task="pyramid block-matching displacement (second downstream task)",
                  description="3-level pyramid, zero-mean NCC 9x9 windows, coarse-to-fine "
                              "integer search; hit = max(|dy|,|dx|) <= tol px vs the "
                              "registered GT view",
                  npz=[os.path.basename(f) for f in files],
                  scenes=[sc["name"] for sc in scenes_raw],
                  variants=edited, levels=args.levels, win=args.win,
                  search=args.search, refine=args.refine, stride=args.stride,
                  max_points=args.max_points, tol=args.tol,
                  min_texture=args.min_texture, n_boot=args.n_boot,
                  seed=args.seed, generated=C.stamp(),
                  delta_convention="delta = hit(edited) - hit(clean)"),
        summary=summary,
        per_scene=per_scene,
        per_view_hit_rate=per_view_out,
        seconds=None,
    )
    res["seconds"] = round(time.time() - t0, 1)
    C.json_dump(args.out, res)
    C.log(f"[{C.stamp()}] WROTE {args.out} in {res['seconds']}s")
    for v, d in summary.items():
        C.log(f"  {v:8s} hit@tol={d['hit_rate']:.3f} "
              f"[{d['hit_lo']:.3f},{d['hit_hi']:.3f}] n_views={d['n_views']}"
              + (f"  delta={d['delta']:+.3f} "
                 f"[{d['delta_lo']:+.3f},{d['delta_hi']:+.3f}] "
                 f"degradation={d['degradation_pp']:+.1f}pp"
                 if "delta" in d and d.get("delta") is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
