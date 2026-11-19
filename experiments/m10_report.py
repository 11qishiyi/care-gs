"""M10 verdicts: does a two-stage SH dictionary clear the 12x near-lossless gate?

L1  near-lossless at >= 12x on >= 6/8 assets   (the gate M9 missed by 0.13-1.10 pp)
L2  residual stage beats a single-stage dictionary at matched bytes (+-10%), >= 6/8
L3  the two-stage envelope owns 15-25x against every other family, >= 6/8
"""
import argparse
import json
import os
import sys

TARGET_BAND = (15.0, 25.0)
MATCH_WINDOW = 0.10
L1_MIN_RATE = 12.0
L1_MAX_DROP = 1.0
L1_MAX_DPSNR = 0.3
L2_GAP_PP = 0.3
L3_GAP_PP = 1.0
RVQ_TAG = "rvq"
SINGLE_TAG = "vq"


def is_rvq(name):
    return RVQ_TAG in name


def is_single(name):
    return name.startswith(SINGLE_TAG) and not is_rvq(name)


def _need(n, frac=0.75):
    import math
    return max(1, int(math.ceil(frac * int(n))))


def _median(xs):
    ys = sorted(x for x in xs if x is not None)
    if not ys:
        return None
    m = len(ys) // 2
    return ys[m] if len(ys) % 2 else 0.5 * (ys[m - 1] + ys[m])


def evaluate(doc, min_rate=L1_MIN_RATE, max_drop=L1_MAX_DROP, max_dpsnr=L1_MAX_DPSNR,
             window=MATCH_WINDOW, l2_gap=L2_GAP_PP, l3_gap=L3_GAP_PP,
             band=TARGET_BAND, frac=0.75):
    scenes = doc.get("scenes", [])
    per = []
    for sc in scenes:
        rows = [r for r in sc.get("rows", [])
                if r.get("rate") and r.get("drop_pp") is not None
                and r.get("variant") != "clean"]
        rvq = [r for r in rows if is_rvq(r["variant"])]
        single = [r for r in rows if is_single(r["variant"])]
        other = [r for r in rows if not is_rvq(r["variant"])]

        # L1: near-lossless members at >= 12x
        ok = [r for r in rvq
              if float(r["rate"]) >= min_rate
              and float(r["drop_pp"]) >= -max_drop
              and r.get("d_psnr") is not None
              and 0.0 <= float(r["d_psnr"]) <= max_dpsnr]
        k1 = dict(members=[dict(variant=r["variant"], rate=r["rate"], drop_pp=r["drop_pp"],
                                d_psnr=r.get("d_psnr")) for r in ok],
                  best=None)
        if rvq:
            b = max(rvq, key=lambda r: float(r["drop_pp"]))
            k1["best"] = dict(variant=b["variant"], rate=b["rate"], drop_pp=b["drop_pp"],
                              d_psnr=b.get("d_psnr"))

        # L2: matched-byte comparison against the single-stage dictionary
        pairs = []
        for r in rvq:
            for s in single:
                if abs(float(s["rate"]) - float(r["rate"])) <= window * float(r["rate"]):
                    pairs.append(dict(rvq=r["variant"], single=s["variant"],
                                      rate=float(r["rate"]), rate_single=float(s["rate"]),
                                      drop_rvq=float(r["drop_pp"]),
                                      drop_single=float(s["drop_pp"]),
                                      diff=float(r["drop_pp"]) - float(s["drop_pp"])))
        best_pair = max(pairs, key=lambda p: p["diff"]) if pairs else None

        # L3: envelope over the 15-25x band, against everything that is not rvq
        inband = lambda r: band[0] <= float(r["rate"]) <= band[1]
        rvq_band = [r for r in rvq if inband(r)]
        other_band = [r for r in other if inband(r)]
        env = None
        if rvq_band and other_band:
            b_r = max(rvq_band, key=lambda r: float(r["drop_pp"]))
            b_o = max(other_band, key=lambda r: float(r["drop_pp"]))
            env = dict(rvq=b_r["variant"], rvq_rate=b_r["rate"], rvq_drop=float(b_r["drop_pp"]),
                       other=b_o["variant"], other_rate=b_o["rate"],
                       other_drop=float(b_o["drop_pp"]),
                       diff=float(b_r["drop_pp"]) - float(b_o["drop_pp"]))
        per.append(dict(scene=sc.get("scene"), l1=k1, l2=best_pair, l3=env))

    n = len(per)
    need = _need(n, frac)

    l1_assets = [p["scene"] for p in per if p["l1"]["members"]]
    l1 = dict(n_assets=n, need_assets=need, assets_with_member=len(l1_assets),
              per_scene={p["scene"]: (p["l1"]["best"] or None) for p in per},
              verdict=len(l1_assets) >= need)

    l2_diffs = [p["l2"]["diff"] if p["l2"] else None for p in per]
    l2_ok = [p["scene"] for p in per if p["l2"] and p["l2"]["diff"] >= l2_gap]
    l2 = dict(window_pct=int(round(100 * window)), gap_pp=l2_gap, n_assets=n,
              need_assets=need, n_assets_with_pair=sum(1 for p in per if p["l2"]),
              median_diff_pp=_median(l2_diffs), assets_meeting_gap=len(l2_ok),
              assets_positive=sum(1 for d in l2_diffs if d is not None and d > 0),
              verdict=len(l2_ok) >= need)

    l3_ok = [p["scene"] for p in per if p["l3"] and p["l3"]["diff"] >= l3_gap]
    l3 = dict(band=band, gap_pp=l3_gap, n_assets=n, need_assets=need,
              n_assets_with_band=sum(1 for p in per if p["l3"]),
              median_diff_pp=_median([p["l3"]["diff"] if p["l3"] else None for p in per]),
              assets_meeting_gap=len(l3_ok), verdict=len(l3_ok) >= need)

    if l1["verdict"] and l2["verdict"]:
        outcome = "rvq_holds"
    elif l2["verdict"]:
        outcome = "rvq_beats_single_stage"
    elif l1["verdict"]:
        outcome = "frontier_only_rvq"
    else:
        outcome = "dead_write_N19"
    return dict(L1_near_lossless=l1, L2_rvq_vs_single=l2, L3_envelope=l3,
                outcome=outcome, scenes=per)


