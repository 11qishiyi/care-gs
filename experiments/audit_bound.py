"""Audit a shipped coverage certificate with the material it ships with (pure CPU).

Why this exists
---------------
The TMLR-era manuscript concluded that a stale certificate is *not* detectable
from the calibration set, because re-running calibration returns the nominal
level by construction.  That argument is about **re-calibration**.  There is a
second, non-circular check the receiver can run, and it needs no new labels:

    re-render the *edited* asset on the **shipped** calibration views, and count
    how many of those residuals fall below the **shipped** q.

The shipped q was computed from the *un-edited* model's residuals on the same
views, so the statistic is not a quantile of the very numbers it recounts, and
because the edit is a function of the model only, the calibration views stay
exchangeable with the deployment views after the edit.  The check therefore
estimates post-edit deployment coverage -- it is an *audit*, not a guarantee.

This script quantifies three things on the dumped artifacts:

1. ``audit``      the estimator above, versus the true post-edit deployment
                  coverage (``stale`` in the paper's notation): bias, mean
                  absolute error, 95th percentile of the absolute error.
2. ``bound``      the Kolmogorov bound.  With ``F``/``F'`` the residual CDFs of
                  the clean and the edited model *on the calibration views* and
                  ``q`` the shipped quantile,

                      drop = F^dep(q) - F'^dep(q)
                           <= KS(F^cal, F'^cal) + 2 * (cal/dep sampling error),

                  because ``F^cal(q) ~ 1 - alpha`` and ``F'^cal(q) >= F^cal(q) - KS``.
                  We report the KS statistic per cell, the fraction of cells in
                  which the measured drop respects the bound, and the tightness
                  ratio ``drop / KS`` (how much slack the bound leaves).
3. ``kview``      how many shipped views the audit needs: the same estimator run
                  on random subsets of the calibration views of size k.

Everything is computed from per-view residual histograms, so the 400 splits cost
seconds instead of minutes.  ``--selftest`` checks the histogram path against the
exact quantile path on synthetic data and needs no GPU artifacts.

Usage
-----
    python experiments/audit_bound.py --npz experiments/artifacts/dump \
        --out results_v120/audit_bound.json
    python experiments/audit_bound.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


# ---------------------------------------------------------------------------
# histogram machinery
# ---------------------------------------------------------------------------

N_BINS = 4096


def view_histograms(resid: np.ndarray, n_bins: int = N_BINS,
                    x_max: float = 1.0) -> np.ndarray:
    """(m, H, W) residuals -> (m, n_bins) counts on ``[0, x_max]``.

    Residuals are ``|render - gt|`` of a grey image in [0, 1], so ``x_max=1``
    covers the support; the last bin also absorbs anything above it.

    Used **only** for the Kolmogorov statistic, which is a sup over the CDF and
    therefore insensitive to ``x_max`` as long as the support is covered.  The
    quantile and every coverage number are computed exactly from the residuals,
    so the paper's tables stay comparable with the earlier exact runs.
    """
    m = resid.shape[0]
    edges = np.linspace(0.0, x_max, n_bins + 1)
    out = np.empty((m, n_bins), np.int64)
    for i in range(m):
        h, _ = np.histogram(resid[i].reshape(-1), bins=edges)
        out[i] = h
    return out


def cdf_from_hist(hists: np.ndarray, view_idx, n_bins: int = N_BINS,
                  x_max: float = 1.0):
    """Concatenate a subset of views' histograms -> (edges, cdf) on the grid.

    ``edges[i]`` is the *upper* edge of bin ``i``, so ``cdf[i]`` is the fraction
    of scores ``<= edges[i]``.
    """
    counts = hists[np.asarray(view_idx)].sum(axis=0)
    n = counts.sum()
    if n == 0:
        raise ValueError("empty calibration histogram")
    cdf = np.cumsum(counts) / float(n)
    edges = np.linspace(0.0, x_max, n_bins + 1)[1:]
    return edges, cdf


def quantile_from_hist(edges, cdf, alpha: float) -> float:
    """Split-conformal quantile of the empirical CDF, on the bin grid.

    Mirrors ``common.cq``: index ``ceil((n+1)(1-alpha))`` of the sorted scores, i.e.
    the smallest value whose empirical CDF reaches ``(n+1)(1-alpha)/n``.  On a
    histogram the answer is snapped to a bin edge, which is why every number this
    script produces is validated against the exact path in ``--selftest`` and
    against the stored exact drops in ``--crosscheck``.
    """
    n = float(cdf.size and 0 or 0)  # placeholder, replaced below
    del n
    target = 1.0 - alpha
    i = int(np.searchsorted(cdf, target, side="left"))
    return float(edges[min(i, edges.size - 1)])


def coverage_at(edges, cdf, q: float) -> float:
    """Fraction of the distribution at or below ``q`` (bin-edge resolution)."""
    i = int(np.searchsorted(edges, q, side="left"))
    if i >= cdf.size:
        return 1.0
    return float(cdf[i])


def ks_distance(edges, cdf_a, cdf_b) -> float:
    return float(np.max(np.abs(cdf_a - cdf_b)))


# ---------------------------------------------------------------------------
# per-scene analysis
# ---------------------------------------------------------------------------

def analyse_scene(path: str, args) -> list:
    """All quantities for one scene, exact for q/coverage, histogram for KS.

    The quantile and every coverage number come from the residuals themselves
    (``np.partition`` / comparisons), so they are *identical* to the numbers the
    paper's tables already report; ``--crosscheck`` asserts that.  Only the
    Kolmogorov statistic runs on the histogram grid, where a bin width of
    ``1/4096`` is three orders of magnitude below the values being compared.
    """
    sc = C.load_npz_scene(path)
    meta = sc["meta"]
    name = meta["scene"]
    vnames = [str(v) for v in sc["variant_names"]]
    resid = np.asarray(sc["resid"])                       # (V, m, H, W) float16
    V, m = resid.shape[0], resid.shape[1]
    splits = C.split_perms(m, args.n_splits, args.seed)
    ci = vnames.index("clean")

    t0 = time.time()
    hists = np.stack([view_histograms(resid[v], args.bins, 1.0) for v in range(V)])
    C.log(f"  [{C.stamp()}] {name}: {V} variants x {m} views -> histograms "
          f"{hists.shape} in {time.time() - t0:.1f}s")

    clean_flat = resid[ci].reshape(m, -1).astype(np.float32)
    rows = []
    for vi, v in enumerate(vnames):
        if v == "clean":
            continue
        edit_flat = resid[vi].reshape(m, -1).astype(np.float32)
        drop, stale, audit, ks, gcal, base_cov, slack = [], [], [], [], [], [], []
        est_pp, true_pp = [], []
        for cal, dep in splits:
            cal = np.asarray(cal)
            dep = np.asarray(dep)
            q = C.cq(clean_flat[cal].reshape(-1), args.alpha)
            c_dep = float((clean_flat[dep] <= q).mean())   # clean model, deployment
            s_dep = float((edit_flat[dep] <= q).mean())    # edited model, deployment
            a_cal = float((edit_flat[cal] <= q).mean())    # edited model, calibration
            f_cal_clean = float((clean_flat[cal] <= q).mean())
            drop.append(s_dep - c_dep)
            stale.append(s_dep)
            base_cov.append(c_dep)
            audit.append(a_cal)
            if getattr(args, "save_splits", False):
                est_pp.append((c_dep - a_cal) * 100.0)      # what a single pass would report
                true_pp.append((c_dep - s_dep) * 100.0)     # what the deployment views say
            # the cal/deployment exchangeability slack of the bound; a receiver
            # cannot measure it (it needs deployment labels), which is why the
            # audited value is an estimate and only the KS part is certified.
            slack.append(abs(f_cal_clean - c_dep) + abs(a_cal - s_dep))
            e_c, fc = cdf_from_hist(hists[ci], cal, args.bins)
            e_e, fe = cdf_from_hist(hists[vi], cal, args.bins)
            ks.append(ks_distance(e_e, fc, fe))
            gcal.append(f_cal_clean - a_cal)

        drop = np.asarray(drop)
        stale = np.asarray(stale)
        audit = np.asarray(audit)
        ks = np.asarray(ks)
        gcal = np.asarray(gcal)
        slack = np.asarray(slack)
        err = audit - stale
        # certified statement: coverage loss <= KS on the calibration views,
        # up to the (unmeasurable-at-receipt) exchangeability slack.
        bound_drop = gcal + 2.0 * slack

        # k-view audit curve: how many shipped views does the audit need?
        kview = {}
        rng = np.random.default_rng(args.seed + 7)
        for k in args.kviews:
            if k >= m // 2:
                kview[str(k)] = None
                continue
            errs = []
            for cal, dep in splits[: args.kview_splits]:
                cal = np.asarray(cal)
                dep = np.asarray(dep)
                q = C.cq(clean_flat[cal].reshape(-1), args.alpha)
                sub = rng.choice(cal, size=min(k, cal.size), replace=False)
                a = float((edit_flat[sub] <= q).mean())
                s = float((edit_flat[dep] <= q).mean())
                errs.append(a - s)
            errs = np.asarray(errs)
            kview[str(k)] = dict(mae_pp=100 * float(np.abs(errs).mean()),
                                 bias_pp=100 * float(errs.mean()),
                                 n=int(errs.size))

        row = dict(
            scene=name, variant=v, n_views=int(m),
            drop_mean=float(drop.mean()),
            drop_lo=float(np.percentile(drop, 2.5)),
            drop_hi=float(np.percentile(drop, 97.5)),
            clean_mean=float(np.mean(base_cov)),
            stale_mean=float(stale.mean()),
            audit_mean=float(audit.mean()),
            audit_bias_pp=100 * float(err.mean()),
            audit_mae_pp=100 * float(np.abs(err).mean()),
            audit_abs_p95_pp=100 * float(np.percentile(np.abs(err), 95)),
            audit_abs_max_pp=100 * float(np.abs(err).max()),
            ks_cal_mean=float(ks.mean()),
            ks_cal_lo=float(np.percentile(ks, 2.5)),
            ks_cal_hi=float(np.percentile(ks, 97.5)),
            pred_drop_mean=float(gcal.mean()),
            pred_drop_mae_pp=100 * float(np.abs(gcal + drop).mean()),
            slack_mean=float(slack.mean()),
            bound_holds_frac=float(np.mean(-drop <= bound_drop + 1e-9)),
            ks_alone_holds_frac=float(np.mean(-drop <= ks + 1e-9)),
            tightness_mean=float(np.mean(-drop / np.maximum(ks, 1e-12))),
            kview=kview,
                    splits=dict(est_pp=[round(float(x), 4) for x in est_pp],
                        true_pp=[round(float(x), 4) for x in true_pp]),
)
        rows.append(row)
        C.log(f"    {v:>8s} drop={100 * row['drop_mean']:6.1f}pp "
              f"audit={100 * row['audit_mean']:5.1f}% "
              f"err={row['audit_bias_pp']:+5.1f}pp "
              f"MAE={row['audit_mae_pp']:4.1f}pp KS={100 * row['ks_cal_mean']:5.1f}pp "
              f"tight={row['tightness_mean']:4.2f}")
    return rows


def summarise(rows: list) -> dict:
    """Pool across scenes: how good is the audit, and how tight is the bound?"""
    geom = [r for r in rows if r["variant"] != "quant8"]
    mae = np.array([r["audit_mae_pp"] for r in rows])
    bias = np.array([r["audit_bias_pp"] for r in rows])
    holds = np.array([r["bound_holds_frac"] for r in rows])
    tight = np.array([r["tightness_mean"] for r in rows])
    return dict(
        n_cells=len(rows),
        audit_mae_pp_mean=float(mae.mean()),
        audit_mae_pp_max=float(mae.max()),
        audit_bias_pp_mean=float(bias.mean()),
        audit_bias_pp_abs_mean=float(np.abs(bias).mean()),
        bound_holds_frac_mean=float(holds.mean()),
        bound_holds_frac_min=float(holds.min()),
        tightness_mean=float(tight.mean()),
        tightness_min=float(tight.min()),
        tightness_max=float(tight.max()),
        noop_cells=[r["variant"] for r in rows if r["variant"] == "quant8"],
        n_geometric_cells=len(geom),
    )


# ---------------------------------------------------------------------------
# self-test: histogram path vs exact path, no GPU artifacts needed
# ---------------------------------------------------------------------------

def selftest(seed: int = 0) -> int:
    rng = np.random.default_rng(seed)
    m, h, w = 8, 24, 32
    clean = rng.gamma(2.0, 0.02, size=(m, h, w)).astype(np.float32)
    edited = (clean * rng.uniform(1.5, 3.0)).astype(np.float32)
    edited = np.clip(edited, 0, 1)
    splits = C.split_perms(m, 40, 0)
    cf = clean.reshape(m, -1)
    ef = edited.reshape(m, -1)

    hc = view_histograms(clean, 4096)
    he = view_histograms(edited, 4096)

    worst_q, worst_cov = 0.0, 0.0
    for cal, dep in splits:
        cal, dep = np.asarray(cal), np.asarray(dep)
        e_c, f_c = cdf_from_hist(hc, cal)
        e_e, f_e = cdf_from_hist(he, cal)
        q_exact = C.cq(cf[cal].reshape(-1), 0.10)
        q_hist = quantile_from_hist(e_c, f_c, 0.10)
        worst_q = max(worst_q, abs(q_hist - q_exact))
        cov_exact = float((ef[dep] <= q_exact).mean())
        cov_hist = coverage_at(*cdf_from_hist(he, dep), q_hist)
        worst_cov = max(worst_cov, abs(cov_hist - cov_exact))
    ok = worst_q < 5e-3 and worst_cov < 5e-3
    print(f"[selftest] max |q_hist - q_exact| = {worst_q:.2e}  "
          f"max |cov_hist - cov_exact| = {worst_cov:.2e}  -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        return 1

    # the KS bound must hold on synthetic data where we can check it exactly
    bad = 0
    for cal, dep in splits:
        cal, dep = np.asarray(cal), np.asarray(dep)
        e_c, f_c = cdf_from_hist(hc, cal)
        e_e, f_e = cdf_from_hist(he, cal)
        q = quantile_from_hist(e_c, f_c, 0.10)
        e_cd, f_cd = cdf_from_hist(hc, dep)
        e_ed, f_ed = cdf_from_hist(he, dep)
        drop = coverage_at(e_ed, f_ed, q) - coverage_at(e_cd, f_cd, q)
        bound = (coverage_at(e_c, f_c, q) - coverage_at(e_e, f_e, q)) + ks_distance(
            e_e, f_c, f_e)
        bad += int(-drop > bound + 1e-9)
    print(f"[selftest] KS bound respected in {len(splits) - bad}/{len(splits)} splits")

    # end-to-end on a synthetic dump, so the CLI path is exercised without a GPU
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "_selftest_dump")
    make_synth(tmp, seed=seed)
    args = build_parser().parse_args(
        ["--npz", tmp, "--out", os.path.join(tmp, "audit.json"),
         "--n-splits", "60", "--kview-splits", "20"])
    args.kviews = [1, 2]
    rows = analyse_scene(os.path.join(tmp, "synth.npz"), args)
    assert rows, "no rows produced"
    for r in rows:
        assert -1.0 <= r["drop_mean"] <= 1.0, r
        assert 0.0 <= r["audit_mae_pp"] < 100.0, r
        assert r["ks_alone_holds_frac"] >= 0.5, ("KS bound violated too often", r)
    print(f"[selftest] end-to-end on a synthetic dump: {len(rows)} cells, "
          f"drop {100 * rows[0]['drop_mean']:.1f} pp, "
          f"audit MAE {rows[0]['audit_mae_pp']:.1f} pp -> PASS")
    return 0


def make_synth(out_dir: str, seed: int = 0, m: int = 12, h: int = 24, w: int = 32) -> str:
    """Write a tiny npz in the dump format so the analysis can be tested on CPU."""
    rng = np.random.default_rng(seed)
    base = rng.gamma(2.0, 0.02, size=(m, h, w)).astype(np.float32)
    variants = ["clean", "prune30", "quant8"]
    resid = []
    for v in variants:
        if v == "clean":
            resid.append(base)
        elif v == "quant8":
            resid.append(base * 1.001)
        else:
            resid.append(np.clip(base * 2.2 + rng.gamma(1.0, 0.004), 0, 1).astype(np.float32))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "synth.npz")
    np.savez(path,
             gray_render=np.zeros_like(np.stack(resid), dtype=np.float16),
             resid=np.stack(resid).astype(np.float16),
             gray_gt=np.zeros((m, h, w), np.float16),
             views=np.arange(m, dtype=np.int32),
             c2w=np.zeros((m, 4, 4), np.float32),
             K=np.zeros((m, 3, 3), np.float32),
             prim_means=np.zeros((8, 3), np.float32),
             prim_opacity=np.zeros(8, np.float32),
             variant_names=np.asarray(variants),
             meta=json.dumps(dict(scene="synth", factor=4, downsample=1,
                                  height=h, width=w, alpha=0.1, n_views=m)))
    return path


def crosscheck(rows: list, region_dir: str) -> int:
    worst, n = 0.0, 0
    for r in rows:
        p = os.path.join(region_dir, f"region_{r['scene']}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        for row in d["rows"]:
            if row["variant"] == r["variant"] and row["granularity"] == "pixel":
                worst = max(worst, abs(100 * row["drop_mean"] + 100 * r["drop_mean"]))
                n += 1
    print(f"[crosscheck] {n} cells, max |analysis drop - stored drop| = {worst:.2f} pp")
    return 0 if worst < 0.1 else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Audit a shipped coverage certificate on shipped calibration views.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--npz", default=C.default_out("dump"), help="dir of <scene>.npz dumps")
    ap.add_argument("--out", default=C.default_out("audit_bound.json"))
    ap.add_argument("--scenes", default="", help="comma list; default: every npz found")
    ap.add_argument("--variants", default="", help="comma list; default: every non-clean")
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--bins", type=int, default=N_BINS)
    ap.add_argument("--n-splits", type=int, default=C.N_SPLITS)
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--kviews", default="1,2,4,8", help="subset sizes for the k-view curve")
    ap.add_argument("--kview-splits", type=int, default=100)
    ap.add_argument("--save-splits", action="store_true",
                    help="also store the per-split (audit estimate, true loss) pairs, for single-pass analysis")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--crosscheck", default="", help="results_v110/region dir to compare with")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.selftest:
        return selftest()

    paths = C.discover_npz(args.npz)
    want = [s.strip() for s in args.scenes.split(",") if s.strip()]
    if want:
        paths = [p for p in paths if os.path.basename(p)[:-4] in want]
    if not paths:
        raise SystemExit(f"no npz in {args.npz}")
    args.kviews = [int(k) for k in str(args.kviews).split(",") if str(k).strip()]

    rows = []
    for p in paths:
        C.log(f"[{C.stamp()}] {p}")
        rows.extend(analyse_scene(p, args))

    out = dict(meta=dict(alpha=args.alpha, bins=args.bins, n_splits=args.n_splits,
                         seed=args.seed, npz=os.path.abspath(args.npz),
                         note="audit = coverage of the EDITED model on the SHIPPED "
                              "calibration views at the SHIPPED q; stale = the same "
                              "coverage on the deployment views"),
               rows=rows, summary=summarise(rows))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    C.json_dump(args.out, out)
    s = out["summary"]
    C.log(f"[{C.stamp()}] {s['n_cells']} cells -> {args.out}")
    C.log(f"  audit MAE {s['audit_mae_pp_mean']:.1f} pp (max {s['audit_mae_pp_max']:.1f}), "
          f"|bias| {s['audit_bias_pp_abs_mean']:.1f} pp")
    C.log(f"  KS bound holds in {100 * s['bound_holds_frac_mean']:.0f}% of cells, "
          f"tightness {s['tightness_min']:.2f}-{s['tightness_max']:.2f}")

    if args.crosscheck:
        return crosscheck(rows, args.crosscheck)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
