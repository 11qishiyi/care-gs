"""S1: is our ladder better than the published-format baselines at *the baselines' own bytes*?

The comparison is paired by asset and by measured byte budget: for every baseline row
(a SH-only quantiser at 8 or 4 bits, or prune-then-quantise at 50%/30%), we look at what
our own measured variants achieve for the same number of bytes (within 5%, no
extrapolation) and subtract the coverage losses.

Sign convention: ``drop_pp`` is the paired coverage change against the clean asset, so it
is negative when the edit costs coverage.  ``delta = ours - baseline`` is **positive when
we lose less**.

Verdict S1: for at least 6 of 8 assets, *every* baseline is beaten by at least
``min_gain_pp`` points at the baseline's own budget, and the paired intervals do not
overlap (our lower loss bound above the baseline's upper loss bound).

    python experiments/sota_report.py --rd sota_rd.json --frontier-dir experiments/artifacts/a4
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

#: The published format: geometry untouched, coefficients rounded (``g32`` = fp32).
PUBLISHED = ("sh8_g32", "sh4_g32")
#: The usual compression recipe: delete by importance, then round what survives.
PRUNE_THEN_QUANT = ("p50_q8_g32", "p50_q4_g32", "p30_q4_g32", "p30_q2_g32")
BASELINES = PUBLISHED + PRUNE_THEN_QUANT

PRETTY = {
    "sh8_g32": "SH 8-bit",
    "sh4_g32": "SH 4-bit",
    "p50_q8_g32": "prune 50% + SH 8-bit",
    "p50_q4_g32": "prune 50% + SH 4-bit",
    "p30_q4_g32": "prune 30% + SH 4-bit",
    "p30_q2_g32": "prune 30% + SH 2-bit",
}

TOL = 0.05          # byte-budget tolerance, same as the frontier table
MIN_GAIN_PP = 1.0   # a win has to be larger than the estimator's noise floor
NEED_FRAC = 0.75


def _need(n: int, frac: float = NEED_FRAC) -> int:
    import math
    return max(1, int(math.ceil(frac * n)))


def load_our_rows(frontier_dir: str) -> dict:
    """All measured rows of our own ladders, keyed by asset (same sources as the frontier)."""
    import frontier as F

    paths = []
    for s in F.SOURCES:
        p = os.path.join(frontier_dir, s if s.endswith(".json") else s + ".json")
        if os.path.exists(p):
            paths.append(p)
    rows = F.load_rows(paths)          # {scene: [row, ...]}
    out = {}
    for scene, rs in rows.items():
        out[scene] = [dict(variant=r["variant"], rate=float(r["rate"]),
                           drop_pp=float(r["drop_pp"]),
                           drop_lo_pp=float(r.get("lo_pp", r["drop_pp"])),
                           drop_hi_pp=float(r.get("hi_pp", r["drop_pp"])),
                           d_psnr=r.get("d_psnr"))
                      for r in rs]
    return out


def load_baselines(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    out = {}
    for sc in doc.get("scenes", []):
        for r in sc.get("rows", []):
            if r.get("variant") in BASELINES and r.get("rate"):
                out.setdefault(sc["scene"], []).append(r)
    return out


def best_within(rows, budget: float, tol: float = TOL):
    """Least damaging of our rows inside ``budget * (1 + tol)``; None if none fit."""
    cand = [r for r in rows if r.get("rate") and r["rate"] <= budget * (1.0 + tol)]
    if not cand:
        return None
    return max(cand, key=lambda r: r["drop_pp"])


def evaluate(our: dict, base: dict, min_gain_pp: float = MIN_GAIN_PP,
             tol: float = TOL, frac: float = NEED_FRAC,
             headroom_pp: float = 0.0, max_dpsnr_gap: float = 0.3) -> dict:
    """Head-to-head at the baselines' own budgets.

    ``headroom_pp`` drops baselines whose own loss is better than ``-headroom_pp``:
    a baseline that already loses nothing leaves no room for a 1 pp win, so including
    it makes the criterion unpassable by construction (the ceiling lesson of N13).
    """
    scenes = sorted(set(our) & set(base))
    detail, per_scene, skipped = [], {}, 0
    for sc in scenes:
        wins = 0
        total = 0
        for b in base[sc]:
            if b["drop_pp"] > -headroom_pp:
                skipped += 1
                continue
            mine = best_within(our[sc], b["rate"], tol)
            if mine is None:
                skipped += 1
                continue
            total += 1
            delta = mine["drop_pp"] - b["drop_pp"]
            # intervals: ours must lose less even at its pessimistic end
            sep = mine["drop_lo_pp"] > b["drop_hi_pp"]
            # S1b: we may win coverage but must not buy it with fidelity
            gap = None
            if mine.get("d_psnr") is not None and b.get("d_psnr") is not None:
                gap = float(mine["d_psnr"]) - float(b["d_psnr"])
            ok = delta >= min_gain_pp and sep and (gap is None or gap <= max_dpsnr_gap)
            wins += int(ok)
            detail.append(dict(scene=sc, baseline=b["variant"],
                               base_rate=b["rate"], base_drop=b["drop_pp"],
                               our_variant=mine["variant"], our_rate=mine["rate"],
                               our_drop=mine["drop_pp"], delta_pp=delta,
                               dpsnr_gap=gap, separated=bool(sep), win=bool(ok)))
        per_scene[sc] = dict(wins=wins, total=total,
                             all_beaten=bool(total > 0 and wins == total))
    n_scenes = len(per_scene)
    n_pass = sum(1 for v in per_scene.values() if v["all_beaten"])
    deltas = [d["delta_pp"] for d in detail]
    return dict(
        per_scene=per_scene, detail=detail,
        n_scenes=n_scenes, scenes_beating_every_baseline=n_pass,
        scenes_needed=_need(n_scenes, frac),
        delta_median_pp=sorted(deltas)[len(deltas) // 2] if deltas else None,
        delta_min_pp=min(deltas) if deltas else None,
        delta_max_pp=max(deltas) if deltas else None,
        pairs_skipped=skipped, headroom_pp=headroom_pp,
        verdict=bool(n_pass >= _need(n_scenes, frac)),
    )


def render(res: dict, baselines=BASELINES) -> str:
    out = ["# S1 — our ladder versus the published-format baselines, at the baselines' own bytes", ""]
    if res.get("delta_median_pp") is None:
        out.append("No comparable rows: none of our measured variants fit any baseline's byte "
                   "budget, or the frontier rows were not found.  Nothing is extrapolated.")
        return "\n".join(out) + "\n"
    out.append(f"Verdict **S1 = {res['verdict']}** — "
               f"{res['scenes_beating_every_baseline']}/{res['n_scenes']} assets beat "
               f"every baseline by at least {MIN_GAIN_PP:.1f} points at the baseline's own "
               f"measured budget (need {res['scenes_needed']}); "
               f"delta median {res['delta_median_pp']:+.2f} pp, "
               f"range {res['delta_min_pp']:+.2f} … {res['delta_max_pp']:+.2f} pp.")
    out += ["", "| asset | baseline | base rate | base loss | our variant | our rate | our loss | delta |",
            "|---|---|---|---|---|---|---|---|"]
    for d in res["detail"]:
        out.append("| {scene} | {base} | {br:.2f}× | {bd:+.2f} | `{ov}` | {orr:.2f}× | {od:+.2f} | "
                   "**{dl:+.2f}** |".format(scene=d["scene"], base=PRETTY.get(d["baseline"], d["baseline"]),
                                            br=d["base_rate"], bd=d["base_drop"], ov=d["our_variant"],
                                            orr=d["our_rate"], od=d["our_drop"], dl=d["delta_pp"]))
    out += ["", "Losses are coverage points against the clean asset (negative = lost). "
                "Delta = ours − baseline, positive when we lose less."]
    return "\n".join(out) + "\n"


def _synth(gain: float, n: int = 8):
    """A world where our rows beat every baseline by ``gain`` points."""
    our, base = {}, {}
    for i in range(n):
        sc = f"s{i}"
        our[sc] = [dict(scene=sc, variant="c8_o8_sh3", rate=5.0, drop_pp=-0.3,
                        drop_lo_pp=-0.5, drop_hi_pp=-0.1)]
        base[sc] = [dict(scene=sc, variant=b, rate=5.0, drop_pp=-0.3 - gain,
                         drop_lo_pp=-0.3 - gain - 0.2, drop_hi_pp=-0.3 - gain + 0.2)
                    for b in BASELINES]
    return our, base


def selftest() -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  [ok] " if cond else "  [FAIL] ") + name)
        ok = ok and bool(cond)

    our, base = _synth(4.0)
    r = evaluate(our, base)
    check("clear win passes S1", r["verdict"] and r["scenes_beating_every_baseline"] == 8)
    check("delta equals the injected gain", abs(r["delta_median_pp"] - 4.0) < 1e-9)

    our2, base2 = _synth(0.3)
    r2 = evaluate(our2, base2)
    check("sub-threshold gain fails S1", not r2["verdict"])

    our3, base3 = _synth(4.0)
    for sc in our3:
        our3[sc][0] = dict(our3[sc][0], rate=20.0)   # nothing of ours fits the budget
    r3 = evaluate(our3, base3)
    check("no row at the budget is not a win", not r3["verdict"])

    print("=" * 60)
    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rd", required=False, help="sota_rd.json (baseline rows)")
    ap.add_argument("--frontier-dir", default="experiments/artifacts/a4")
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-gain-pp", type=float, default=MIN_GAIN_PP)
    ap.add_argument("--tol", type=float, default=TOL)
    ap.add_argument("--headroom-pp", type=float, default=0.0,
                    help="drop baselines that already lose less than this (a 1 pp win "
                         "is impossible when the baseline loses nothing)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.rd:
        ap.error("--rd is required")
    our = load_our_rows(args.frontier_dir)
    base = load_baselines(args.rd)
    res = evaluate(our, base, args.min_gain_pp, args.tol,
                  headroom_pp=args.headroom_pp)
    md = render(res)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("WROTE", args.out)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
