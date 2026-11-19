"""J1 — rate–reliability frontier and the coverage-aware rate planner (CPU only).

Input is the already-measured M5 grid (`experiments/artifacts/a4/m5_rd_v2.json`):
8 scene-checkpoints x 20 coded variants, each with measured rate, bytes/primitive,
paired coverage drop (pp, negative = loss), PSNR, SSIM and LPIPS.

This round answers three questions from that grid, no new rendering:

  E1  For a coverage tolerance eps, what is the largest rate any variant reaches?
      Split by action family, so "prune" and "quantise" can be priced separately.
  E2  At the rate the planner picks, what would a fidelity-first or a prune-first
      practitioner actually lose in coverage? (matched-rate collision)
  E2b Does a planner that predicts coverage from the other assets (leave-one-asset-out)
      reproduce the oracle choice, and how often does each heuristic violate eps?
  E3  How many coverage points is one decibel worth, per asset? (is a dB budget
      convertible into a pp budget?)

Criteria are written in `experiments/J1_RESULTS.md` before the run; this file only
computes. Nothing here re-renders or re-measures: it is a secondary analysis of M5.

Usage:
    python experiments/j1_reliability.py            # writes artifacts/a4/j1_*.{json,md}
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

GRID = Path("experiments/artifacts/a4/m5_rd_v2.json")
OUT_JSON = Path("experiments/artifacts/a4/j1_reliability.json")
OUT_MD = Path("experiments/artifacts/a4/j1_reliability.md")

EPS_LIST = [0.5, 1.0, 2.0, 5.0]
USABLE_RULE = "no variant improves coverage (any positive drop => protocol artefact)"


def load(path: Path = GRID) -> dict:
    d = json.loads(path.read_text())
    scenes = {s["scene"]: s for s in d["scenes"]}
    return {"meta": d.get("meta", {}), "scenes": scenes}


def usable(scenes: dict) -> tuple[list[str], list[str]]:
    keep, drop = [], []
    for name, sc in scenes.items():
        if any(r["drop_pp"] > 0 for r in sc["rows"]):
            drop.append(name)
        else:
            keep.append(name)
    return keep, drop


def best_rate(rows: list[dict], eps: float, family: str | None = None,
              use_truth: bool = True) -> dict | None:
    """Largest rate whose coverage loss is within eps. `use_truth=False` reads pred_drop."""
    pool = [r for r in rows if family is None or r.get("family") == family]
    ok = [r for r in pool if (r["drop_pp"] if use_truth else r["pred_drop"]) >= -eps]
    if not ok:
        return None
    return max(ok, key=lambda r: r["rate"])


def e1_frontier(keep: list[str], scenes: dict) -> dict:
    out = {}
    for eps in EPS_LIST:
        out[str(eps)] = {}
        for name in keep:
            rows = scenes[name]["rows"]
            any_ = best_rate(rows, eps)
            qfp = best_rate(rows, eps, "qfp")
            prn = best_rate(rows, eps, "prune")
            out[str(eps)][name] = {
                "any": None if any_ is None else {
                    "variant": any_["variant"], "rate": any_["rate"],
                    "drop_pp": any_["drop_pp"], "psnr": any_["psnr"],
                    "ssim": any_["ssim"], "lpips": any_["lpips"]},
                "qfp": None if qfp is None else {"variant": qfp["variant"], "rate": qfp["rate"],
                                                 "drop_pp": qfp["drop_pp"]},
                "prune": None if prn is None else {"variant": prn["variant"], "rate": prn["rate"],
                                                   "drop_pp": prn["drop_pp"]},
            }
    return out


def e2_collision(keep: list[str], scenes: dict, frontier: dict, eps: float = 1.0) -> list[dict]:
    """At the planner's rate, what do fidelity-first and prune-first get in coverage?"""
    rows_out = []
    for name in keep:
        pick = frontier[str(eps)][name]["any"]
        if pick is None:
            continue
        r_star = pick["rate"]
        rows = scenes[name]["rows"]
        within = [r for r in rows if r["rate"] <= r_star]
        best_fid = max(within, key=lambda r: r["psnr"])
        prunes = [r for r in within if r.get("family") == "prune"]
        best_prune = max(prunes, key=lambda r: r["rate"]) if prunes else None
        rows_out.append({
            "scene": name, "rate": r_star,
            "planner": {"variant": pick["variant"], "drop_pp": pick["drop_pp"],
                        "psnr": pick["psnr"], "ssim": pick["ssim"], "lpips": pick["lpips"]},
            "fidelity_first": {"variant": best_fid["variant"], "drop_pp": best_fid["drop_pp"],
                               "psnr": best_fid["psnr"], "ssim": best_fid["ssim"],
                               "lpips": best_fid["lpips"]},
            "prune_first": None if best_prune is None else {
                "variant": best_prune["variant"], "drop_pp": best_prune["drop_pp"],
                "psnr": best_prune["psnr"]},
        })
    return rows_out