def render(res, title="M10 - two-stage dictionary (residual VQ)"):
    out = [f"# {title}", ""]
    l1, l2, l3 = res["L1_near_lossless"], res["L2_rvq_vs_single"], res["L3_envelope"]
    out += ["| criterion | verdict | detail |", "|---|---|---|"]
    out.append(f"| L1 near-lossless >= {L1_MIN_RATE:.0f}x, >= {l1['need_assets']}/{l1['n_assets']} "
               f"assets | **{'PASS' if l1['verdict'] else 'FAIL'}** | "
               f"{l1['assets_with_member']}/{l1['n_assets']} assets have a member |")
    out.append(f"| L2 residual stage beats single stage at +-{l2['window_pct']}% bytes "
               f"(>= {l2['gap_pp']} pp) | **{'PASS' if l2['verdict'] else 'FAIL'}** | "
               f"{l2['assets_meeting_gap']}/{l2['n_assets']} assets, median "
               f"{(l2['median_diff_pp'] or 0):+.2f} pp |")
    out.append(f"| L3 envelope owns {l3['band'][0]:.0f}-{l3['band'][1]:.0f}x "
               f"(>= {l3['gap_pp']} pp) | **{'PASS' if l3['verdict'] else 'FAIL'}** | "
               f"{l3['assets_meeting_gap']}/{l3['n_assets']} assets, median "
               f"{(l3['median_diff_pp'] or 0):+.2f} pp |")
    out += ["", f"**outcome: `{res['outcome']}`**", "", "## L1 - per asset", "",
            "| asset | best two-stage point | rate | drop pp | dPSNR | member |",
            "|---|---|---|---|---|---|"]
    for p in res["scenes"]:
        b = p["l1"]["best"]
        if not b:
            out.append(f"| {p['scene']} | - | - | - | - | no |")
            continue
        out.append(f"| {p['scene']} | `{b['variant']}` | {float(b['rate']):.2f}x | "
                   f"{float(b['drop_pp']):+.2f} | {float(b.get('d_psnr') or 0):+.3f} | "
                   f"{'yes' if p['l1']['members'] else 'no'} |")
    out += ["", "## L2 - two-stage vs single-stage at matched bytes", "",
            "| asset | two-stage | single | rate | drop two-stage | drop single | diff pp |",
            "|---|---|---|---|---|---|---|"]
    for p in res["scenes"]:
        q = p["l2"]
        if not q:
            out.append(f"| {p['scene']} | - | - | - | - | - | no pair |")
            continue
        out.append(f"| {p['scene']} | `{q['rvq']}` | `{q['single']}` | {q['rate']:.2f}x | "
                   f"{q['drop_rvq']:+.2f} | {q['drop_single']:+.2f} | {q['diff']:+.2f} |")
    out += ["", "## L3 - envelope over the target band", "",
            "| asset | two-stage best | rate | drop | other best | rate | drop | diff pp |",
            "|---|---|---|---|---|---|---|---|"]
    for p in res["scenes"]:
        e = p["l3"]
        if not e:
            out.append(f"| {p['scene']} | - | - | - | - | - | - | not covered |")
            continue
        out.append(f"| {p['scene']} | `{e['rvq']}` | {float(e['rvq_rate']):.2f}x | "
                   f"{e['rvq_drop']:+.2f} | `{e['other']}` | {float(e['other_rate']):.2f}x | "
                   f"{e['other_drop']:+.2f} | {e['diff']:+.2f} |")
    return "\n".join(out) + "\n"


