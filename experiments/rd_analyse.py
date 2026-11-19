"""A4 analysis (pure CPU): matched-bytes comparison of the edit families.

Reads the ``<scene>.npz`` + ``rd_manifest.json`` written by ``rate_distortion.py``
and answers the two registered questions by *interpolating every family's
rate--distortion curve onto the same byte rates*:

    C1  at matched bytes, is the coverage loss of the best non-prune family
        (quant / joint / allocator) smaller than the Fisher-prune family's?
    C2  inside the allocator's action space, does the tail-weighted allocation
        beat the visibility-weighted one?

Both are paired by the 400 calibration/deployment splits of ``common.py``: the
interpolation is done *per split*, so the difference is a paired statistic and
the 2.5/97.5 percentiles are honest intervals rather than a spread of means.

Protocol (identical to ``audit_bound.py``, which the paper's tables come from):
``q`` = split-conformal quantile of the CLEAN residual on the split's calibration
views; ``drop`` = coverage(edited, deployment) - coverage(clean, deployment).

Usage
-----
    python experiments/rd_analyse.py --npz /workspace/res/a4/dump \
        --out /workspace/res/a4/rd.json --rates 2.0,2.5,3.0,3.5,4.0
    python experiments/rd_analyse.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

FAMILIES = ("prune", "quant", "joint", "alloc_mse", "alloc_tail")
NONPRUNE = ("quant", "joint", "alloc_mse", "alloc_tail")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def family_of(name: str) -> str:
    """Variant name -> family label (kept local so the analysis never needs torch)."""
    if name == "clean":
        return "clean"
    if name.startswith("am"):
        return "alloc_mse"
    if name.startswith("at"):
        return "alloc_tail"
    if name.startswith("p") and "_q" in name:
        return "joint"
    if name.startswith("p"):
        return "prune"
    if name.startswith("q"):
        return "quant"
    return "other"


def spec_bytes_per_prim(name: str, sh_degree: int = 3) -> float:
    """Byte accounting, duplicated from ``rate_distortion`` (numpy-only path).

    Duplicated on purpose: the analysis must run on the workstation without
    torch, and the formula is two lines.  ``rate_distortion.selftest`` asserts
    the two agree through the synthetic dump.
    """
    fixed, cols = 44.0, 3 * (sh_degree + 1) ** 2
    fp32 = fixed + cols * 32 / 8
    if name == "clean":
        return fp32
    if name.startswith("am") or name.startswith("at"):
        return fp32 / float(name[2:])
    if name.startswith("p") and "_q" in name:
        keep_s, bits_s = name[1:].split("_q", 1)
        return float(keep_s) / 100.0 * (fixed + cols * int(bits_s) / 8)
    if name.startswith("p"):
        return float(name[1:]) / 100.0 * fp32
    if name.startswith("q"):
        return fixed + cols * int(name[1:]) / 8
    raise ValueError(name)


def _load_manifest(dump_dir: str) -> dict | None:
    p = os.path.join(dump_dir, "rd_manifest.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _scene_meta(manifest: dict | None, scene: str) -> dict:
    if not manifest:
        return {}
    for row in manifest.get("scenes", []):
        if row.get("scene") == scene:
            return row
    return {}


def per_split_drops(resid: np.ndarray, splits, alpha: float) -> dict:
    """{variant: (n_splits,) drop array}; drop<0 means the edit hurt coverage."""
    V, m = resid.shape[0], resid.shape[1]
    flat = resid.reshape(V, m, -1).astype(np.float32)
    names = None
    out = {}
    clean = flat[0] if V else None
    qs = []
    for cal, dep in splits:
        cal, dep = np.asarray(cal), np.asarray(dep)
        q = C.cq(clean[cal].reshape(-1), alpha)
        qs.append(q)
        base_cov = float((clean[dep] <= q).mean())
        out.setdefault("clean", []).append(base_cov)
    return qs, out


def variant_drops(resid: np.ndarray, names, splits, alpha: float):
    """{(variant): per-split drop} plus the clean coverage per split.

    The protocol is ``audit_bound.py``'s, exactly: per split, ``q`` is the
    split-conformal quantile of the CLEAN residuals on the calibration views and
    ``drop = coverage(edited, deployment) - coverage(clean, deployment)``.

    Coverage is evaluated through the sorted residual of each (variant, view)
    rather than as a full boolean array: over 32 variants x 400 splits the naive
    form compares ~1.5e11 elements, while ``searchsorted`` does the same work in
    ~1e5 binary searches and is exact (``side='right'`` == ``x <= q``).
    """
    V, m = resid.shape[0], resid.shape[1]
    P = int(np.prod(resid.shape[2:]))
    flat = resid.reshape(V, m, P)
    srt = np.empty((V, m, P), dtype=np.float32)
    for v in range(V):
        for k in range(m):
            srt[v, k] = np.sort(flat[v, k].astype(np.float32))
    ci = list(names).index("clean")
    qs, clean_cov, drops = [], [], {n: [] for n in names if n != "clean"}
    for cal, dep in splits:
        cal, dep = list(np.asarray(cal)), list(np.asarray(dep))
        pooled = np.concatenate([flat[ci, k] for k in cal]).astype(np.float32)
        q = C.cq(pooled, alpha)
        del pooled
        qs.append(q)
        base_cov = float(np.mean([np.searchsorted(srt[ci, k], q, side="right")
                                  for k in dep])) / P
        clean_cov.append(base_cov)
        for vi, n in enumerate(names):
            if n == "clean":
                continue
            cov = float(np.mean([np.searchsorted(srt[vi, k], q, side="right")
                                 for k in dep])) / P
            drops[n].append(cov - base_cov)
    return ({n: np.asarray(v) for n, v in drops.items()},
            np.asarray(clean_cov), np.asarray(qs), np.asarray([float(x) for x in qs]))


def interp_family(points, target: float):
    """Linear interpolation of per-split drops onto ``target`` bytes/primitive.

    ``points`` is a list of ``(rate, drop_vector)``; returns ``(values, covered)``
    where ``covered`` says whether ``target`` lies inside the family's rate range
    (no extrapolation is ever used for a registered comparison).
    """
    pts = sorted(points, key=lambda t: t[0])
    if len(pts) < 2:
        return None, False
    xs = np.asarray([p[0] for p in pts], dtype=np.float64)
    ys = np.stack([p[1] for p in pts], axis=0)                # (K, n_splits)
    covered = bool(xs.min() - 1e-9 <= target <= xs.max() + 1e-9)
    at = np.empty(ys.shape[1])
    for s in range(ys.shape[1]):
        at[s] = float(np.interp(target, xs, ys[:, s]))
    return at, covered


# ---------------------------------------------------------------------------
# main analysis
# ---------------------------------------------------------------------------


def analyse_dump(dump_dir: str, rates=(2.0, 2.5, 3.0, 3.5, 4.0),
                 n_splits: int = C.N_SPLITS, alpha: float = C.ALPHA,
                 verbose: bool = True, seed: int = C.RNG_SEED) -> dict:
    manifest = _load_manifest(dump_dir)
    paths = C.discover_npz(dump_dir)
    if not paths:
        raise SystemExit(f"no npz in {dump_dir}")

    scenes, pooled = [], {r: {"c1": [], "c2": []} for r in rates}
    for path in paths:
        sc = C.load_npz_scene(path)
        meta = sc["meta"]
        scene = meta.get("scene", os.path.basename(path)[:-4])
        names = [str(v) for v in sc["variant_names"]]
        sh_deg = int(meta.get("sh_degree", 3) or 3)
        resid = np.asarray(sc["resid"])
        m = resid.shape[1]
        splits = C.split_perms(m, n_splits, seed)
        drops, clean_cov, qs, qarr = variant_drops(resid, names, splits, alpha)
        row_meta = _scene_meta(manifest, scene)

        rows = []
        fam_points = {f: [] for f in FAMILIES}
        for name in names:
            fam = family_of(name)
            if fam == "clean":
                continue
            vmeta = (row_meta.get("variants") or {}).get(name) or {}
            bpp = vmeta.get("bytes_per_prim")
            if bpp is None:
                bpp = spec_bytes_per_prim(name, sh_deg)
            rate_x = 236.0 / float(bpp) if sh_deg != 3 else (
                (44.0 + 3 * (sh_deg + 1) ** 2 * 4) / float(bpp))
            d = drops[name]
            rows.append(dict(variant=name, family=fam, bytes_per_prim=float(bpp),
                             rate=float(rate_x),
                             drop_mean=float(d.mean()),
                             drop_lo=float(np.percentile(d, 2.5)),
                             drop_hi=float(np.percentile(d, 97.5)),
                             drop_pp=100.0 * float(d.mean()),
                             psnr=vmeta.get("psnr")))
            if fam in fam_points:
                fam_points[fam].append((float(rate_x), d))

        matched, comp = {}, {}
        for r in rates:
            matched[str(r)] = {}
            vals = {}
            for fam, pts in fam_points.items():
                v, ok = interp_family(pts, r)
                if v is None:
                    continue
                vals[fam] = (v, ok)
                matched[str(r)][fam] = dict(
                    drop_pp=100.0 * float(v.mean()),
                    lo_pp=100.0 * float(np.percentile(v, 2.5)),
                    hi_pp=100.0 * float(np.percentile(v, 97.5)),
                    covered=bool(ok))
            if "prune" not in vals:
                continue
            pr, pr_ok = vals["prune"]
            cand = [(f, vals[f]) for f in NONPRUNE if f in vals and vals[f][1]]
            if pr_ok and cand:
                best = np.stack([v for _f, (v, _o) in cand], axis=0).max(axis=0)
                diff = best - pr                       # >0: non-prune loses less
                comp.setdefault(str(r), {})["best_nonprune_minus_prune"] = dict(
                    mean_pp=100.0 * float(diff.mean()),
                    lo_pp=100.0 * float(np.percentile(diff, 2.5)),
                    hi_pp=100.0 * float(np.percentile(diff, 97.5)),
                    n_splits=int(diff.size))
                pooled[r]["c1"].append(100.0 * float(diff.mean()))
            if ("alloc_tail" in vals) and ("alloc_mse" in vals):
                (va, oka), (vt, okt) = vals["alloc_mse"], vals["alloc_tail"]
                if oka and okt:
                    diff = vt - va                     # >0: tail weighting helps
                    comp.setdefault(str(r), {})["tail_minus_mse"] = dict(
                        mean_pp=100.0 * float(diff.mean()),
                        lo_pp=100.0 * float(np.percentile(diff, 2.5)),
                        hi_pp=100.0 * float(np.percentile(diff, 97.5)),
                        n_splits=int(diff.size))
                    pooled[r]["c2"].append(100.0 * float(diff.mean()))

        scenes.append(dict(scene=scene, sh_degree=sh_deg, n_views=int(m),
                           clean_coverage=float(clean_cov.mean()),
                           q_mean=float(qarr.mean()), rows=rows,
                           matched=matched, comparisons=comp))
        if verbose:
            C.log(f"  [{C.stamp()}] {scene}: clean cov {100 * clean_cov.mean():.1f}% "
                  f"at q={qarr.mean():.4f}, {len(rows)} variants")
            for name in [n for n in names if n != "clean"]:
                r = next(x for x in rows if x["variant"] == name)
                C.log(f"    {name:>8s} {r['rate']:5.2f}x drop={r['drop_pp']:6.1f}pp "
                      f"[{100 * r['drop_lo']:6.1f},{100 * r['drop_hi']:6.1f}] "
                      f"PSNR={r['psnr'] if r['psnr'] is None else round(r['psnr'], 2)}")
            for r in rates:
                c = comp.get(str(r), {})
                b = c.get("best_nonprune_minus_prune")
                t = c.get("tail_minus_mse")
                # a rate outside the prune family's span (p30 is the floor at
                # 3.33x) has no C1 comparison; say so instead of printing None
                s1 = (f"C1 {b['mean_pp']:+6.1f}pp [{b['lo_pp']:+5.1f},{b['hi_pp']:+5.1f}]"
                      if b else "C1 not covered     ")
                s2 = (f"C2 {t['mean_pp']:+6.1f}pp [{t['lo_pp']:+5.1f},{t['hi_pp']:+5.1f}]"
                      if t else "C2 not covered")
                C.log(f"    rate {r:4.2f}x  {s1}   {s2}")

    n_scenes = len(scenes)
    summary = {"n_scenes": n_scenes, "rates": [float(r) for r in rates],
               "criteria": {}}
    for key, tag, thresh in (("c1", "C1_nonprune_beats_prune_at_matched_bytes", 3.0),
                             ("c2", "C2_tail_weight_beats_mse_in_allocator", 1.0)):
        per_rate, n_ok, n_pos_scenes = {}, 0, 0
        for r in rates:
            vals = pooled[r][key]
            if not vals:
                per_rate[str(r)] = dict(n_scenes=0)
                continue
            arr = np.asarray(vals)
            # the registered cross-scene rule is ">= 3 of 4 scenes"; with fewer
            # scenes (a one-scene self-test) every scene must agree instead.
            need = 3 if arr.size >= 4 else int(arr.size)
            ok = bool(arr.mean() >= thresh and arr.min() > 0
                      and int((arr > 0).sum()) >= need)
            per_rate[str(r)] = dict(mean_pp=float(arr.mean()),
                                    min_scene_pp=float(arr.min()),
                                    n_positive=int((arr > 0).sum()),
                                    n_scenes=int(arr.size), passes=ok)
            n_ok += int(ok)
            n_pos_scenes = max(n_pos_scenes, int((arr > 0).sum()))
        summary["criteria"][tag] = dict(
            threshold_pp=float(thresh), rates_passing=int(n_ok),
            rates_total=len(rates), threshold_rates_needed=3,
            verdict=bool(n_ok >= 3), per_rate=per_rate)
    return dict(meta=dict(npz=os.path.abspath(dump_dir), alpha=alpha,
                          n_splits=n_splits, seed=seed,
                          note="matched-bytes comparison; drops are paired by split"),
                scenes=scenes, summary=summary)


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------


def selftest() -> int:
    rng = np.random.default_rng(0)
    # a synthetic dump where the families are ordered by construction:
    #   allocator (tail) < allocator (mse) < quant < joint < prune   in loss
    m, h, w = 12, 20, 24
    base = rng.gamma(2.0, 0.02, size=(m, h, w)).astype(np.float32)
    sev = {"q16": 1.03, "q12": 1.05, "q10": 1.07, "q8": 1.09, "q6": 1.12,
           "q4": 1.16, "q3": 1.20,
           "p90": 1.06, "p80": 1.10, "p70": 1.16, "p60": 1.24, "p50": 1.32,
           "p40": 1.42, "p30": 1.55,
           "p90_q6": 1.14, "p80_q6": 1.18, "p90_q4": 1.19, "p80_q4": 1.24,
           "p70_q6": 1.26, "p60_q8": 1.31, "p50_q8": 1.38,
           "am2.0": 1.06, "am2.5": 1.08, "am3.0": 1.11, "am3.5": 1.13, "am4.0": 1.16,
           "at2.0": 1.00, "at2.5": 1.02, "at3.0": 1.05, "at3.5": 1.07, "at4.0": 1.10}
    names = ["clean"] + list(sev)
    resid = np.stack([base] + [np.clip(base * sev[n], 0, 1) for n in sev])
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "artifacts", "_a4_selftest_rd")
    os.makedirs(out_dir, exist_ok=True)
    np.savez(os.path.join(out_dir, "synth.npz"),
             resid=resid.astype(np.float16),
             gray_render=np.zeros_like(resid, dtype=np.float16),
             gray_gt=np.zeros((m, h, w), np.float16),
             views=np.arange(m, dtype=np.int32), c2w=np.zeros((m, 4, 4), np.float32),
             K=np.zeros((m, 3, 3), np.float32),
             prim_means=np.zeros((4, 3), np.float32), prim_opacity=np.zeros(4, np.float32),
             variant_names=np.asarray(names),
             meta=json.dumps(dict(scene="synth", alpha=0.1, n_views=m, sh_degree=3)))
    # rates that every family spans: prune stops at 3.33x, so 4x would be an
    # extrapolation and the registered comparison must refuse it.
    res = analyse_dump(out_dir, rates=(2.0, 2.5, 3.0), n_splits=40, verbose=False)
    c1 = res["summary"]["criteria"]["C1_nonprune_beats_prune_at_matched_bytes"]
    c2 = res["summary"]["criteria"]["C2_tail_weight_beats_mse_in_allocator"]
    print(f"[selftest] C1 rates passing {c1['rates_passing']}/{c1['rates_total']} "
          f"verdict={c1['verdict']}")
    print(f"[selftest] C2 rates passing {c2['rates_passing']}/{c2['rates_total']} "
          f"verdict={c2['verdict']}")
    ok = c1["verdict"] and c2["verdict"]
    # monotonicity of the prune curve: heavier pruning must not help
    rows = {r["variant"]: r for r in res["scenes"][0]["rows"]}
    order = ["p90", "p80", "p70", "p60", "p50", "p40", "p30"]
    mono = all(rows[a]["drop_pp"] >= rows[b]["drop_pp"] for a, b in zip(order, order[1:]))
    print(f"[selftest] prune curve monotone: {mono}")
    print(f"[selftest] {'PASS' if ok and mono else 'FAIL'}")
    return 0 if (ok and mono) else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A4: matched-bytes rate--distortion analysis (CPU).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--npz", default=C.default_out("a4/dump"))
    ap.add_argument("--out", default=C.default_out("a4/rd.json"))
    ap.add_argument("--rates", default="2.0,2.5,3.0,3.5,4.0")
    ap.add_argument("--n-splits", type=int, default=C.N_SPLITS)
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--selftest", action="store_true")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.selftest:
        return selftest()
    rates = tuple(float(r) for r in args.rates.split(",") if r.strip())
    res = analyse_dump(args.npz, rates, args.n_splits, args.alpha, seed=args.seed)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    C.json_dump(args.out, res)
    for tag, c in res["summary"]["criteria"].items():
        C.log(f"[{C.stamp()}] {tag}: {c['rates_passing']}/{c['rates_total']} rates "
              f"pass (need {c['threshold_rates_needed']}, threshold "
              f"{c['threshold_pp']:.1f} pp) -> {'PASS' if c['verdict'] else 'FAIL'}")
    C.log(f"[{C.stamp()}] WROTE {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
