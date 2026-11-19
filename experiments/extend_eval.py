"""Extended edit-family table from a dump directory -- pure CPU, numpy only.

Input is what ``dump_artifacts.py`` leaves behind: one ``<scene>.npz`` per scene,
each holding, per variant, the per-view channel-mean absolute residual map.  One
run of this script turns that directory into the numbers the extension section
needs, for **every scene x variant**:

* deployment-side coverage: mean fraction of *deployment* pixels under the clean
  calibration threshold (the "is the certificate still true?" number);
* the paired drop vs. ``clean``: ``drop = cov(edited) - cov(clean)`` per split,
  reported as a mean with the 2.5/97.5 percentiles over the 400 splits, so a
  negative drop is a degradation (``degradation_pp = -100*drop`` is the positive
  form used in the tables);
* the conformal threshold growth ``q_edit / q_clean - 1`` (how far the *edited*
  asset's own calibration quantile moved, i.e. the edit's footprint on the score
  distribution rather than on coverage);
* all of the above at **two granularities** -- ``pixel`` (the paper's unit) and
  ``B x B`` block-max units (default ``64`` stored px, the paper's block size);
* a cross-scene summary per variant (median and range), and a dose-response view
  per edit family (prune ratio / quantiser bits / SH degree).

Output: ``extend_eval.json`` (everything, machine readable) plus a markdown file
with tables written to be pasted into the appendix.

The protocol is *not* re-derived here.  Splits, the conformal quantile, the
coverage pairing, the block-max regions and the percentile summary all come from
``common.py`` / ``region_coverage.py``, i.e. the exact code paths that produce the
paper's existing tables:

    C.split_perms(400)          np.random.default_rng(0), n_C = max(2, m//2)
    C.cq(alpha=0.10)            ceil((n+1)(1-alpha)) order statistic
    C.pixel_split_coverage      the paper's per-pixel protocol (many_splits.py)
    C.pooled_coverage_splits    region protocol, max over the views of a split
    RC.block_matrix             max-pooling into B x B blocks (certificate_audit)
    C.summarise_drops           drop_mean + 2.5/97.5 percentiles + degradation_pp

``tests/test_extend_eval.py`` asserts that the pixel and block numbers this script
prints agree with ``region_coverage.py`` on the same artifact, so the two tools
cannot drift apart.

Usage
-----
    # real run (after the npz artifacts are fetched back from the GPU node)
    python experiments/extend_eval.py --npz experiments/artifacts/dump \
        --out experiments/artifacts/extend_eval.json

    # CPU self-check on the synthetic fixture (no GPU, no torch)
    python experiments/extend_eval.py --dry-run

Only ``resid``, ``variant_names`` and ``meta`` are read from each npz, so a
``resid``-only trimmed artifact (see ``RUNBOOK_2026-11.md``, transfer option B)
evaluates identically to the full dump.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import dump_artifacts as D  # noqa: E402  (variant families / edit notes; no torch at import)
import region_coverage as RC  # noqa: E402  (the paper's block-max region builder)

#: percentile pair used for every interval in the tables (over the 400 splits)
CI_LO, CI_HI = 2.5, 97.5

#: variant ordering for the output tables: clean first, then families by severity
FAMILY_ORDER = {"clean": 0, "prune": 1, "pup": 2, "sh": 3, "quant": 4, "other": 5}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Extended scene x variant coverage / drop / q-growth tables (CPU).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--npz", default=C.default_out("dump"),
                    help="dir with <scene>.npz, a single npz, or a comma-separated list")
    ap.add_argument("--out", default=C.default_out("extend_eval.json"))
    ap.add_argument("--md", default="",
                    help="markdown output (default: <out stem>.md next to the json)")
    ap.add_argument("--variants", default="",
                    help="default: every non-clean variant present in the artifacts")
    ap.add_argument("--granularities", default="pixel,block")
    ap.add_argument("--blocks", default="64",
                    help="comma list of block sizes in STORED pixels (64 = the paper's"
                         " block column on factor-4 maps)")
    ap.add_argument("--block-mode", default="floor", choices=["floor", "pad"],
                    help="floor = H//b blocks (certificate_audit.py convention)")
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--n-splits", type=int, default=C.N_SPLITS)
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--max-scenes", type=int, default=0)
    ap.add_argument("--max-views", type=int, default=0)
    ap.add_argument("--decimals", type=int, default=1, help="decimals in the markdown")
    # synthetic self-check
    ap.add_argument("--dry-run", action="store_true",
                    help="evaluate the synthetic fixture (dump_artifacts.py --dry-run)")
    ap.add_argument("--dry-run-out", default=os.path.join(C.default_out("dryrun_extend"),
                                                          "dump"))
    ap.add_argument("--dry-run-rebuild", action="store_true",
                    help="re-write the synthetic fixture even if the npz files exist")
    ap.add_argument("--dry-run-scenes", default="dryrun_alpha,dryrun_beta")
    ap.add_argument("--dry-run-hw", default="259,389")
    ap.add_argument("--dry-run-views", type=int, default=18)
    ap.add_argument("--dry-run-variants",
                    default="clean,prune50,prune30,shdeg1,quant8,quant4,quant6")
    return ap


# ---------------------------------------------------------------------------
# per-split statistics (all protocol work delegated to common.py)
# ---------------------------------------------------------------------------


def _flat_thresholds(flat, splits, alpha):
    """Per-split conformal quantile of the *pixel* calibration scores."""
    return np.asarray([C.cq(flat[cal].reshape(-1), alpha) for cal, _ in splits],
                      np.float64)


def _region_thresholds(E, splits, alpha, pool="max"):
    """Per-split quantile of the *region* calibration scores (max over cal views).

    Mirrors ``C.pooled_coverage_splits``' calibration half exactly; kept separate
    because that helper reports coverage but not the threshold, and the threshold
    growth is one of the required quantities here.
    """
    out = []
    for cal, _ in splits:
        s = C._pool(np.asarray(E)[np.asarray(cal)], pool)
        ok = np.isfinite(s)
        out.append(C.cq(s[ok], alpha) if ok.any() else np.nan)
    return np.asarray(out, np.float64)


def _summarise(clean_cov, deploy_cov, drops, q_clean, q_edit):
    """Coverage / drop / q-growth summary for one (scene, variant, granularity)."""
    out = dict(C.summarise_drops(drops, clean_cov, deploy_cov))
    qc = np.asarray(q_clean, np.float64)
    qe = np.asarray(q_edit, np.float64)
    growth = qe / np.clip(qc, 1e-12, None) - 1.0
    growth = growth[np.isfinite(growth)]
    out.update(
        q_mean=C.as_float(np.mean(qc)) if qc.size else None,
        q_edit_mean=C.as_float(np.mean(qe)) if qe.size else None,
        q_growth_mean=C.as_float(growth.mean()) if growth.size else None,
        q_growth_lo=C.as_float(np.percentile(growth, CI_LO)) if growth.size else None,
        q_growth_hi=C.as_float(np.percentile(growth, CI_HI)) if growth.size else None,
    )
    return out


def _row(scene, variant, gran, n_views, n_units, summ, extra=None):
    row = dict(scene=scene, variant=variant, granularity=gran,
               is_clean=bool(variant == "clean"),
               edit=D.EDIT_NOTES.get(variant, ""),
               family=D.variant_family(variant), dose=D.variant_dose(variant),
               n_views=int(n_views), n_units=int(n_units))
    row.update({k: v for k, v in summ.items()})
    if extra:
        row.update(extra)
    return row


def pixel_rows(clean_resid, edited, scene, splits, args):
    """``pixel`` granularity rows for one scene."""
    m = clean_resid.shape[0]
    flat_clean = clean_resid.reshape(m, -1)
    qc = _flat_thresholds(flat_clean, splits, args.alpha)
    rows = []
    cc, cc2, dd, _ = C.pixel_split_coverage(flat_clean, flat_clean, splits,
                                            args.alpha, qs=qc)
    rows.append(_row(scene, "clean", "pixel", m, flat_clean.shape[1],
                     _summarise(cc, cc2, dd, qc, qc)))
    for v in _order(edited):
        res = edited[v]
        flat = np.asarray(res, np.float32).reshape(m, -1)
        qe = _flat_thresholds(flat, splits, args.alpha)
        cc, ss, dd, _ = C.pixel_split_coverage(flat_clean, flat, splits,
                                               args.alpha, qs=qc)
        rows.append(_row(scene, v, "pixel", m, flat_clean.shape[1],
                         _summarise(cc, ss, dd, qc, qe)))
    return rows


def block_rows(clean_resid, edited, scene, splits, args, blocks):
    """``block<b>`` granularity rows for one scene."""
    m = clean_resid.shape[0]
    rows = []
    for b in blocks:
        E_clean = RC.block_matrix(clean_resid, b, args.block_mode)
        qc = _region_thresholds(E_clean, splits, args.alpha)
        cc, cc2, dd = C.pooled_coverage_splits(E_clean, E_clean, splits,
                                               args.alpha, pool="max")
        _check_aligned(cc, qc, scene, f"block{b}")
        gran = f"block{b}"
        block_px = int(b * float(args.factor) * float(args.downsample))
        extra = dict(block_stored_px=int(b), block_capture_px=block_px,
                     block_mode=args.block_mode)
        rows.append(_row(scene, "clean", gran, m, E_clean.shape[1],
                         _summarise(cc, cc2, dd, qc, qc), extra))
        for v in _order(edited):
            res = edited[v]
            E = RC.block_matrix(res, b, args.block_mode)
            qe = _region_thresholds(E, splits, args.alpha)
            cc, ss, dd = C.pooled_coverage_splits(E_clean, E, splits,
                                                  args.alpha, pool="max")
            _check_aligned(cc, qe, scene, gran)
            rows.append(_row(scene, v, gran, m, E_clean.shape[1],
                             _summarise(cc, ss, dd, qc, qe), extra))
    return rows


def _check_aligned(cov, q, scene, gran):
    """``pooled_coverage_splits`` skips splits it cannot score; so must we."""
    if len(cov) != len(q):
        raise RuntimeError(
            f"{scene}/{gran}: {len(cov)} scored splits but {len(q)} thresholds -- "
            "the artifact has regions that are never observed in calibration, "
            "which this block-based tool does not expect (NaN in a resid map?)")


# ---------------------------------------------------------------------------
# one scene
# ---------------------------------------------------------------------------


def _want_variants(sc, args):
    names = sc["variant_names"]
    if args.variants:
        want = [v.strip() for v in args.variants.split(",") if v.strip()]
        missing = [v for v in want if v not in names]
        if missing:
            raise SystemExit(f"{sc['meta'].get('scene')}: missing variants {missing} "
                             f"(have {names})")
        return want
    return [v for v in names if v != "clean"]


def run_scene(path, args):
    sc = C.load_npz_scene(path)
    meta = sc["meta"]
    scene = str(meta.get("scene") or os.path.basename(path)[:-4])
    vnames = sc["variant_names"]
    if "clean" not in vnames:
        raise SystemExit(f"{path}: no 'clean' variant, cannot pair the drop")
    resid = np.asarray(sc["resid"], np.float32)
    m = int(resid.shape[1])
    if args.max_views:
        m = min(m, int(args.max_views))
    if m < 4:
        raise SystemExit(f"{scene}: {m} held-out views is too few for the "
                         f"{args.n_splits}-split protocol (need >= 4)")
    resid = resid[:, :m]
    splits = C.split_perms(m, args.n_splits, args.seed)
    clean = resid[vnames.index("clean")]
    edited = {v: resid[vnames.index(v)] for v in _want_variants(sc, args)}
    gran = [g.strip() for g in args.granularities.split(",") if g.strip()]
    blocks = [int(b) for b in str(args.blocks).split(",") if str(b).strip()]

    # factor/downsample only annotate the block size in capture pixels
    args.factor = float(meta.get("factor", 4))
    args.downsample = float(meta.get("downsample", 1))

    rows = []
    if "pixel" in gran:
        t0 = time.time()
        rows += pixel_rows(clean, edited, scene, splits, args)
        C.log(f"  {scene}: pixel done ({rows[0]['n_units']} pixels/view x {m} views, "
              f"{len(edited) + 1} variants, {time.time() - t0:.1f}s)")
    if "block" in gran:
        t0 = time.time()
        brows = block_rows(clean, edited, scene, splits, args, blocks)
        rows += brows
        C.log(f"  {scene}: {'+'.join(f'block{b}' for b in blocks)} done "
              f"({brows[0]['n_units']} regions/view, {time.time() - t0:.1f}s)")
    return rows, dict(scene=scene, path=path, n_views=m,
                      variants=["clean"] + list(edited),
                      factor=args.factor, downsample=args.downsample,
                      dry_run=bool(meta.get("dry_run", False)),
                      height=int(meta.get("height", resid.shape[-2])),
                      width=int(meta.get("width", resid.shape[-1])))


# ---------------------------------------------------------------------------
# cross-scene summary + dose curves
# ---------------------------------------------------------------------------


def _order(variants):
    return sorted(variants, key=lambda v: (FAMILY_ORDER.get(D.variant_family(v), 9),
                                           D.variant_dose(v), v))


def _med_range(vals):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], np.float64)
    if v.size == 0:
        return dict(median=None, lo=None, hi=None, n=0)
    return dict(median=float(np.median(v)), lo=float(v.min()), hi=float(v.max()),
                n=int(v.size))


def summarise(rows):
    """Per (variant, granularity): median / range across scenes."""
    variants = _order({r["variant"] for r in rows})
    grans = []
    for r in rows:
        if r["granularity"] not in grans:
            grans.append(r["granularity"])
    out = {}
    for v in variants:
        out[v] = {}
        for g in grans:
            sel = [r for r in rows if r["variant"] == v and r["granularity"] == g]
            if not sel:
                continue
            out[v][g] = dict(
                n_scenes=len(sel),
                edit=D.EDIT_NOTES.get(v, ""),
                family=D.variant_family(v),
                dose=D.variant_dose(v),
                deploy_cov=_med_range([r.get("stale_mean") for r in sel]),
                clean_cov=_med_range([r.get("clean_mean") for r in sel]),
                drop_pp=_med_range([None if r.get("drop_mean") is None
                                    else 100.0 * r["drop_mean"] for r in sel]),
                degradation_pp_mean=(
                    float(np.mean([-100.0 * r["drop_mean"] for r in sel
                                   if r.get("drop_mean") is not None]))
                    if any(r.get("drop_mean") is not None for r in sel) else None),
                q_growth_pct=_med_range([None if r.get("q_growth_mean") is None
                                         else 100.0 * r["q_growth_mean"] for r in sel]),
                n_scenes_degraded=int(sum(1 for r in sel
                                          if r.get("drop_mean") is not None
                                          and r["drop_mean"] < 0.0)),
                n_scenes_improved=int(sum(1 for r in sel
                                          if r.get("drop_mean") is not None
                                          and r["drop_mean"] > 0.0)),
                by_scene={r["scene"]: dict(
                    deploy_cov=r.get("stale_mean"), drop_pp=(None if r.get("drop_mean")
                                                             is None
                                                             else 100.0 * r["drop_mean"]),
                    drop_lo_pp=(None if r.get("drop_lo") is None else 100.0 * r["drop_lo"]),
                    drop_hi_pp=(None if r.get("drop_hi") is None else 100.0 * r["drop_hi"]),
                    q_growth_pct=(None if r.get("q_growth_mean") is None
                                  else 100.0 * r["q_growth_mean"])) for r in sel},
            )
    return out


def dose_curves(summary):
    """Per edit family: median pixel drop vs. dose (prune ratio / bits / SH degree)."""
    out = {}
    for fam in ("prune", "quant", "sh", "pup"):
        pts = []
        for v, per in summary.items():
            if D.variant_family(v) != fam or "pixel" not in per:
                continue
            drop = per["pixel"]["drop_pp"]["median"]
            if drop is None:
                continue
            pts.append(dict(variant=v, dose=D.variant_dose(v),
                            edit=D.EDIT_NOTES.get(v, ""),
                            drop_pp=float(drop),
                            q_growth_pct=per["pixel"]["q_growth_pct"]["median"],
                            n_scenes=per["pixel"]["n_scenes"]))
        if pts:
            out[fam] = sorted(pts, key=lambda p: p["dose"])
    return out


# ---------------------------------------------------------------------------
# markdown
# ---------------------------------------------------------------------------


def _f(x, nd=1, scale=1.0, suffix="", sign=False):
    if x is None or not np.isfinite(x):
        return "n/a"
    v = scale * float(x)
    fmt = f"{{:+.{nd}f}}" if sign else f"{{:.{nd}f}}"
    return fmt.format(v) + suffix


def _pp(x, nd=1):
    """A coverage drop as a signed pp number."""
    return _f(x, nd, 100.0, "", sign=True)


def _pct(x, nd=0):
    return _f(x, nd, 100.0, "", sign=True)


def markdown(rows, summary, curves, meta, args):
    scenes = []
    for r in rows:
        if r["scene"] not in scenes:
            scenes.append(r["scene"])
    variants = _order({r["variant"] for r in rows})
    grans = []
    for r in rows:
        if r["granularity"] not in grans:
            grans.append(r["granularity"])
    px = "pixel"
    blk = next((g for g in grans if g.startswith("block")), None)

    L = []
    L.append("# Extended edit-family evaluation")
    L.append("")
    L.append(f"Auto-generated by `experiments/extend_eval.py` from "
             f"{len(meta['scenes'])} scene artifact(s) "
             f"({', '.join(s['scene'] for s in meta['scenes'])}).")
    L.append("")
    if meta.get("dry_run"):
        L.append("> **SYNTHETIC FIXTURE -- dry run.** These numbers come from the "
                 "synthetic `dump_artifacts.py --dry-run` arrays.  They validate the "
                 "pipeline, the schema and the protocol plumbing; they are *not* "
                 "results and must never be quoted in the paper.")
        L.append("")
    blk_list = "/".join(str(b) for b in meta["blocks"])
    L.append(f"**Protocol.** {meta['n_splits']} random calibration/deployment view splits "
             f"(`np.random.default_rng({meta['seed']})`, `n_C = max(2, m//2)`); the "
             f"threshold is the split-conformal quantile of the **clean** calibration "
             f"scores at `alpha = {meta['alpha']:.2f}`; coverage is measured on "
             f"deployment units; `drop = cov(edited) - cov(clean)` is paired by split, so "
             f"a negative drop is a degradation. Intervals are the "
             f"{CI_LO:g}/{CI_HI:g} percentiles over the {meta['n_splits']} splits, not "
             f"standard errors. Pixel rows use every pixel of a deployment view; "
             f"block rows use max-pooled {blk_list}x{blk_list} blocks "
             f"({blk_list} stored px = "
             f"{meta['blocks'][0] * meta['factor'] * meta['downsample']:.0f} capture px).")
    L.append("")

    # ---- Table E1/E2: deployment coverage + paired drop --------------------
    for gi, (g, title) in enumerate((
            (px, "Table E1. Pixel granularity"),
            (blk, "Table E2. Block granularity"))):
        if g is None:
            continue
        L.append(f"## {title}: deployment-side coverage and paired drop vs. `clean`")
        L.append("")
        head = "| variant | edit | " + " | ".join(f"{s} (n={_nviews(meta, s)})"
                                                  for s in scenes)
        head += " | median drop (pp) [min, max] |"
        L.append(head)
        L.append("|---|---|" + "---|" * len(scenes) + "---|")
        for v in variants:
            cells = []
            for s in scenes:
                r = _find(rows, s, v, g)
                if r is None:
                    cells.append("n/a")
                    continue
                if r["is_clean"]:
                    cells.append(f"cov {_f(r.get('stale_mean'), 1, 100.0, '%')}")
                else:
                    cells.append(f"{_f(r.get('stale_mean'), 1, 100.0, '%')} / "
                                 f"{_pp(r.get('drop_mean'))} [{_pp(r.get('drop_lo'))}, "
                                 f"{_pp(r.get('drop_hi'))}]")
            sm = summary.get(v, {}).get(g, {}).get("drop_pp", {})
            rng = (f"{_f(sm.get('median'), 1, 1.0, '', True)} "
                   f"[{_f(sm.get('lo'), 1, 1.0, '', True)}, "
                   f"{_f(sm.get('hi'), 1, 1.0, '', True)}]")
            L.append(f"| `{v}` | {D.EDIT_NOTES.get(v, '')} | " + " | ".join(cells)
                     + f" | {rng} |")
        L.append("")
        L.append("Cell format: deployment-side coverage % / paired drop in pp with its "
                 f"{CI_LO:g}/{CI_HI:g} split interval. `clean` rows are the reference "
                 "coverage (their drop is 0 by construction).")
        L.append("")

    # ---- Table E3: q growth ------------------------------------------------
    L.append("## Table E3. Conformal threshold growth `q_edit / q_clean - 1`")
    L.append("")
    L.append("| variant | edit | " + " | ".join(scenes) + " | median % [min, max] |")
    L.append("|---|---|" + "---|" * len(scenes) + "---|")
    for v in variants:
        if v == "clean":
            continue
        cells = []
        for s in scenes:
            parts = []
            for g in grans:
                r = _find(rows, s, v, g)
                if r is not None:
                    parts.append(f"{_pct(r.get('q_growth_mean'))}"
                                 + ("%" if g == px else "%ᵇ"))
            cells.append(" / ".join(parts) if parts else "n/a")
        sm = summary.get(v, {}).get(px, {}).get("q_growth_pct", {})
        rng = (f"{_f(sm.get('median'), 0, 1.0, '', True)} "
               f"[{_f(sm.get('lo'), 0, 1.0, '', True)}, "
               f"{_f(sm.get('hi'), 0, 1.0, '', True)}]")
        L.append(f"| `{v}` | {D.EDIT_NOTES.get(v, '')} | " + " | ".join(cells)
                 + f" | {rng} |")
    L.append("")
    L.append("Cell format: pixel / block-threshold growth (block marked ᵇ). Growth > 0 "
             "means the edited asset's own calibration scores got larger, i.e. the edit "
             "moved the score distribution even where coverage did not move.")
    L.append("")

    # ---- Table E4: cross-scene summary ------------------------------------
    L.append("## Table E4. Cross-scene summary per variant (median [min, max] over scenes)")
    L.append("")
    L.append("| variant | edit | gran. | deployment cov % | drop pp | q growth % "
             "| scenes degraded |")
    L.append("|---|---|---|---|---|---|---|")
    for v in variants:
        for g in grans:
            d = summary.get(v, {}).get(g)
            if not d:
                continue
            L.append(f"| `{v}` | {D.EDIT_NOTES.get(v, '')} | {g} "
                     f"| {_f(d['deploy_cov']['median'], 1, 100.0)} "
                     f"[{_f(d['deploy_cov']['lo'], 1, 100.0)}, "
                     f"{_f(d['deploy_cov']['hi'], 1, 100.0)}] "
                     f"| {_f(d['drop_pp']['median'], 1, 1.0, '', True)} "
                     f"[{_f(d['drop_pp']['lo'], 1, 1.0, '', True)}, "
                     f"{_f(d['drop_pp']['hi'], 1, 1.0, '', True)}] "
                     f"| {_f(d['q_growth_pct']['median'], 0, 1.0, '', True)} "
                     f"[{_f(d['q_growth_pct']['lo'], 0, 1.0, '', True)}, "
                     f"{_f(d['q_growth_pct']['hi'], 0, 1.0, '', True)}] "
                     f"| {d['n_scenes_degraded']}/{d['n_scenes']} |")
    L.append("")

    # ---- Table E5: dose response -----------------------------------------
    if curves:
        L.append("## Table E5. Dose response within each edit family (median pixel units)")
        L.append("")
        L.append("| family | variant | dose | edit | drop pp | q growth % | scenes |")
        L.append("|---|---|---|---|---|---|---|")
        for fam, pts in curves.items():
            for p in pts:
                L.append(f"| {fam} | `{p['variant']}` | {p['dose']:g} | {p['edit']} "
                         f"| {_f(p['drop_pp'], 1, 1.0, '', True)} "
                         f"| {_f(p['q_growth_pct'], 0, 1.0, '', True)} "
                         f"| {p['n_scenes']} |")
        L.append("")
        L.append("Dose = kept fraction for `prune`/`pup`, quantiser bits for `quant`, SH "
                 "degree for `sh`; a monotone column is what the appendix's "
                 "dose-response claim needs (more severe edit -> larger drop).")
        L.append("")

    # ---- Table E6: long form ---------------------------------------------
    L.append("## Table E6. Long form (one row per scene x variant x granularity)")
    L.append("")
    L.append("| scene | variant | granularity | units | clean cov % | deploy cov % "
             "| drop pp | drop 2.5% | drop 97.5% | q growth % | q g. 2.5% | q g. 97.5% |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['scene']} | `{r['variant']}` | {r['granularity']} "
                 f"| {r['n_units']} | {_f(r.get('clean_mean'), 2, 100.0)} "
                 f"| {_f(r.get('stale_mean'), 2, 100.0)} | {_pp(r.get('drop_mean'), 2)} "
                 f"| {_pp(r.get('drop_lo'), 2)} | {_pp(r.get('drop_hi'), 2)} "
                 f"| {_pct(r.get('q_growth_mean'), 1)} "
                 f"| {_pct(r.get('q_growth_lo'), 1)} | {_pct(r.get('q_growth_hi'), 1)} |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("Source: `extend_eval.json` (same run). `degradation_pp = -100 * drop` is "
             "the positive form of the same quantity. Nothing here is a bootstrap of the "
             "mean: the interval is the spread of the per-split statistic, exactly like "
             "the paper's coverage columns.")
    L.append("")
    return "\n".join(L)


def _find(rows, scene, variant, gran):
    for r in rows:
        if r["scene"] == scene and r["variant"] == variant and r["granularity"] == gran:
            return r
    return None


def _nviews(meta, scene):
    for s in meta["scenes"]:
        if s["scene"] == scene:
            return s["n_views"]
    return "?"


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def _prepare_dry_run(args):
    """Build (or reuse) the synthetic fixture written by ``dump_artifacts --dry-run``."""
    out = args.dry_run_out
    want = [f"{s}.npz" for s in args.dry_run_scenes.split(",") if s.strip()]
    have = all(os.path.isfile(os.path.join(out, w)) for w in want)
    if have and not args.dry_run_rebuild:
        C.log(f"[{C.stamp()}] dry-run fixture reused from {out} "
              f"(--dry-run-rebuild to rewrite)")
        return out
    C.log(f"[{C.stamp()}] dry-run: writing synthetic fixture to {out}")
    D.main(["--dry-run", "--dry-run-out", out,
            "--dry-run-scenes", args.dry_run_scenes,
            "--dry-run-hw", args.dry_run_hw,
            "--dry-run-views", str(args.dry_run_views),
            "--variants", args.dry_run_variants,
            "--seed", str(args.seed),
            "--alpha", str(args.alpha)])
    return out


def main(argv=None):
    args = build_parser().parse_args(argv)
    t0 = time.time()
    npz_in = _prepare_dry_run(args) if args.dry_run else args.npz
    files = C.discover_npz(npz_in)
    if not files:
        raise SystemExit(f"no npz artifacts under {npz_in}")
    if args.max_scenes:
        files = files[: args.max_scenes]
    md_path = args.md or os.path.splitext(args.out)[0] + ".md"
    C.log(f"[{C.stamp()}] extend_eval: {len(files)} npz, variants="
          f"{args.variants or 'all non-clean'}, granularities={args.granularities} "
          f"blocks={args.blocks}, splits={args.n_splits} alpha={args.alpha}")

    rows, scenes = [], []
    for path in files:
        C.log(f"  --- {os.path.basename(path)}")
        r, s = run_scene(path, args)
        rows += r
        scenes.append(s)

    summary = summarise(rows)
    curves = dose_curves(summary)
    grans = sorted({r["granularity"] for r in rows}, key=lambda g: (g != "pixel", g))
    meta = dict(
        protocol="400 random cal/deployment view splits (np.random.default_rng(0), "
                 "n_C=max(2,m//2)); threshold = split-conformal quantile of the CLEAN "
                 "calibration scores; coverage on deployment units; "
                 "drop = coverage(edited) - coverage(clean) paired by split; "
                 "degradation_pp = -100*drop; q growth = q(edited cal) / q(clean cal) - 1",
        intervals=f"{CI_LO:g}/{CI_HI:g} percentiles over the splits (not a bootstrap of "
                  "the mean)",
        alpha=float(args.alpha), n_splits=int(args.n_splits), seed=int(args.seed),
        blocks=[int(b) for b in str(args.blocks).split(",") if str(b).strip()],
        block_mode=args.block_mode, granularities=grans,
        factor=scenes[0]["factor"], downsample=scenes[0]["downsample"],
        dry_run=bool(args.dry_run), npz=[os.path.basename(f) for f in files],
        scenes=scenes, n_rows=len(rows),
        generated=C.stamp(), seconds=round(time.time() - t0, 1))
    res = dict(meta=meta, rows=rows, summary_by_variant=summary,
               dose_response=curves, seconds=round(time.time() - t0, 1))
    C.json_dump(args.out, res)
    C.log(f"[{C.stamp()}] WROTE {args.out} ({C.sizeof_fmt(os.path.getsize(args.out))}, "
          f"{len(rows)} rows)")

    txt = markdown(rows, summary, curves, meta, args)
    os.makedirs(os.path.dirname(os.path.abspath(md_path)) or ".", exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(txt)
    C.log(f"[{C.stamp()}] WROTE {md_path} ({C.sizeof_fmt(len(txt.encode('utf-8')))}"
          f"{', DRY-RUN FIXTURE -- numbers are synthetic' if args.dry_run else ''})")

    for v in _order({r['variant'] for r in rows}):
        if v == "clean":
            continue
        parts = []
        for g in meta["granularities"]:
            d = summary.get(v, {}).get(g)
            if not d:
                continue
            parts.append(f"{g} drop {_f(d['drop_pp']['median'], 1, 1.0, '', True)}pp "
                         f"qg {_f(d['q_growth_pct']['median'], 0, 1.0, '', True)}%")
        if parts:
            C.log(f"  {v:8s} median over scenes: " + "  ".join(parts))
    C.log(f"[{C.stamp()}] done in {res['seconds']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
