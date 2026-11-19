"""Build the PUP / Fisher-pruned 30 % PLY that ``dump_artifacts.py`` renders (GPU).

PUP 3D-GS ranks primitives by the diagonal of the Hessian of the photometric
loss and deletes the ones that matter least.  ``calib/sensitivity.py`` already
implements that score for this code base (squared accumulated gradient of the
L1 loss over a handful of calibration views), so this script is only the
bookkeeping around it:

    score_i = sum_p ( dL / d theta_{i,p} )^2      accumulated over N cal views
    keep    = the top ``ratio`` fraction by score
    write   = an INRIA-format PLY (log scales / logit opacities, channel-major
              f_rest) that ``calib.gsrender.load_splats`` reads back unchanged.

Important: the score is computed on **calibration views only** (``cal_idx``), so
the deployment views used by every coverage number in the paper are never seen
by the pruner.  The pruning decision therefore transfers to held-out views
legitimately.

``--dry-run`` exercises ranking + PLY writing + read-back on synthetic arrays with
numpy only (no torch), which is how this script is validated on the workstation.

Usage on the node
-----------------
    python experiments/make_pup_variant.py --archive /workspace/data/out3dgs \
        --out-dir /workspace/data/rev_dump/pup --device cuda
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="PUP/Fisher top-30%% pruning -> INRIA PLY (GPU).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="flowers,bicycle,treehill,stump")
    ap.add_argument("--out-dir", default=C.default_out("dump/pup"))
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--ratio", type=float, default=0.3, help="fraction of primitives to keep")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--n-views", type=int, default=4,
                    help="number of calibration views used to accumulate the score"
                         " (PUP paper uses 6; 4 keeps the backward pass small)")
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the load_splats() read-back check of the written PLY")
    ap.add_argument("--dry-run", action="store_true",
                    help="synthetic arrays, numpy only: validates ranking + PLY round-trip")
    ap.add_argument("--dry-run-prims", type=int, default=5000)
    ap.add_argument("--dry-run-out", default=None,
                    help="dry-run output dir (default <out-dir>/dryrun)")
    return ap


# ---------------------------------------------------------------------------
# ranking + summary (shared by the real and the dry path)
# ---------------------------------------------------------------------------


def rankdata(x: np.ndarray) -> np.ndarray:
    """Tie-averaged ranks (1..n), scipy-free."""
    x = np.asarray(x, np.float64)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, np.float64)
    ranks[order] = np.arange(x.size, dtype=np.float64)
    sx = x[order]
    # average ties
    i = 0
    while i < x.size:
        j = i + 1
        while j < x.size and sx[j] == sx[i]:
            j += 1
        if j - i > 1:
            ranks[order[i:j]] = ranks[order[i:j]].mean()
        i = j
    return ranks


def spearman(a, b) -> float:
    ra, rb = rankdata(a), rankdata(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    den = float(np.sqrt((ra ** 2).sum() * (rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else 0.0


def topk_keep(scores: np.ndarray, ratio: float) -> np.ndarray:
    """Indices (sorted ascending) of the top ``ratio`` fraction by score."""
    n = scores.size
    k = max(1, min(n, int(round(ratio * n))))
    keep = np.argsort(-np.asarray(scores, np.float64), kind="stable")[:k]
    return np.sort(keep)


def rank_summary(scores, opacity, keep, ratio: float, n_total: int) -> dict:
    """Rank correlation between the Fisher order and the opacity order."""
    keep_mask = np.zeros(n_total, bool)
    keep_mask[keep] = True
    op_keep = topk_keep(opacity, ratio)
    op_mask = np.zeros(n_total, bool)
    op_mask[op_keep] = True
    inter = int(np.sum(keep_mask & op_mask))
    union = int(np.sum(keep_mask | op_mask))
    return dict(
        ratio=float(ratio), n_primitives=int(n_total), n_kept=int(keep.size),
        spearman_fisher_vs_opacity=spearman(scores, opacity),
        topk_overlap=dict(same_keep=int(inter), jaccard=float(inter / max(union, 1)),
                          frac_of_kept=float(inter / max(int(keep.size), 1))),
        fisher=dict(mean=float(np.mean(scores)), median=float(np.median(scores)),
                    p10=float(np.percentile(scores, 10)),
                    p90=float(np.percentile(scores, 90)),
                    max=float(np.max(scores))),
        opacity_kept_mean=float(np.mean(opacity[keep])),
        opacity_dropped_mean=float(np.mean(opacity[~keep_mask])) if n_total > keep.size else None,
        fisher_kept_frac_of_total_score=float(np.sum(scores[keep]) / max(np.sum(scores), 1e-12)),
    )


def write_variant_ply(path, splats_dict, keep, ratio: float) -> str:
    """Slice the *on-disk* attribute dict and write a standard INRIA PLY."""
    out = dict(
        means=np.asarray(splats_dict["means"])[keep],
        scales=np.asarray(splats_dict["scales"])[keep],        # log scales on disk
        quats=np.asarray(splats_dict["quats"])[keep],
        opacities=np.asarray(splats_dict["opacities"])[keep],  # logit on disk
        sh0=np.asarray(splats_dict["sh0"])[keep],
        shN=np.asarray(splats_dict["shN"])[keep],
    )
    return C.write_inria_ply(path, comment=f"pup top-{ratio:.2f} (n={len(keep)})", **out)


# ---------------------------------------------------------------------------
# real (GPU) path
# ---------------------------------------------------------------------------


def run_real(args) -> dict:
    C.add_code_root()
    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images, normalize_exposure
    from calib.gsrender import load_splats
    from calib.sensitivity import sensitivity_scores

    torch.manual_seed(args.seed)
    os.makedirs(args.out_dir, exist_ok=True)
    rows = []
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        t0 = time.time()
        ply = args.ply_pattern.format(archive=args.archive, scene=scene)
        sp = load_splats(ply, device=args.device)
        C.log(f"[{C.stamp()}] === {scene}: {sp.n} primitives <- {ply}")

        sc = load_archive_only_scene(args.archive, scene, factor=args.factor,
                                     cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        gt = torch.from_numpy(normalize_exposure(
            load_images(sc["image_paths"], args.factor, (W, H)))).float().to(args.device)
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        cal = [int(i) for i in sc["cal_idx"]]
        if not cal:
            raise RuntimeError("archive scene has no calibration views")

        t1 = time.time()
        scores = sensitivity_scores(sp, c2w, K, gt, cal, W, H,
                                    n_views=args.n_views, device=args.device)
        scores_np = scores.detach().float().cpu().numpy()
        opac_np = sp.opacities.detach().float().cpu().numpy()
        C.log(f"  Fisher scores over {min(args.n_views, len(cal))} cal views in "
              f"{time.time() - t1:.1f}s; mean={scores_np.mean():.3e} "
              f"p90={np.percentile(scores_np, 90):.3e}")

        keep = topk_keep(scores_np, args.ratio)
        path = os.path.join(args.out_dir, f"{scene}_pup{int(round(args.ratio * 100))}.ply")

        # slice the *raw on-disk* attributes, so the writer never re-derives them
        p = np.clip(sp.opacities.detach().cpu().numpy(), 1e-6, 1 - 1e-6)
        d = dict(
            means=sp.means.detach().cpu().numpy(),
            scales=np.log(sp.scales.detach().cpu().numpy().clip(1e-8)),
            quats=sp.quats.detach().cpu().numpy(),
            opacities=np.log(p / (1.0 - p)),
            sh0=sp.sh0.detach().cpu().numpy(),
            shN=sp.shN.detach().cpu().numpy(),
        )
        write_variant_ply(path, d, keep, args.ratio)
        C.log(f"  wrote {path} ({C.sizeof_fmt(os.path.getsize(path))})")

        row = rank_summary(scores_np, opac_np, keep, args.ratio, sp.n)
        row.update(scene=scene, ply=path, ply_bytes=int(os.path.getsize(path)),
                   n_views_scored=int(min(args.n_views, len(cal))),
                   seconds=round(time.time() - t0, 1))

        if not args.no_verify:
            back = load_splats(path, device="cpu")
            ok_n = back.n == keep.size
            ok_m = bool(np.allclose(back.means.detach().cpu().numpy(),
                                    d["means"][keep], atol=1e-6))
            ok_o = bool(np.allclose(back.opacities.detach().cpu().numpy(),
                                    sp.opacities.detach().cpu().numpy()[keep], atol=1e-6))
            row["verify"] = dict(n_ok=bool(ok_n), means_ok=ok_m, opacity_ok=ok_o)
            if not (ok_n and ok_m and ok_o):
                raise RuntimeError(f"PLY round-trip failed for {path}: {row['verify']}")
            C.log(f"  read-back verified: n={back.n}, means/opacities identical")
        rows.append(row)
        del sp, d

    summary = dict(dry_run=False, archive=args.archive, ratio=float(args.ratio),
                   n_views=int(args.n_views), factor=int(args.factor),
                   seed=int(args.seed), scenes=rows)
    out = os.path.join(args.out_dir, "pup_summary.json")
    C.json_dump(out, summary)
    C.log(f"[{C.stamp()}] WROTE {out}")
    return summary


# ---------------------------------------------------------------------------
# dry run (CPU, synthetic)
# ---------------------------------------------------------------------------


def run_dry(args) -> dict:
    rng = np.random.default_rng(args.seed)
    out_dir = args.dry_run_out or os.path.join(args.out_dir, "dryrun")
    os.makedirs(out_dir, exist_ok=True)
    n = int(args.dry_run_prims)
    # synthetic INRIA asset with the same attribute layout as a real checkpoint
    logit_o = rng.normal(0.5, 2.0, size=n).astype(np.float32)
    opacity = 1.0 / (1.0 + np.exp(-logit_o))
    shN = rng.normal(scale=0.1, size=(n, 3, 3)).astype(np.float32)     # SH degree 2
    d = dict(
        means=rng.normal(size=(n, 3)).astype(np.float32),
        scales=np.log(rng.uniform(0.002, 0.05, size=(n, 3))).astype(np.float32),
        quats=rng.normal(size=(n, 4)).astype(np.float32),
        opacities=logit_o,
        sh0=rng.normal(scale=0.5, size=(n, 1, 3)).astype(np.float32),
        shN=shN,
    )
    # synthetic Fisher score: correlated with opacity but far from identical
    scores = (0.6 * logit_o + rng.normal(scale=1.0, size=n)).astype(np.float32)
    keep = topk_keep(scores, args.ratio)
    scenename = "dryrun_pup"
    path = os.path.join(out_dir, f"{scenename}_pup{int(round(args.ratio * 100))}.ply")
    write_variant_ply(path, d, keep, args.ratio)

    # read back with the same reader dump_artifacts' loader uses (calib.plyio when
    # plyfile is absent -> we validate with our numpy reader, which parses the
    # identical property layout)
    back = C.read_inria_ply(path)
    assert back["n"] == keep.size, (back["n"], keep.size)
    assert np.allclose(back["means"], d["means"][keep], atol=1e-5)
    assert np.allclose(back["opacities"], d["opacities"][keep], atol=1e-5)
    assert back["shN"].shape == (keep.size, 3, 3), back["shN"].shape
    assert np.allclose(back["shN"], d["shN"][keep], atol=1e-5)

    row = rank_summary(scores, opacity, keep, args.ratio, n)
    row.update(scene=scenename, ply=path, ply_bytes=int(os.path.getsize(path)),
               n_views_scored=0, seconds=0.0,
               verify=dict(n_ok=True, means_ok=True, opacity_ok=True,
                           reader="experiments/common.read_inria_ply (numpy)"))
    C.log(f"  dry {scenename}: {n} -> {keep.size} primitives, "
          f"spearman(fisher,opacity)={row['spearman_fisher_vs_opacity']:+.3f}, "
          f"jaccard(topk)={row['topk_overlap']['jaccard']:.3f}, "
          f"wrote {C.sizeof_fmt(row['ply_bytes'])}")
    summary = dict(dry_run=True,
                   note="SYNTHETIC arrays: validates ranking, PLY writer and read-back; "
                        "the Fisher/gsplat path is GPU-only and NOT exercised here",
                   ratio=float(args.ratio), n_views=int(args.n_views),
                   seed=int(args.seed), scenes=[row])
    out = os.path.join(out_dir, "pup_summary.json")
    C.json_dump(out, summary)
    C.log(f"[{C.stamp()}] DRY-RUN WROTE {out}")
    return summary


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.dry_run:
        run_dry(args)
    else:
        run_real(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
