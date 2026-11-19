"""Threshold-sensitivity sweep of the downstream localisation task (pure CPU, from npz).

The paper reports one downstream-task number per scene, which invites the
question "did you tune the matcher to make the drop look big?".  This script
answers it by sweeping the three knobs a practitioner would actually vary --
patch size, match tolerance, peak threshold and search radius -- over the grid

    patch   in {32, 48, 64}
    tol     in {1, 2, 4}          pixels
    peak    >= {0.30, 0.45, 0.60, 0.75}
    search  in {16, 24, 32}       pixels around the true location
    patches = 100 per (scene, view-batch), drawn from the ground-truth image

and reports, for every cell of the grid, the clean hit rate, the edited hit
rate(s) and the task drop.  It then answers the stability question directly:
across all 108 cells, how often does the *task* drop of 30 % pruning exceed the
*coverage* drop of the same edit, and how often is the variant ordering by task
drop the same as the ordering by coverage drop?

Everything here is recomputed from ``dump_artifacts.py`` npz files, and the NCC
matcher is imported from ``research/code/calib/downstream_task.py`` -- there is no
second copy of the matcher in this repository's experiment folder.

An analytic shortcut, verified at runtime
-----------------------------------------
``task_success`` decides a hit with ``dy <= tol and dx <= tol and peak >= min_peak``.
The best-match offset and its correlation do not depend on ``tol``/``min_peak``,
only on ``(size, search)``, so we compute ``(dy, dx, peak)`` once per
(view, patch, size, search, variant) and then evaluate the 12 (tol, peak) cells
from that cache.  ``--verify`` re-runs ``task_success`` itself on a subset and
asserts the two agree exactly, so the shortcut cannot silently drift from the
reference implementation.

Usage
-----
    python experiments/task_sweep.py --npz experiments/artifacts/dump \
        --out experiments/artifacts/task_sweep.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Downstream localisation task: threshold sensitivity sweep.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--npz", default=C.default_out("dump"),
                    help="npz dir / file / comma list produced by dump_artifacts.py")
    ap.add_argument("--out", default=C.default_out("task_sweep.json"))
    ap.add_argument("--variants", default="",
                    help="edited variants to sweep (default: all but clean, in npz order)")
    ap.add_argument("--sizes", default="32,48,64")
    ap.add_argument("--tols", default="1,2,4")
    ap.add_argument("--peaks", default="0.3,0.45,0.6,0.75")
    ap.add_argument("--searches", default="16,24,32")
    ap.add_argument("--n-patches", type=int, default=100,
                    help="patches per scene, spread evenly over its held-out views")
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--n-splits", type=int, default=C.N_SPLITS,
                    help="splits for the coverage reference (paper protocol: 400)")
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--n-boot", type=int, default=2000, help="view-level bootstrap reps")
    ap.add_argument("--max-scenes", type=int, default=0)
    ap.add_argument("--max-views", type=int, default=0, help="cap views per scene (debug)")
    ap.add_argument("--verify", dest="verify", action="store_true", default=True,
                    help="cross-check the (dy,dx,peak) shortcut against task_success")
    ap.add_argument("--no-verify", dest="verify", action="store_false")
    return ap


def _floats(s):
    return [float(x) for x in str(s).split(",") if str(x).strip()]


def _ints(s):
    return [int(float(x)) for x in str(s).split(",") if str(x).strip()]


# ---------------------------------------------------------------------------
# matcher wrapper (uses calib.downstream_task.localise -- no second NCC here)
# ---------------------------------------------------------------------------


def match_deltas(task, render_gray, gt_gray, corners, size, search):
    """Best-match offsets/correlation for every patch.

    Mirrors the window cropping of ``downstream_task.task_success`` (same lines:
    ``y0 = max(0, y-search)`` ... ``win = render[y0:y1, x0:x1]``) but returns the
    raw ``(dy, dx, peak)`` so that ``tol`` / ``min_peak`` can be swept for free.
    """
    H, W = render_gray.shape
    n = len(corners)
    dy = np.full(n, 10 ** 6, np.int32)
    dx = np.full(n, 10 ** 6, np.int32)
    peak = np.zeros(n, np.float32)
    ok = np.zeros(n, bool)
    for i, (y, x) in enumerate(corners):
        patch = gt_gray[y:y + size, x:x + size]
        y0, y1 = max(0, y - search), min(H, y + search + size)
        x0, x1 = max(0, x - search), min(W, x + search + size)
        win = render_gray[y0:y1, x0:x1]
        if win.shape[0] < size or win.shape[1] < size:
            continue
        pos, pk = task.localise(win, patch)
        if pos is None:
            continue
        dy[i] = abs(int(pos[0] + y0) - int(y))
        dx[i] = abs(int(pos[1] + x0) - int(x))
        peak[i] = pk
        ok[i] = True
    return dy, dx, peak, ok


def hits_from_deltas(dy, dx, peak, ok, tol, min_peak):
    return int(np.sum(ok & (dy <= tol) & (dx <= tol) & (peak >= min_peak)))


def sample_corners(task, gt_gray, size, n_per_view, rng, min_texture=0.02):
    """Deterministic patch corners for one view at one patch size."""
    return task.sample_patches(gt_gray, size, n_per_view, rng, min_texture=min_texture)


# ---------------------------------------------------------------------------
# coverage reference (the paper's per-pixel protocol, used for the stability test)
# ---------------------------------------------------------------------------


def coverage_reference(scenes, variants, n_splits, alpha, seed):
    """Per-pixel coverage drop (positive pp = degraded) for every scene x variant."""
    out = {}
    for sc in scenes:
        resid = sc["resid"].astype(np.float32)                 # (V,m,H,W)
        vnames = sc["vnames"]
        if "clean" not in vnames:
            continue
        ci = vnames.index("clean")
        m = resid.shape[1]
        clean_flat = resid[ci].reshape(m, -1)
        splits = C.split_perms(m, n_splits, seed)
        qs = [C.cq(clean_flat[cal].reshape(-1), alpha) for cal, _ in splits]
        row = {}
        for v in variants:
            if v not in vnames:
                continue
            vi = vnames.index(v)
            _, _, drops, _ = C.pixel_split_coverage(
                clean_flat, resid[vi].reshape(m, -1), splits, alpha, qs=qs)
            row[v] = C.summarise_drops(drops)
        out[sc["meta"]["scene"]] = row
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def run(args) -> dict:
    task = C.add_code_root()
    sys.path.insert(0, task)
    from calib import downstream_task as dtask  # noqa: E402  (the reference matcher)

    files = C.discover_npz(args.npz)
    if not files:
        raise SystemExit(f"no npz artifacts found under {args.npz}")
    sizes = _ints(args.sizes)
    tols = _ints(args.tols)
    peaks = _floats(args.peaks)
    searches = _ints(args.searches)
    if args.max_scenes:
        files = files[: args.max_scenes]

    C.log(f"[{C.stamp()}] task_sweep: {len(files)} npz, grid "
          f"sizes={sizes} tols={tols} peaks={peaks} searches={searches} "
          f"n_patches={args.n_patches}")

    # ---- load + patch sampling + match cache -----------------------------
    scenes = []
    for path in files:
        sc = C.load_npz_scene(path)
        meta = sc["meta"]
        name = meta["scene"]
        vnames = sc["variant_names"]
        edited = ([v.strip() for v in args.variants.split(",") if v.strip()]
                  if args.variants else [v for v in vnames if v != "clean"])
        missing = [v for v in edited if v not in vnames]
        if missing:
            raise SystemExit(f"{name}: variants {missing} not in npz ({vnames})")
        m = sc["gray_gt"].shape[0]
        if args.max_views:
            m = min(m, args.max_views)
        gt = sc["gray_gt"][:m].astype(np.float32)
        renders = {v: sc["gray_render"][vnames.index(v)][:m].astype(np.float32)
                   for v in (["clean"] + edited) if v in vnames}
        n_per_view = max(1, int(np.ceil(args.n_patches / max(1, m))))
        store = dict(name=name, path=path, meta=meta, m=m, gt=gt, renders=renders,
                     edited=edited, corners={}, cache={},
                     resid=sc["resid"], vnames=vnames)
        # patch corners: one rng per (scene, size), identical across variants/views
        t0 = time.time()
        for size in sizes:
            cs = []
            for i in range(m):
                rng = np.random.default_rng([args.seed, zlib.crc32(name.encode()) % 100003,
                                             size, i])
                cs.append(sample_corners(dtask, gt[i], size, n_per_view, rng))
            store["corners"][size] = cs
        C.log(f"  {name}: {m} views, {n_per_view} patches/view/size "
              f"({time.time() - t0:.1f}s sampling)")
        scenes.append(store)

    # ---- matching (the only expensive part) ------------------------------
    for sc in scenes:
        t0 = time.time()
        for size in sizes:
            for search in searches:
                for v in ["clean"] + sc["edited"]:
                    if v not in sc["renders"]:
                        continue
                    per_view = []
                    for i in range(sc["m"]):
                        per_view.append(match_deltas(dtask, sc["renders"][v][i],
                                                     sc["gt"][i], sc["corners"][size][i],
                                                     size, search))
                    sc["cache"][(size, search, v)] = per_view
        C.log(f"  {sc['name']}: matched {len(sizes) * len(searches)} (size,search) x "
              f"{len(sc['renders'])} variants in {time.time() - t0:.1f}s")

    # ---- verify the shortcut against task_success ------------------------
    verify = dict(checked=0, mismatches=0, max_abs_diff=0.0)
    if args.verify:
        for sc in scenes:
            for size in sizes[:1]:
                for search in searches[:1]:
                    for v in ["clean"] + sc["edited"]:
                        if v not in sc["renders"]:
                            continue
                        for i in range(min(2, sc["m"])):
                            corners = sc["corners"][size][i]
                            if not corners:
                                continue
                            dy, dx, pk, ok = sc["cache"][(size, search, v)][i]
                            for tol in tols:
                                for mp in peaks:
                                    mine = hits_from_deltas(dy, dx, pk, ok, tol, mp)
                                    ref = dtask.task_success(
                                        sc["renders"][v][i], sc["gt"][i], corners, size,
                                        tol=tol, min_peak=mp, search=search)
                                    ref_hits = int(round(ref["hit_rate"] * ref["n_patches"]))
                                    verify["checked"] += 1
                                    d = abs(mine - ref_hits)
                                    verify["max_abs_diff"] = max(verify["max_abs_diff"], d)
                                    if d:
                                        verify["mismatches"] += 1
        C.log(f"  verify vs calib.downstream_task.task_success: "
              f"{verify['checked']} cells, {verify['mismatches']} mismatches")
        if verify["mismatches"]:
            raise SystemExit("shortcut disagrees with task_success -- aborting")

    # ---- sweep -----------------------------------------------------------
    edited_all = list(scenes[0]["edited"])
    for sc in scenes[1:]:
        for v in sc["edited"]:
            if v not in edited_all:
                edited_all.append(v)
    coverage = coverage_reference(scenes, edited_all, args.n_splits, args.alpha, args.seed)
    per_config = []
    for size in sizes:
        for tol in tols:
            for mp in peaks:
                for search in searches:
                    row = dict(patch=size, tol=tol, min_peak=mp, search=search,
                               per_scene={})
                    pv_clean = {}
                    pv_edit = {}
                    for sc in scenes:
                        hcv = _scene_hit_per_view(sc, size, search, "clean", tol, mp)
                        if hcv.size == 0:
                            row["per_scene"][sc["name"]] = dict(hit_clean=None)
                            continue
                        pv_clean[sc["name"]] = hcv
                        entry = dict(hit_clean=float(hcv.mean()), n_views=int(hcv.size))
                        for v in edited_all:
                            if (size, search, v) not in sc["cache"]:
                                continue
                            hiv = _scene_hit_per_view(sc, size, search, v, tol, mp)
                            pv_edit[(v, sc["name"])] = hiv
                            entry[f"hit_{v}"] = float(hiv.mean())
                            entry[f"delta_{v}"] = float(hiv.mean() - hcv.mean())
                        row["per_scene"][sc["name"]] = entry
                    for v in edited_all:
                        pair_scenes = [s for s in pv_clean if (v, s) in pv_edit]
                        if not pair_scenes:
                            for k in ("hit_clean_", "hit_", "delta_", "delta_lo_",
                                      "delta_hi_", "degradation_pp_"):
                                row[f"{k}{v}"] = None
                            continue
                        cl = np.concatenate([pv_clean[s] for s in pair_scenes])
                        ed = np.concatenate([pv_edit[(v, s)] for s in pair_scenes])
                        pc, pe = float(cl.mean()), float(ed.mean())
                        row[f"hit_clean_{v}"] = pc
                        row[f"hit_{v}"] = pe
                        row[f"delta_{v}"] = pe - pc
                        row[f"degradation_pp_{v}"] = 100.0 * (pc - pe)
                        ci = C.paired_bootstrap_ci(cl, ed, n_boot=args.n_boot, seed=args.seed)
                        row[f"delta_lo_{v}"] = ci["lo"]
                        row[f"delta_hi_{v}"] = ci["hi"]
                        row[f"n_views_{v}"] = ci["n"]
                    per_config.append(row)

    # ---- pooled, per-variant summary over the whole grid ------------------
    edited = edited_all
    summary = {}
    for v in edited:
        hc = np.array([r[f"hit_clean_{v}"] for r in per_config if r.get(f"hit_clean_{v}") is not None])
        hv = np.array([r[f"hit_{v}"] for r in per_config if r.get(f"hit_{v}") is not None])
        dg = np.array([r[f"degradation_pp_{v}"] for r in per_config
                       if r.get(f"degradation_pp_{v}") is not None])
        summary[v] = dict(
            n_configs=int(dg.size),
            hit_clean_grid_mean=float(hc.mean()) if hc.size else None,
            hit_clean_grid_min=float(hc.min()) if hc.size else None,
            hit_clean_grid_max=float(hc.max()) if hc.size else None,
            hit_edited_grid_mean=float(hv.mean()) if hv.size else None,
            hit_edited_grid_min=float(hv.min()) if hv.size else None,
            hit_edited_grid_max=float(hv.max()) if hv.size else None,
            degradation_pp_grid_mean=float(dg.mean()) if dg.size else None,
            degradation_pp_grid_median=float(np.median(dg)) if dg.size else None,
            degradation_pp_grid_min=float(dg.min()) if dg.size else None,
            degradation_pp_grid_max=float(dg.max()) if dg.size else None,
            frac_configs_degraded_gt_0pp=float(np.mean(dg > 0)) if dg.size else None,
            frac_configs_degraded_gt_2pp=float(np.mean(dg > 2)) if dg.size else None,
        )

    cov_degr = {}
    for v in edited:
        vals = [coverage[s][v]["degradation_pp"] for s in coverage
                if v in coverage[s] and coverage[s][v]["degradation_pp"] is not None]
        cov_degr[v] = float(np.mean(vals)) if vals else None

    # ---- stability: task drop vs coverage drop, and variant ordering ------
    stab = dict(
        coverage_degradation_pp_by_variant=cov_degr,
        task_vs_coverage={},
        variant_ordering={},
    )
    for v in edited:
        if cov_degr.get(v) is None:
            continue
        dg = np.array([r[f"degradation_pp_{v}"] for r in per_config
                       if r.get(f"degradation_pp_{v}") is not None])
        if dg.size == 0:
            continue
        stab["task_vs_coverage"][v] = dict(
            coverage_degradation_pp=cov_degr[v],
            task_degradation_pp_mean=float(dg.mean()),
            frac_configs_task_gt_coverage=float(np.mean(dg > cov_degr[v])),
            n_configs=int(dg.size))
    versions = edited
    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            a, b = versions[i], versions[j]
            da = np.array([r[f"degradation_pp_{a}"] for r in per_config
                           if r.get(f"degradation_pp_{a}") is not None])
            db = np.array([r[f"degradation_pp_{b}"] for r in per_config
                           if r.get(f"degradation_pp_{b}") is not None])
            n = min(da.size, db.size)
            if n == 0:
                continue
            stab["variant_ordering"][f"{a}_worse_than_{b}"] = dict(
                frac_configs=float(np.mean(da[:n] > db[:n])), n_configs=int(n),
                coverage_worse=bool(cov_degr.get(a) is not None
                                    and cov_degr.get(b) is not None
                                    and cov_degr[a] > cov_degr[b]))
    # how often does the task ranking equal the ranking implied by coverage?
    if len(versions) > 1 and all(cov_degr.get(v) is not None for v in versions):
        cov_rank = {v: r for r, v in enumerate(sorted(versions, key=lambda v: -cov_degr[v]))}
        agree = []
        for r in per_config:
            dgs = {v: r.get(f"degradation_pp_{v}") for v in versions}
            if any(x is None for x in dgs.values()):
                continue
            task_rank = {v: k for k, v in
                         enumerate(sorted(versions, key=lambda v: -dgs[v]))}
            agree.append(all(task_rank[v] == cov_rank[v] for v in versions))
        stab["full_ranking_agreement"] = dict(
            frac_configs_exact_rank_match=float(np.mean(agree)) if agree else None,
            n_configs=int(len(agree)),
            coverage_rank={v: int(r) for v, r in cov_rank.items()})

    meta = dict(
        npz=[os.path.basename(f) for f in files],
        scenes=[sc["name"] for sc in scenes],
        variants=edited, grid=dict(sizes=sizes, tols=tols, peaks=peaks, searches=searches),
        n_patches_per_scene=int(args.n_patches),
        patches_per_view=int(max(1, int(np.ceil(args.n_patches / max(1, scenes[0]["m"]))))),
        alpha=float(args.alpha), n_splits=int(args.n_splits), seed=int(args.seed),
        n_boot=int(args.n_boot),
        matcher="research/code/calib/downstream_task.py (ncc_map/localise/task_success)",
        patch_source="ground-truth grey image (channel mean)",
        hit_rule="dy<=tol and dx<=tol and peak>=min_peak, search window "
                 "x0=max(0,x-search), x1=min(W,x+search+size)",
        delta_convention="delta = hit(edited) - hit(clean); degradation_pp = -100*delta; "
                         "delta_lo/hi = view-level cluster bootstrap of delta (paired)",
        verify=verify, generated=C.stamp(),
    )
    return dict(meta=meta, coverage_reference=coverage, variant_summary=summary,
                stability=stab, per_config=per_config)


def _scene_hit_per_view(sc, size, search, variant, tol, mp):
    """Per-view hit rates for one (size, search, variant, tol, peak) cell."""
    per_view = []
    for i in range(sc["m"]):
        dy, dx, pk, ok = sc["cache"][(size, search, variant)][i]
        n = ok.size
        if n == 0:
            continue
        per_view.append(hits_from_deltas(dy, dx, pk, ok, tol, mp) / n)
    return np.asarray(per_view, np.float64)


def _scene_hit_rate(sc, size, search, variant, tol, mp):
    """Mean over views of the per-view hit rate (view-level unit)."""
    v = _scene_hit_per_view(sc, size, search, variant, tol, mp)
    return float(v.mean()) if v.size else None


def main(argv=None):
    args = build_parser().parse_args(argv)
    t0 = time.time()
    res = run(args)
    res["meta"]["seconds"] = round(time.time() - t0, 1)
    C.json_dump(args.out, res)
    s = res["variant_summary"]
    C.log(f"[{C.stamp()}] WROTE {args.out} in {res['meta']['seconds']}s")
    for v, d in s.items():
        C.log(f"  {v:8s} hit_clean={d['hit_clean_grid_mean']:.3f} "
              f"hit_edited={d['hit_edited_grid_mean']:.3f} "
              f"degradation={d['degradation_pp_grid_mean']:+.1f}pp "
              f"[{d['degradation_pp_grid_min']:+.1f},{d['degradation_pp_grid_max']:+.1f}] "
              f"frac_configs_degraded> 0pp:{d['frac_configs_degraded_gt_0pp']:.2f} "
              f">2pp:{d['frac_configs_degraded_gt_2pp']:.2f}")
    C.log(f"  task-vs-coverage stability: "
          f"{json.dumps(res['stability']['task_vs_coverage'])[:400]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
