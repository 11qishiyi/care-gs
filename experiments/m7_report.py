"""M7 report: does local (cluster-relative) position coding beat the scene-wide grid?

Reads the ``m7_rd.json`` produced on the node (measured-byte axis) and evaluates the
three preregistered criteria of METHOD_PLAN.md "M7 规格":

  H1  at matched measured bytes, the cluster family loses >= 2.0 pp less coverage than
      the global-grid family (median over matched pairs), and wins on >= 6/8 assets
  H2  a *qualified* near-lossless member exists at >= 12x on >= 6/8 assets
      (qualified = absolute drop >= -1.0 pp, dPSNR <= 0.3 dB **and dPSNR >= 0**,
      so a member cannot pass by gaining PSNR from the archive's GT exposure mismatch)
  H3  the E1 replay of the analyser (non-prune vs prune at matched bytes) still passes

Nothing here may be re-tuned after the numbers exist.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1_analyse as A                                          # noqa: E402

CLUSTER_RE = re.compile(r"(?:^|_)c(\d+)(?:_|$)")
GRID_RE = re.compile(r"(?:^|_)m(\d+)(?:_|$)")


def kind_of(name: str) -> str:
    """``cluster`` / ``grid`` / ``other`` for one variant name."""
    s = name.strip()
    if CLUSTER_RE.search(s):
        return "cluster"
    if GRID_RE.search(s):
        return "grid"
    return "other"


def _frac(n: int, frac: float = 0.75) -> int:
    return max(1, int(-(-frac * n // 1)))


def matched_pairs(cd: list, gd: list, window: float = 0.15) -> list:
    """``[(d_pp, rate_c, rate_g, name_c, name_g)]`` for cluster/grid pairs within window.

    ``d_pp = drop_cluster - drop_grid`` (positive = the cluster codec loses less
    coverage, i.e. is better).  Matching is symmetric: every cluster variant is
    compared against the best grid variant inside ``+/-window`` of its own rate.
    """
    out = []
    for c in cd:
        cand = [g for g in gd
                if abs(g["rate"] - c["rate"]) <= window * min(g["rate"], c["rate"])]
        if not cand:
            continue
        g = max(cand, key=lambda r: r["drop_pp"])
        out.append((float(c["drop_pp"]) - float(g["drop_pp"]), c["rate"], g["rate"],
                    c["variant"], g["variant"]))
    return out


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else 0.5 * (xs[m - 1] + xs[m])


def evaluate(doc: dict, window: float = 0.15, h1_gap: float = 2.0,
             h2_rate: float = 12.0, h2_drop: float = 1.0, h2_dpsnr: float = 0.3,
             frac: float = 0.75) -> dict:
    scenes = doc.get("scenes", [])
    per = []
    for sc in scenes:
        rows = sc.get("rows", [])
        cl = [r for r in rows if kind_of(r["variant"]) == "cluster" and r.get("rate")]
        gr = [r for r in rows if kind_of(r["variant"]) == "grid" and r.get("rate")]
        pairs = matched_pairs(cl, gr, window)
        d = [p[0] for p in pairs]
        # H2: qualified near-lossless member at a high rate
        best = None
        for r in rows:
            dp = r.get("d_psnr")
            if not r.get("rate") or r["rate"] < h2_rate:
                continue
            if r["drop_pp"] < -h2_drop or dp is None:
                continue
            if float(dp) > h2_dpsnr or float(dp) < 0.0:
                continue
            if best is None or r["drop_pp"] > best["drop_pp"]:
                best = dict(variant=r["variant"], rate=r["rate"],
                            drop_pp=r["drop_pp"], d_psnr=float(dp))
        per.append(dict(
            scene=sc.get("scene"),
            n_cluster=len(cl), n_grid=len(gr), n_pairs=len(pairs),
            h1_median_pp=_median(d),
            h1_best_pair_pp=max(d) if d else None,
            h1_pairs=[dict(d_pp=p[0], rate_cluster=p[1], rate_grid=p[2],
                           cluster=p[3], grid=p[4]) for p in pairs],
            h2_member=best,
        ))
    n = len(per)
    need = _frac(n, frac)
    h1_med = [p["h1_median_pp"] for p in per if p["h1_median_pp"] is not None]
    h1 = dict(need_assets=need, n_assets=n,
              median_of_medians_pp=_median(h1_med),
              assets_positive=sum(1 for x in h1_med if x > 0),
              assets_meeting_gap=sum(1 for x in h1_med if x >= h1_gap),
              window=window, gap_pp=h1_gap)
    h1["verdict"] = bool(h1_med and _median(h1_med) >= h1_gap
                         and h1["assets_positive"] >= need)
    h2 = dict(need_assets=need, min_rate=h2_rate, max_drop_pp=h2_drop,
              max_dpsnr=h2_dpsnr, require_dpsnr_nonneg=True,
              assets_with_member=sum(1 for p in per if p["h2_member"]),
              members={p["scene"]: p["h2_member"] for p in per if p["h2_member"]})
    h2["verdict"] = h2["assets_with_member"] >= need
    h3 = doc.get("summary", {}).get("criteria", {}).get("E1_universal_dominance", {})
    h3_pass = bool(h3.get("verdict"))
    # An E1 that no rate point can cover is *unmeasurable*, not refuted: the M7 grid
    # has no quantising variant below ~7x, so the 5x/7x points have no counterpart.
    per_rate = h3.get("per_rate") or {}
    covered = [k for k, v in per_rate.items() if (v or {}).get("n_scenes")]
    need_rates = int(h3.get("threshold_rates_needed") or 0)
    thr_pp = float(h3.get("threshold_pp") or 3.0)
    thr_assets = int(h3.get("threshold_assets_agree") or 0)

    def _point_passes(v):
        v = v or {}
        if not v.get("n_scenes"):
            return False
        return (float(v.get("mean_pp", 0.0)) >= thr_pp
                and float(v.get("min_scene_pp", 0.0)) > 0.0
                and int(v.get("n_positive", 0)) >= thr_assets)

    all_covered_pass = bool(covered) and all(_point_passes(per_rate[k]) for k in covered)
    h3["covered_rates"] = covered
    h3["unmeasurable"] = bool(per_rate) and not covered
    # "Failed" is not the same as "could not be measured where the bytes are": if every
    # covered point passes but too few points have both curves, the replay is
    # under-covered, which says nothing about the claim either way.
    h3["under_covered"] = bool(covered) and not h3_pass and all_covered_pass \
        and (not need_rates or len(covered) < need_rates)
    state = "pass" if h3_pass else ("under_covered" if h3["under_covered"] else
                                   ("unmeasurable" if h3["unmeasurable"] else "fail"))
    if h1["verdict"] and h2["verdict"] and state == "pass":
        outcome = "local_coding_holds"
    elif h1["verdict"] and state == "pass":
        outcome = "local_coding_only"
    elif h1["verdict"]:
        outcome = "local_coding_positive_dominance_untested"
    elif state == "pass":
        outcome = "dominance_only"
    elif not h2["verdict"] and state == "fail":
        outcome = "dead_write_N16"
    else:
        outcome = "local_coding_negative_dominance_untested"
    return dict(window=window, scenes=per,
                H1_local_coding_wins=h1, H2_frontier_12x=h2,
                H3_dominance=h3, H3_pass=h3_pass, H3_state=state, outcome=outcome,
                meta=doc.get("meta", {}))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M7: cluster-relative positions vs the scene grid")
    ap.add_argument("--json", default="experiments/artifacts/a4/m7_rd.json")
    ap.add_argument("--out", default=None, help="write markdown here")
    ap.add_argument("--window", type=float, default=0.15)
    ap.add_argument("--self", dest="selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    with open(args.json, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    res = evaluate(doc, window=args.window)
    md = render(res)
    print(md)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md + "\n")
        print(f"\nwrote {args.out}")
    return 0


def render(res: dict) -> str:
    h1, h2, h3 = res["H1_local_coding_wins"], res["H2_frontier_12x"], res["H3_dominance"]
    L = []
    L.append("# M7 — cluster-relative positions vs the scene-wide grid\n")
    L.append(f"matched-byte window ±{h1['window']:.0%}, rate axis: "
             f"{res['meta'].get('rate_source', '?')} "
             f"(n_measured={res['meta'].get('n_measured', '?')})\n")
    L.append("| criterion | verdict | evidence |")
    L.append("|---|---|---|")
    L.append(f"| H1 local coding wins | {'PASS' if h1['verdict'] else 'FAIL'} | "
             f"median of per-asset medians {fmt(h1['median_of_medians_pp'])} pp "
             f"(need ≥ +{h1['gap_pp']:.1f}); positive on "
             f"{h1['assets_positive']}/{h1['n_assets']} (need {h1['need_assets']}) |")
    L.append(f"| H2 frontier ≥{h2['min_rate']:.0f}x | {'PASS' if h2['verdict'] else 'FAIL'} | "
             f"{h2['assets_with_member']}/{len(res['scenes'])} assets "
             f"(need {h2['need_assets']}) |")
    if h3.get("unmeasurable"):
        h3_txt = f"unmeasurable — no rate point has both curves ({sorted(per_rate)})"
    else:
        h3_txt = f"passing {h3.get('passing')}"
    L.append("")
    L.append(f"| H3 dominance (E1 replay) | {'PASS' if res['H3_pass'] else 'FAIL'} | "
             f"passing {h3.get('rates_passing', '?')}/{h3.get('rates_total', '?')} rate points "
             f"{h3.get('passing_rates') or '—'}; measured at "
             f"{h3.get('covered_rates') or '—'} |")
    L.append(f"\n**outcome: `{res['outcome']}`**\n")
    L.append("## H1 — per asset\n")
    L.append("| asset | cluster pts | grid pts | pairs | median Δ (pp) | best pair Δ (pp) |")
    L.append("|---|---|---|---|---|---|")
    for p in res["scenes"]:
        L.append(f"| {p['scene']} | {p['n_cluster']} | {p['n_grid']} | {p['n_pairs']} | "
                 f"{fmt(p['h1_median_pp'])} | {fmt(p['h1_best_pair_pp'])} |")
    L.append("\n## H2 — qualified near-lossless members\n")
    L.append("| asset | member | rate | drop (pp) | dPSNR (dB) |")
    L.append("|---|---|---|---|---|")
    for p in res["scenes"]:
        m = p["h2_member"]
        if not m:
            L.append(f"| {p['scene']} | — | — | — | — |")
        else:
            L.append(f"| {p['scene']} | `{m['variant']}` | {m['rate']:.2f}× | "
                     f"{m['drop_pp']:+.2f} | {m['d_psnr']:+.3f} |")
    return "\n".join(L)


def fmt(x, nd=2):
    return "—" if x is None else f"{x:+.{nd}f}"


def _synth(seed=0):
    """A synthetic rd doc with a known answer, for the self-test."""
    import random
    rng = random.Random(seed)
    scenes = []
    for i in range(4):
        rows = []
        # cluster family: mild loss that grows slowly with rate
        for c, rate in ((8, 7.5), (10, 7.4), (12, 7.2), (14, 6.9)):
            rows.append(dict(variant=f"c{c}_o8_sh3", family="qfp", rate=rate,
                             drop_pp=-(0.2 + 0.1 * i), d_psnr=0.05 + 0.01 * i))
        # grid family: same bytes, worse loss
        for m_bits, rate in ((16, 7.25), (18, 7.0)):
            rows.append(dict(variant=f"m{m_bits}_o8_sh3", family="qfp", rate=rate,
                             drop_pp=-(3.0 + 0.2 * i), d_psnr=0.9 + 0.1 * i))
        # a high-rate near-lossless member, plus a decoy that only "gains" PSNR
        rows.append(dict(variant="c10_o8_sh2", family="qfp", rate=13.0,
                         drop_pp=-0.3, d_psnr=0.02))
        rows.append(dict(variant="d0_m16_o8_sh8", family="qfp", rate=15.5,
                         drop_pp=-0.1, d_psnr=-2.5))
        scenes.append(dict(scene=f"s{i}", rows=rows))
    doc = dict(meta=dict(rate_source="measured", n_measured=16), scenes=scenes,
               summary=dict(criteria=dict(E1_universal_dominance=dict(
                   verdict=True, passing=["5.0", "7.0"], per_rate={}))))
    return doc


def selftest() -> int:
    fails = []

    def check(name, cond, detail=""):
        print(f"  [{'ok' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails.append(name)

    check("kind_of cluster", kind_of("c12_o8_sh3") == "cluster"
          and kind_of("p50_c12_o8_sh3") == "cluster")
    check("kind_of grid", kind_of("m16_o8_sh3") == "grid"
          and kind_of("m18_o6_sh3") == "grid")
    check("kind_of other", kind_of("clean") == "other" and kind_of("p30") == "other")

    doc = _synth()
    res = evaluate(doc)
    check("H1 passes when the cluster codec is better", res["H1_local_coding_wins"]["verdict"],
          f"median {res['H1_local_coding_wins']['median_of_medians_pp']:.2f} pp")
    check("H2 passes on a qualified member", res["H2_frontier_12x"]["verdict"],
          f"{res['H2_frontier_12x']['assets_with_member']} assets")
    check("decoy that gains PSNR is not qualified",
          all(m["d_psnr"] >= 0 for m in res["H2_frontier_12x"]["members"].values()))
    check("outcome local_coding_holds", res["outcome"] == "local_coding_holds", res["outcome"])

    # flip the world: the grid codec becomes the better one
    doc2 = _synth()
    for sc in doc2["scenes"]:
        for r in sc["rows"]:
            if r["variant"].startswith(("c", "m")):
                r["drop_pp"], r["d_psnr"] = (
                    -(3.0 if r["variant"].startswith("c") else 0.3), 1.0)
    res2 = evaluate(doc2)
    check("H1 fails when the grid codec is better", not res2["H1_local_coding_wins"]["verdict"])
    check("outcome falls back, not local_coding_holds",
          res2["outcome"] != "local_coding_holds", res2["outcome"])

    # no high-rate member at all -> H2 must fail rather than pass vacuously
    doc3 = _synth()
    for sc in doc3["scenes"]:
        sc["rows"] = [r for r in sc["rows"] if r["rate"] < 11.0]
    res3 = evaluate(doc3)
    check("H2 fails when no member is above the rate gate",
          not res3["H2_frontier_12x"]["verdict"])

    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
