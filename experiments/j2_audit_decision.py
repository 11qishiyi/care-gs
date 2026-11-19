"""J2 — can a tolerance be *certified* by a cross-asset prior, or does it need the audit?

This is the decision-theoretic companion to J1. J1 showed that a planner which
predicts coverage loss from the other assets (leave-one-asset-out median) gets the
rate close to the oracle but violates the tolerance on half the assets. J2 asks the
next question directly, on the 56 cell audit grid already measured in
`results_v120/audit_bound_nobonsai.json`:

  for every (asset, edit) cell, three decision rules say "ship" or "do not ship"
  against a tolerance eps:

    prior   : ship iff the leave-one-asset-out median loss for this edit <= eps
    audit   : ship iff the re-rendered loss on the shipped calibration views <= eps
    audited : ship iff the audit estimate <= eps - delta   (delta = measured audit error)

  and the truth is the full held-out coverage loss. A false accept is the dangerous
  error: the asset is shipped with a guarantee it does not meet.

No new rendering: this reads the same JSON the CVIU manuscript's audit table reads.

Usage:
    python experiments/j2_audit_decision.py
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

SRC = Path("results_v120/audit_bound_nobonsai.json")
OUT_JSON = Path("experiments/artifacts/a4/j2_audit_decision.json")
OUT_MD = Path("experiments/artifacts/a4/j2_audit_decision.md")
EPS_LIST = [0.5, 1.0, 2.0, 5.0]
DELTAS = [0.0, 1.0, 2.0, 3.0]


def load() -> dict:
    return json.loads(SRC.read_text())


def cells(d: dict) -> list[dict]:
    """One record per (scene, variant) with losses in pp (positive = loss)."""
    rows = []
    for r in d["rows"]:
        truth = -r["drop_mean"] * 100.0
        audit = -(r["audit_mean"] - r["clean_mean"]) * 100.0
        rows.append({"scene": r["scene"], "variant": r["variant"], "truth": truth,
                     "audit": audit, "n_views": r["n_views"],
                     "ks": r["ks_cal_mean"] * 100.0})
    return rows


def prior_losses(rows: list[dict]) -> dict:
    """Leave-one-asset-out median loss per (scene, variant) from the other scenes."""
    scenes = sorted({r["scene"] for r in rows})
    variants = sorted({r["variant"] for r in rows})
    prior = {}
    for sc in scenes:
        for v in variants:
            others = [r["truth"] for r in rows if r["variant"] == v and r["scene"] != sc]
            if others:
                prior[(sc, v)] = st.median(others)
    for r in rows:
        r["prior"] = prior.get((r["scene"], r["variant"]))
    return rows


def decide(rows: list[dict], eps: float, delta: float = 0.0) -> dict:
    n = 0
    fa = fr = ok = 0
    fa_excess, fr_excess = [], []
    for r in rows:
        if r.get("prior") is None:
            continue
        truth_ok = r["truth"] <= eps
        audit_ok = r["audit"] <= eps - delta
        n += 1
        if audit_ok and not truth_ok:
            fa += 1
            fa_excess.append(r["truth"] - eps)
        elif truth_ok and not audit_ok:
            fr += 1
            fr_excess.append(eps - r["truth"])
        elif truth_ok and audit_ok:
            ok += 1
    return {"n": n, "accept_correct": ok, "false_accept": fa, "false_reject": fr,
            "accuracy": round((n - fa - fr) / n, 3) if n else None,
            "false_accept_rate": round(fa / n, 3) if n else None,
            "mean_excess_pp_when_false_accept": round(st.mean(fa_excess), 2) if fa_excess else 0.0}


def decide_prior(rows: list[dict], eps: float) -> dict:
    n = fa = fr = ok = 0
    fa_excess = []
    for r in rows:
        if r.get("prior") is None:
            continue
        truth_ok = r["truth"] <= eps
        prior_ok = r["prior"] <= eps
        n += 1
        if prior_ok and not truth_ok:
            fa += 1
            fa_excess.append(r["truth"] - eps)
        elif truth_ok and not prior_ok:
            fr += 1
        else:
            ok += 1
    return {"n": n, "accept_correct": ok, "false_accept": fa, "false_reject": fr,
            "accuracy": round((n - fa - fr) / n, 3) if n else None,
            "false_accept_rate": round(fa / n, 3) if n else None,
            "mean_excess_pp_when_false_accept": round(st.mean(fa_excess), 2) if fa_excess else 0.0}


def main() -> None:
    d = load()
    rows = prior_losses(cells(d))
    res = {"meta": {"source": str(SRC), "eps": EPS_LIST, "deltas": DELTAS,
                    "note": "loss in pp, positive = coverage lost; audit uses the shipped "
                            "calibration views, truth uses all held-out views"},
           "n_cells": len(rows),
           "prior": {str(e): decide_prior(rows, e) for e in EPS_LIST},
           "audit": {str(e): {str(dl): decide(rows, e, dl) for dl in DELTAS} for e in EPS_LIST},
           "per_cell": rows}
    # margin that removes false accepts at each eps
    res["min_delta_zero_false_accept"] = {}
    for e in EPS_LIST:
        best = None
        for dl in [x / 2 for x in range(0, 21)]:
            r = decide(rows, e, dl)
            if r["false_accept"] == 0:
                best = dl
                break
        res["min_delta_zero_false_accept"][str(e)] = best

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    L = ["# J2 — is a tolerance certifiable without the audit?\n",
         f"Cells: **{res['n_cells']}** (8 scene-checkpoints x 7 edits; bonsai excluded upstream). "
         "Losses in pp, positive = coverage lost.\n",
         "## Decision rule: cross-asset prior (leave-one-asset-out median)\n",
         "| eps (pp) | n | correct accept | false accept | false reject | accuracy | mean excess on false accept (pp) |",
         "|---|---|---|---|---|---|---|"]
    for e in EPS_LIST:
        r = res["prior"][str(e)]
        L.append(f"| {e} | {r['n']} | {r['accept_correct']} | {r['false_accept']} | "
                 f"{r['false_reject']} | {r['accuracy']} | {r['mean_excess_pp_when_false_accept']} |")
    L += ["\n## Decision rule: 2-view / full audit on shipped calibration views\n"]
    for e in EPS_LIST:
        L.append(f"\n**eps = {e} pp**\n")
        L.append("| safety margin delta (pp) | correct accept | false accept | false reject | accuracy | mean excess (pp) |")
        L.append("|---|---|---|---|---|---|")
        for dl in DELTAS:
            r = res["audit"][str(e)][str(dl)]
            L.append(f"| {dl} | {r['accept_correct']} | {r['false_accept']} | "
                     f"{r['false_reject']} | {r['accuracy']} | {r['mean_excess_pp_when_false_accept']} |")
    L.append("\n## Smallest safety margin that removes every false accept\n")
    L.append("| eps (pp) | delta (pp) |")
    L.append("|---|---|")
    for e in EPS_LIST:
        L.append(f"| {e} | {res['min_delta_zero_false_accept'][str(e)]} |")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    for e in EPS_LIST:
        pr = res["prior"][str(e)]
        au = res["audit"][str(e)]["0.0"]
        print(f"eps={e:>4}  prior: acc {pr['accuracy']} FA {pr['false_accept']}/{pr['n']}  |  "
              f"audit: acc {au['accuracy']} FA {au['false_accept']}/{au['n']}")


if __name__ == "__main__":
    main()