def loo_predictions(keep: list[str], scenes: dict) -> dict:
    """For each held-out asset, predicted drop/dPSNR per variant = median over the others."""
    variants = sorted({r["variant"] for r in scenes[keep[0]]["rows"]})
    preds = {}
    for name in keep:
        others = [n for n in keep if n != name]
        p = {}
        for v in variants:
            drops, dps = [], []
            for o in others:
                r = next(x for x in scenes[o]["rows"] if x["variant"] == v)
                drops.append(r["drop_pp"])
                dps.append(scenes[o]["clean_psnr"] - r["psnr"])
            p[v] = {"pred_drop": st.median(drops), "pred_dpsnr": st.median(dps)}
        preds[name] = p
    return preds


def e2b_planners(keep: list[str], scenes: dict, preds: dict) -> dict:
    """CARP (coverage-constrained, LOO prior) vs four heuristics, per asset and eps."""
    out = {}
    for eps in [1.0, 2.0, 5.0]:
        rows_out = []
        for name in keep:
            rows = scenes[name]["rows"]
            for r in rows:
                r["pred_drop"] = preds[name][r["variant"]]["pred_drop"]
            truth = {r["variant"]: r for r in rows}
            oracle = best_rate(rows, eps, use_truth=True)
            carp = best_rate(rows, eps, use_truth=False)
            maxrate = max(rows, key=lambda r: r["rate"])
            safe = truth["m16_o8_sh8"]
            prunes = [r for r in rows if r.get("family") == "prune"]
            prune_pick = None
            ok_prune = [r for r in prunes if r["pred_drop"] >= -eps]
            if ok_prune:
                prune_pick = max(ok_prune, key=lambda r: r["rate"])
            rows_out.append({
                "scene": name,
                "oracle": {"variant": oracle["variant"], "rate": oracle["rate"],
                           "drop": truth[oracle["variant"]]["drop_pp"]},
                "carp": {"variant": carp["variant"], "rate": carp["rate"],
                         "drop": truth[carp["variant"]]["drop_pp"]},
                "maxrate": {"variant": maxrate["variant"], "rate": maxrate["rate"],
                            "drop": maxrate["drop_pp"]},
                "safe8": {"variant": safe["variant"], "rate": safe["rate"],
                          "drop": safe["drop_pp"]},
                "prune_safe": None if prune_pick is None else {
                    "variant": prune_pick["variant"], "rate": prune_pick["rate"],
                    "drop": truth[prune_pick["variant"]]["drop_pp"]},
            })
        # aggregate
        def agg(key):
            rates, viol, excess = [], 0, []
            for r in rows_out:
                if r[key] is None:
                    continue
                rates.append(r[key]["rate"] / r["oracle"]["rate"])
                if r[key]["drop"] < -eps - 1e-9:
                    viol += 1
                    excess.append(-r[key]["drop"] - eps)
            return {"mean_rate_vs_oracle": round(st.mean(rates), 3) if rates else None,
                    "violations": viol, "n": len(rates),
                    "mean_excess_pp_when_violating": round(st.mean(excess), 2) if excess else 0.0}
        out[str(eps)] = {"per_asset": rows_out,
                         "aggregate": {k: agg(k) for k in ("oracle", "carp", "maxrate", "safe8",
                                                           "prune_safe")}}
    return out


def e3_decibel(keep: list[str], scenes: dict) -> list[dict]:
    """Coverage points per decibel, per asset, over the quantisation family only."""
    out = []
    for name in keep:
        rows = scenes[name]["rows"]
        q = [r for r in rows if r.get("family") == "qfp"]
        pairs = [(scenes[name]["clean_psnr"] - r["psnr"], -r["drop_pp"]) for r in q]
        pairs = [(d, p) for d, p in pairs if d > 0.05 and p > 0]
        slope = st.median([p / d for d, p in pairs]) if pairs else None
        out.append({"scene": name, "n_pairs": len(pairs),
                    "pp_per_dB_median": round(slope, 2) if slope else None,
                    "pp_per_dB_min": round(min([p / d for d, p in pairs]), 2) if pairs else None,
                    "pp_per_dB_max": round(max([p / d for d, p in pairs]), 2) if pairs else None})
    slopes = [x["pp_per_dB_median"] for x in out if x["pp_per_dB_median"]]
    return {"per_asset": out,
            "median_range": [min(slopes), max(slopes)] if slopes else None,
            "spread_x": round(max(slopes) / min(slopes), 1) if slopes else None}


