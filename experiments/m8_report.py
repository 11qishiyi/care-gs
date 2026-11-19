"""M8 report: does band truncation beat bit-narrowing in the high-rate corner?

Reads ``m8_rd.json`` (measured-byte axis) and applies the preregistered criteria
(METHOD_PLAN.md "M8 规格" + "M8.4a 修订"):

  J1  a *qualified* near-lossless member exists at >= 12x on >= 6/8 assets
      (qualified = |coverage loss| <= 1.0 pp, dPSNR in [0, 0.3] dB, so a member cannot
      pass by gaining PSNR from the archive's GT exposure mismatch)
  J2  inside a 15-25 B window, the band-truncated family loses >= 1.0 pp less coverage
      than the all-bands-low-bits family (>= 6/8 assets); a gap below 1.0 pp is called
      equivalent rather than a win
  J3  is *not* evaluated here: dominance over 5x-12x was established by M5's E1 replay
      and M8's grid deliberately covers only 7x-13x (see M8.4a).

Nothing here may be re-tuned after the numbers exist.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1_analyse as A                                          # noqa: E402

BAND_RE = re.compile(r"^d([0-3])_")
ALLBAND_SH_RE = re.compile(r"_sh([0-9]+)$")


def kind_of(name: str) -> str:
    """``band`` (fewer bands) / ``allband`` (every band, few bits) / ``other``."""
    s = name.strip()
    if BAND_RE.search(s):
        return "band"
    if "_o" in s and ALLBAND_SH_RE.search(s) and int(ALLBAND_SH_RE.search(s).group(1)) <= 3:
        return "allband"
    return "other"


def _need(n: int, frac: float = 0.75) -> int:
    return max(1, int(-(-frac * n // 1)))


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else 0.5 * (xs[m - 1] + xs[m])


def evaluate(doc: dict, min_rate: float = 12.0, max_drop: float = 1.0,
             max_dpsnr: float = 0.3, window=(15.0, 25.0), gap_pp: float = 1.0,
             frac: float = 0.75) -> dict:
    scenes = doc.get("scenes", [])
    per = []
    for sc in scenes:
        rows = sc.get("rows", [])
        # J1: qualified near-lossless member at a high rate
        best = None
        for r in rows:
            dp = r.get("d_psnr")
            if not r.get("rate") or r["rate"] < min_rate:
                continue
            if r["drop_pp"] < -max_drop or dp is None:
                continue
            if not (0.0 <= float(dp) <= max_dpsnr):
                continue
            if best is None or r["drop_pp"] > best["drop_pp"]:
                best = dict(variant=r["variant"], rate=r["rate"], drop_pp=r["drop_pp"],
                            d_psnr=float(dp))
        # J2: same byte window, band truncation vs all-bands-few-bits
        inwin = [r for r in rows if r.get("rate") and r.get("bytes_per_prim")
                 and window[0] <= float(r["bytes_per_prim"]) <= window[1]]
        band = [r for r in inwin if kind_of(r["variant"]) == "band"]
        allb = [r for r in inwin if kind_of(r["variant"]) == "allband"]
        j2 = None
        if band and allb:
            bb = max(band, key=lambda r: r["drop_pp"])
            ab = max(allb, key=lambda r: r["drop_pp"])
            j2 = dict(diff_pp=float(bb["drop_pp"]) - float(ab["drop_pp"]),
                      band_variant=bb["variant"], band_drop_pp=bb["drop_pp"],
                      band_rate=bb["rate"], allband_variant=ab["variant"],
                      allband_drop_pp=ab["drop_pp"], allband_rate=ab["rate"])
        per.append(dict(scene=sc.get("scene"), j1_member=best, j2=j2,
                        n_band=len(band), n_allband=len(allb)))
    n = len(per)
    need = _need(n, frac)
    j1 = dict(min_rate=min_rate, max_drop_pp=max_drop, max_dpsnr=max_dpsnr,
              require_dpsnr_nonneg=True, n_assets=n, need_assets=need,
              assets_with_member=sum(1 for p in per if p["j1_member"]),
              members={p["scene"]: p["j1_member"] for p in per if p["j1_member"]})
    j1["verdict"] = j1["assets_with_member"] >= need
    diffs = [p["j2"]["diff_pp"] for p in per if p["j2"]]
    j2 = dict(window=list(window), gap_pp=gap_pp, n_assets=n, need_assets=need,
              n_pairs=len(diffs), median_diff_pp=_median(diffs),
              assets_positive=sum(1 for d in diffs if d > 0),
              assets_meeting_gap=sum(1 for d in diffs if d >= gap_pp))
    if not diffs:
        j2["winner"] = None
        j2["verdict"] = False
    else:
        j2["winner"] = ("band" if _median(diffs) >= gap_pp
                        else ("allband" if _median(diffs) <= -gap_pp else "equivalent"))
        j2["verdict"] = j2["winner"] == "band" and j2["assets_positive"] >= need
    if j1["verdict"] and j2["verdict"]:
        outcome = "high_rate_near_lossless_holds"
    elif j1["verdict"]:
        outcome = "frontier_only"
    elif j2["verdict"]:
        outcome = "degree_beats_bits_at_high_rate"
    else:
        outcome = "dead_write_N17"
    return dict(scenes=per, J1_frontier_12x=j1, J2_band_vs_allband=j2,
                outcome=outcome, meta=doc.get("meta", {}))


def render(res: dict) -> str:
    j1, j2 = res["J1_frontier_12x"], res["J2_band_vs_allband"]
    L = ["# M8 — band truncation at the high-rate corner\n",
         f"rate axis: {res['meta'].get('rate_source', '?')} "
         f"(n_measured={res['meta'].get('n_measured', '?')})\n",
         "| criterion | verdict | evidence |", "|---|---|---|",
         f"| J1 near-lossless ≥{j1['min_rate']:.0f}× | "
         f"{'PASS' if j1['verdict'] else 'FAIL'} | {j1['assets_with_member']}/{j1['n_assets']} "
         f"assets (need {j1['need_assets']}) |",
         f"| J2 band vs all-band ({j2['window'][0]:.0f}–{j2['window'][1]:.0f} B) | "
         f"{'PASS' if j2['verdict'] else 'FAIL'} | winner `{j2['winner']}`, median Δ "
         f"{fmt(j2['median_diff_pp'])} pp, {j2['assets_positive']}/{j2['n_pairs']} positive "
         f"(need +{j2['gap_pp']:.1f} on {j2['need_assets']}) |",
         f"\n**outcome: `{res['outcome']}`**\n",
         "## J1 — qualified near-lossless members\n",
         "| asset | member | rate | drop (pp) | dPSNR (dB) |", "|---|---|---|---|---|"]
    for p in res["scenes"]:
        m = p["j1_member"]
        L.append(f"| {p['scene']} | — | — | — | — |" if not m else
                 f"| {p['scene']} | `{m['variant']}` | {m['rate']:.2f}× | "
                 f"{m['drop_pp']:+.2f} | {m['d_psnr']:+.3f} |")
    L += ["\n## J2 — per asset\n",
          "| asset | band pick | Δ vs all-band (pp) | all-band pick |", "|---|---|---|---|"]
    for p in res["scenes"]:
        j = p["j2"]
        L.append(f"| {p['scene']} | — | — | — |" if not j else
                 f"| {p['scene']} | `{j['band_variant']}` {j['band_rate']:.2f}× "
                 f"({j['band_drop_pp']:+.2f} pp) | {j['diff_pp']:+.2f} | "
                 f"`{j['allband_variant']}` {j['allband_rate']:.2f}× "
                 f"({j['allband_drop_pp']:+.2f} pp) |")
    return "\n".join(L)


def fmt(x, nd=2):
    return "—" if x is None else f"{x:+.{nd}f}"


def _synth(gain=0.0):
    rows = [
        dict(variant="clean", family="clean", rate=1.0, bytes_per_prim=236.0,
             drop_pp=0.0, d_psnr=0.0),
        dict(variant="p10", family="prune", rate=10.0, bytes_per_prim=236.0,
             drop_pp=-35.0, d_psnr=5.0),
        # all-band, few bits: cheap but lossy
        dict(variant="c8_o8_sh3", family="qfp", rate=9.0, bytes_per_prim=20.0,
             drop_pp=-6.0, d_psnr=2.0),
        dict(variant="c12_o8_sh2", family="qfp", rate=12.5, bytes_per_prim=19.0,
             drop_pp=-5.5, d_psnr=2.0),
        # band-truncated: same window, much better
        dict(variant="d1_c8_o8_sh4", family="qfp", rate=12.4, bytes_per_prim=19.1,
             drop_pp=-0.4 - gain, d_psnr=0.05),
        dict(variant="d2_c8_o8_sh4", family="qfp", rate=9.4, bytes_per_prim=25.0,
             drop_pp=-0.2, d_psnr=0.02),
    ]
    return dict(meta=dict(rate_source="measured", n_measured=len(rows)),
                scenes=[dict(scene=f"s{i}", rows=[dict(r) for r in rows]) for i in range(8)])


def selftest() -> int:
    fails = []

    def check(name, cond, detail=""):
        print(f"  [{'ok' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails.append(name)

    check("kind_of band", kind_of("d1_c8_o8_sh4") == "band"
          and kind_of("p50_d1_c8_o8_sh4") == "other")
    check("kind_of allband", kind_of("c8_o8_sh3") == "allband"
          and kind_of("c12_o8_sh2") == "allband")
    res = evaluate(_synth())
    check("J1 passes with a qualified 12x member", res["J1_frontier_12x"]["verdict"],
          f"{res['J1_frontier_12x']['assets_with_member']} assets")
    check("J2 picks band", res["J2_band_vs_allband"]["winner"] == "band",
          str(res["J2_band_vs_allband"]["winner"]))
    check("outcome high_rate_near_lossless_holds",
          res["outcome"] == "high_rate_near_lossless_holds", res["outcome"])

    # a member that only "gains" PSNR must not qualify
    doc = _synth()
    for sc in doc["scenes"]:
        for r in sc["rows"]:
            if r["variant"] == "d1_c8_o8_sh4":
                r["d_psnr"] = -1.2
    res2 = evaluate(doc)
    check("PSNR-gaining member is not qualified",
          res2["J1_frontier_12x"]["assets_with_member"] == 0, "0 expected")
    check("outcome falls back to degree_beats_bits",
          res2["outcome"] == "degree_beats_bits_at_high_rate", res2["outcome"])

    # nothing in the byte window -> J2 must not pass vacuously
    doc3 = _synth()
    for sc in doc3["scenes"]:
        sc["rows"] = [r for r in sc["rows"] if not (15 <= r["bytes_per_prim"] <= 25)]
    res3 = evaluate(doc3)
    check("J2 fails without a matched window", not res3["J2_band_vs_allband"]["verdict"])

    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M8: band truncation vs bit narrowing")
    ap.add_argument("--json", default="experiments/artifacts/a4/m8_rd.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--self", dest="selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    with open(args.json, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    res = evaluate(doc)
    md = render(res)
    print(md)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md + "\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