def _synth(gain_pp, n=8, dpsnr_ok=True, base_drop=-1.9):
    """Synthetic world: RVQ is ``gain_pp`` better than the single stage everywhere."""
    scenes = []
    for i in range(n):
        rows = [dict(variant="clean", rate=1.0, drop_pp=0.0, d_psnr=0.0)]
        for b, bits in ((6, 12), (8, 14), (10, 16)):
            rows.append(dict(variant=f"vq{bits}_c8_o8", rate=18.0,
                             drop_pp=base_drop - 0.1, d_psnr=0.15))
        rows.append(dict(variant="c8_o8_sh2", rate=17.0, drop_pp=base_drop - 1.1,
                         d_psnr=0.2))
        for bits in (12, 14):
            rows.append(dict(variant=f"rvq8-{bits - 8}_c8_o8", rate=18.2,
                             drop_pp=base_drop + gain_pp,
                             d_psnr=(0.15 if dpsnr_ok else -0.4)))
        rows.append(dict(variant="p30_rvq10-4_c8_o8", rate=60.0, drop_pp=-14.0,
                         d_psnr=4.0))
        scenes.append(dict(scene=f"s{i}", rows=rows))
    return dict(scenes=scenes)


def selftest():
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        print(f"  [{'ok' if cond else 'FAIL'}] {label} {detail}")
        ok = ok and bool(cond)

    res = evaluate(_synth(2.0))
    check("a two-stage dictionary clears the near-lossless gate",
          res["L1_near_lossless"]["verdict"],
          f"{res['L1_near_lossless']['assets_with_member']}/8")
    check("L2 passes when the residual stage wins by 2 pp",
          res["L2_rvq_vs_single"]["verdict"],
          f"{res['L2_rvq_vs_single']['median_diff_pp']:+.2f} pp")
    check("outcome is the full claim", res["outcome"] == "rvq_holds", res["outcome"])

    res = evaluate(_synth(0.1, base_drop=-0.6))
    check("a 0.1 pp residual gain fails L2", not res["L2_rvq_vs_single"]["verdict"],
          f"{res['L2_rvq_vs_single']['median_diff_pp']:+.2f} pp")
    check("outcome downgrades to the frontier claim",
          res["outcome"] == "frontier_only_rvq", res["outcome"])

    res = evaluate(_synth(2.0, dpsnr_ok=False))
    check("a dPSNR below zero never counts as near-lossless",
          not res["L1_near_lossless"]["verdict"],
          f"{res['L1_near_lossless']['assets_with_member']}/8")
    check("L2 still passes without the near-lossless claim",
          res["outcome"] == "rvq_beats_single_stage", res["outcome"])

    res = evaluate(_synth(0.0), l3_gap=1.0)
    check("L3 fails when the envelope is flat", not res["L3_envelope"]["verdict"],
          f"{res['L3_envelope']['median_diff_pp']:+.2f} pp")
    print("=" * 60)
    print("ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.json:
        ap.error("--json is required unless --selftest")
    with open(args.json, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    res = evaluate(doc)
    text = render(res)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"WROTE {args.out}")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