def to_md(res: dict) -> str:
    L = []
    L.append("# J1 — rate–reliability frontier and the coverage-aware planner (CPU, from the M5 grid)\n")
    L.append(f"Usable assets: **{', '.join(res['keep'])}**. "
             f"Excluded: **{', '.join(res['excluded']) or 'none'}** (rule: {USABLE_RULE}).\n")
    L.append("## E1 — largest rate within a coverage tolerance\n")
    L.append("| eps (pp) | asset | planner pick | rate | drop (pp) | PSNR | SSIM | LPIPS | best prune | best prune rate |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for eps, per in res["e1"].items():
        for name, row in per.items():
            any_ = row["any"] or {}
            prn = row["prune"] or {}
            L.append(f"| {eps} | {name} | {any_.get('variant','—')} | {any_.get('rate',0):.2f} | "
                     f"{any_.get('drop_pp',0):+.2f} | {any_.get('psnr',0):.2f} | "
                     f"{any_.get('ssim',0):.4f} | {any_.get('lpips',0):.4f} | "
                     f"{prn.get('variant','—')} | {prn.get('rate',0):.2f} |")
    L.append("\n## E2 — matched-rate collision (eps = 1 pp)\n")
    L.append("| asset | rate | planner | planner drop | fidelity-first | its drop | prune-first | its drop |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in res["e2"]:
        pf = r["prune_first"] or {}
        L.append(f"| {r['scene']} | {r['rate']:.2f} | {r['planner']['variant']} | "
                 f"{r['planner']['drop_pp']:+.2f} | {r['fidelity_first']['variant']} | "
                 f"{r['fidelity_first']['drop_pp']:+.2f} | {pf.get('variant','—')} | "
                 f"{pf.get('drop_pp',0):+.2f} |")
    L.append("\n## E2b — planners under a leave-one-asset-out coverage prior\n")
    for eps, block in res["e2b"].items():
        L.append(f"\n**eps = {eps} pp**\n")
        L.append("| planner | mean rate / oracle | violations | mean excess when violating (pp) |")
        L.append("|---|---|---|---|")
        for k, v in block["aggregate"].items():
            L.append(f"| {k} | {v['mean_rate_vs_oracle']} | {v['violations']}/{v['n']} | "
                     f"{v['mean_excess_pp_when_violating']} |")
        L.append("\n| asset | oracle rate | carp rate | carp drop | maxrate drop | safe8 drop | prune-safe drop |")
        L.append("|---|---|---|---|---|---|---|")
        for r in block["per_asset"]:
            ps = r["prune_safe"]
            L.append(f"| {r['scene']} | {r['oracle']['rate']:.2f} | {r['carp']['rate']:.2f} | "
                     f"{r['carp']['drop']:+.2f} | {r['maxrate']['drop']:+.2f} | "
                     f"{r['safe8']['drop']:+.2f} | "
                     f"{('%.2f' % ps['drop']) if ps else '—'} |")
    L.append("\n## E3 — how many coverage points is a decibel?\n")
    L.append("| asset | pairs | pp per dB (median) | min | max |")
    L.append("|---|---|---|---|---|")
    for r in res["e3"]["per_asset"]:
        L.append(f"| {r['scene']} | {r['n_pairs']} | {r['pp_per_dB_median']} | "
                 f"{r['pp_per_dB_min']} | {r['pp_per_dB_max']} |")
    L.append(f"\nAcross assets: **{res['e3']['median_range']} pp/dB, spread "
             f"{res['e3']['spread_x']}x**.\n")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=Path, default=GRID)
    ap.add_argument("--out-json", type=Path, default=OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=OUT_MD)
    args = ap.parse_args()

    data = load(args.grid)
    scenes = data["scenes"]
    keep, excluded = usable(scenes)
    frontier = e1_frontier(keep, scenes)
    res = {
        "meta": {"source": str(args.grid), "rule": USABLE_RULE, "eps": EPS_LIST},
        "keep": keep,
        "excluded": excluded,
        "e1": frontier,
        "e2": e2_collision(keep, scenes, frontier, eps=1.0),
        "e2b": e2b_planners(keep, scenes, loo_predictions(keep, scenes)),
        "e3": e3_decibel(keep, scenes),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(to_md(res), encoding="utf-8")
    print(f"wrote {args.out_json} and {args.out_md}")
    print(f"usable: {keep}\nexcluded: {excluded}")


if __name__ == "__main__":
    main()
