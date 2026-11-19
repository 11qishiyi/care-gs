"""Trivial baselines for "does the certificate predict downstream damage?" (B2).

The red-team-adjacent objection this answers: a reviewer of a measurement paper wants to know
whether the measured proxy beats a *trivial* predictor.  We compare three predictors of the
**task** loss at the reference cell (patch 32, search 24, tol 2, peak 0.6) across six assets and
two edits (30 % and 50 % pruning):

    A  "no damage"        t_hat = 0                     (the stale certificate, re-issued never)
    B  "one number"       t_hat = leave-one-out mean of the other cells' task losses
    C  "the certificate"  t_hat = coverage loss of the same asset and edit

Reported: MAE and Spearman rank correlation against the measured task loss.  If C is barely better
than B, that is the quantitative form of the paper's claim that the certificate tracks validity,
not utility.

Inputs (all produced by the campaign):
    results_v110/region/region_<scene>.json          coverage losses, pixel, 400 splits
    results_v110/task_sweep_4.json                   task losses, four Mip-NeRF 360 assets
    results_v110/task_sweep_bonsai.json              task losses, fifth asset
    results_v110/task_sweep_ams.json                 task losses, second dataset

Usage: python tools/baseline_table.py [--out results_v110/baseline_table.json]
"""
from __future__ import annotations

import argparse
import json
import os

CFG = dict(patch=32, search=24, tol=2, min_peak=0.6)
EDITS = ("prune30", "prune50")
ASSETS = ["bicycle", "flowers", "stump", "treehill", "bonsai", "amsterdam_20k"]
TASK_FILES = ["task_sweep_4.json", "task_sweep_bonsai.json", "task_sweep_ams.json"]
SCENE_ALIAS = {"amsterdam_20k": "amsterdam_20k"}


def coverage(scene: str, variant: str) -> float:
    path = os.path.join("results_v110", "region", f"region_{scene}.json")
    blob = json.load(open(path, encoding="utf-8"))
    rows = blob["rows"] if isinstance(blob, dict) and "rows" in blob else blob
    for r in rows:
        if r.get("scene") == scene and r.get("variant") == variant and \
                (r.get("gran") or r.get("granularity")) == "pixel":
            return abs(r["degradation_pp"])
    raise KeyError((scene, variant))


def task_losses() -> dict:
    """(scene, edit) -> task loss in points at the reference cell."""
    out = {}
    for f in TASK_FILES:
        path = os.path.join("results_v110", f)
        if not os.path.isfile(path):
            print(f"  [skip] {path} absent")
            continue
        d = json.load(open(path, encoding="utf-8"))
        ref = [c for c in d["per_config"] if c["patch"] == CFG["patch"] and c["search"] == CFG["search"]
               and c["tol"] == CFG["tol"] and abs(c["min_peak"] - CFG["min_peak"]) < 1e-9][0]
        for scene, v in ref["per_scene"].items():
            for arm in EDITS:
                out[(scene, arm)] = -100 * v[f"delta_{arm}"]
    extra = os.path.join("results_v110", "task_sweep_extra_ref.json")
    if os.path.isfile(extra):
        for scene, arms in json.load(open(extra, encoding="utf-8")).items():
            if scene.startswith("_"):
                continue
            for arm, val in arms.items():
                out.setdefault((scene, arm), float(val))
    return out


def spearman(xs, ys) -> float:
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results_v110/baseline_table.json")
    args = ap.parse_args()

    t = task_losses()
    cells = []
    for scene in ASSETS:
        for arm in EDITS:
            if (scene, arm) not in t:
                continue
            cells.append(dict(scene=scene, edit=arm, task=t[(scene, arm)], cov=coverage(scene, arm)))
    if len(cells) < 6:
        print("not enough cells:", len(cells))
        return 2

    task = [c["task"] for c in cells]
    cov = [c["cov"] for c in cells]
    n = len(cells)
    mae_zero = sum(abs(y) for y in task) / n
    # leave-one-out constant baseline
    mae_const = sum(abs(y - (sum(task) - y) / (n - 1)) for y in task) / n
    mae_cov = sum(abs(y - x) for x, y in zip(cov, task)) / n
    rho = spearman(cov, task)

    print(f"{n} cells over {len({c['scene'] for c in cells})} assets x {len(EDITS)} edits")
    print(f"{'asset':14s} {'edit':8s} {'coverage':>9s} {'task':>7s}")
    for c in cells:
        print(f"{c['scene']:14s} {c['edit']:8s} {c['cov']:9.1f} {c['task']:7.1f}")
    print(f"\nMAE  A (no damage)        {mae_zero:6.1f} points")
    print(f"MAE  B (LOO constant)     {mae_const:6.1f} points")
    print(f"MAE  C (the certificate)  {mae_cov:6.1f} points")
    print(f"Spearman(coverage, task)  {rho:+.2f}")
    json.dump(dict(cells=cells, mae_zero=mae_zero, mae_loo_constant=mae_const,
                   mae_certificate=mae_cov, spearman=rho, n_cells=n),
              open(args.out, "w", encoding="utf-8"), indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
