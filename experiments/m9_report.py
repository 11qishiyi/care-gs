"""M9 report: does a view-dependent dictionary beat per-coefficient SH coding?

Reads ``m9_rd.json`` (measured-byte axis) and applies the preregistered criteria
(METHOD_PLAN.md "M9 规格"):

  K1  a *qualified* near-lossless member exists at >= 12x on >= 6/8 assets
      (qualified = |coverage loss| <= 1.0 pp, dPSNR in [0, 0.3] dB, so a member cannot
      pass by gaining PSNR from the archive's GT exposure mismatch)
  K2  at matched bytes (a +-15 % window), the dictionary family loses >= 1.0 pp less
      coverage than the per-coefficient family, on >= 6/8 assets
  K3  the codebook is paid for: every dictionary row must carry its codebook bytes,
      and the share of the file it takes is reported (an unpaid dictionary is not a
      codec, so it may not be used to claim a rate)

Nothing here may be re-tuned after the numbers exist.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1_analyse as A                                          # noqa: E402

VQ_TAG = "vq"


def is_vq(name: str) -> bool:
    return VQ_TAG in name


def is_scalar_sh(name: str) -> bool:
    return (not is_vq(name)) and ("sh" in name) and name != "clean"


def _need(n: int, frac: float = 0.75) -> int:
    return max(1, int(-(-frac * n // 1)))


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else 0.5 * (xs[m - 1] + xs[m])


def evaluate(doc: dict, min_rate: float = 12.0, max_drop: float = 1.0,
             max_dpsnr: float = 0.3, window: float = 0.15, gap_pp: float = 1.0,
             frac: float = 0.75, bytes_doc: dict = None) -> dict:
    scenes = doc.get("scenes", [])
    stored = {}
    for sc_b in (bytes_doc or {}).get("scenes", []):
        for row in sc_b.get("rows", []):
            stored[(sc_b.get("scene"), row.get("spec"))] = row.get("stored")
    per = []
    for sc in scenes:
        rows = sc.get("rows", [])
        # K1: qualified near-lossless member at a high rate
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
        # K2: dictionary vs per-coefficient at matched bytes
        vq = [r for r in rows if is_vq(r["variant"]) and r.get("bytes_per_prim")]
        sc_rows = [r for r in rows if is_scalar_sh(r["variant"]) and r.get("bytes_per_prim")]
        pairs = []
        for r in vq:
            b = float(r["bytes_per_prim"])
            cand = [q for q in sc_rows if abs(float(q["bytes_per_prim"]) - b) <= window * b]
            if not cand:
                continue
            q = max(cand, key=lambda z: z["drop_pp"])
            pairs.append(dict(vq_variant=r["variant"], vq_bpp=round(b, 2),
                              vq_drop_pp=r["drop_pp"], vq_rate=r["rate"],
                              scalar_variant=q["variant"],
                              scalar_bpp=round(float(q["bytes_per_prim"]), 2),
                              scalar_drop_pp=q["drop_pp"], scalar_rate=q["rate"],
                              diff_pp=float(r["drop_pp"]) - float(q["drop_pp"])))
        k2 = None
        if pairs:
            bp = max(pairs, key=lambda p: p["diff_pp"])
            k2 = dict(best=bp, n_pairs=len(pairs),
                      median_diff_pp=_median([p["diff_pp"] for p in pairs]))        # K3: codebook ledger.  The rd json carries no byte accounting, so the codebook
        # size is recomputed from the name (the model the whole round uses) and the
        # stored primitive count comes from the bytes json when it is available.
        cb = []
        for r in vq:
            spec = A.parse_spec(r["variant"])
            vq_bits = spec[5]
            deg_scene = int(sc.get("sh_degree") or 3)
            deg_out = deg_scene if spec[3] is None else min(int(spec[3]), deg_scene)
            cols = A.sh_cols(deg_out)
            code = float(A.vq_codebook_bytes(int(vq_bits), cols)) if vq_bits else 0.0
            n_st = stored.get((sc.get("scene"), r["variant"])) if stored else None
            bpp = r.get("bytes_per_prim")
            share = (code / (float(bpp) * float(n_st))
                     if (n_st and bpp) else None)
            cb.append(dict(variant=r["variant"], codebook_bytes=code, bpp=bpp,
                           stored=n_st, share=share))
        per.append(dict(scene=sc.get("scene"), k1_member=best, k2=k2, k3=cb,
                        n_vq=len(vq), n_scalar=len(sc_rows)))
    n = len(per)
    need = _need(n, frac)
    k1 = dict(min_rate=min_rate, max_drop_pp=max_drop, max_dpsnr=max_dpsnr,
              require_dpsnr_nonneg=True, n_assets=n, need_assets=need,
              assets_with_member=sum(1 for p in per if p["k1_member"]),
              members={p["scene"]: p["k1_member"] for p in per if p["k1_member"]})
    k1["verdict"] = k1["assets_with_member"] >= need
    diffs = [p["k2"]["median_diff_pp"] for p in per if p["k2"]]
    k2 = dict(window_pct=int(window * 100), gap_pp=gap_pp, n_assets=n, need_assets=need,
              n_assets_with_pair=len(diffs), median_diff_pp=_median(diffs),
              assets_positive=sum(1 for d in diffs if d > 0),
              assets_meeting_gap=sum(1 for d in diffs if d >= gap_pp))
    k2["verdict"] = k2["assets_meeting_gap"] >= need
    unpaid = [p["scene"] for p in per for c in p["k3"] if not c["codebook_bytes"]]
    shares = [c["share"] for p in per for c in p["k3"] if c["share"] is not None]
    sizes = [c["codebook_bytes"] for p in per for c in p["k3"] if c["codebook_bytes"]]
    k3 = dict(rows_without_codebook=len(unpaid), scenes=sorted(set(unpaid)),
              median_codebook_share=_median(shares), max_codebook_share=max(shares or [0.0]),
              max_codebook_bytes=max(sizes or [0.0]), n_measured_shares=len(shares))
    # A dictionary whose size cannot be checked against the file is not "paid for":
    # the ledger only passes when every dictionary row got a measured share.
    n_vq_rows = sum(len(p["k3"]) for p in per)
    k3["n_vq_rows"] = n_vq_rows
    k3["verdict"] = (not unpaid) and n_vq_rows > 0 and k3["n_measured_shares"] == n_vq_rows
    if k1["verdict"] and k2["verdict"] and k3["verdict"]:
        outcome = "vq_dictionary_holds"
    elif k1["verdict"] and k3["verdict"]:
        outcome = "frontier_only_vq"
    elif k2["verdict"] and k3["verdict"]:
        outcome = "vq_beats_scalar_only"
    else:
        outcome = "dead_write_N18"
    return dict(scenes=per, K1_frontier_12x=k1, K2_vq_vs_scalar=k2, K3_codebook=k3,
                outcome=outcome, meta=doc.get("meta", {}))


def render(res: dict) -> str:
    k1, k2, k3 = res["K1_frontier_12x"], res["K2_vq_vs_scalar"], res["K3_codebook"]
    L = ["# M9 — view-dependent dictionary (vector-quantised SH)\n",
         f"rate axis: `{res['meta'].get('rate_source', '?')}` "
         f"(measured bytes when available)\n",
         "| criterion | verdict | detail |", "|---|---|---|",
         f"| K1 near-lossless >= {k1['min_rate']:.0f}x, >= {k1['need_assets']}/{k1['n_assets']} assets "
         f"| **{'PASS' if k1['verdict'] else 'FAIL'}** | "
         f"{k1['assets_with_member']}/{k1['n_assets']} assets have a member |",
         f"| K2 VQ beats scalar SH at +-{k2['window_pct']}% bytes | "
         f"**{'PASS' if k2['verdict'] else 'FAIL'}** | "
         f"{k2['assets_meeting_gap']}/{k2['n_assets']} assets >= {k2['gap_pp']:.1f} pp |",
         f"| K3 codebook is paid for | **{'PASS' if k3['verdict'] else 'FAIL'}** | "
         f"median share {100 * (k3['median_codebook_share'] or 0):.2f}% of the file |",
         "", f"**outcome: `{res['outcome']}`**", "",
         "## K1 — best qualified member above 12x", "",
         "| asset | member | rate | coverage loss | dPSNR |", "|---|---|---|---|---|"]
    for p in res["scenes"]:
        m = p["k1_member"]
        if m:
            L.append(f"| {p['scene']} | `{m['variant']}` | {m['rate']:.2f}x | "
                     f"{m['drop_pp']:+.2f} pp | {m['d_psnr']:+.3f} dB |")
        else:
            L.append(f"| {p['scene']} | — | — | — | — |")
    L += ["", "## K2 — dictionary vs per-coefficient at matched bytes", "",
          "| asset | dictionary | B/prim | loss | per-coefficient | B/prim | loss | diff |",
          "|---|---|---|---|---|---|---|---|"]
    for p in res["scenes"]:
        k = p["k2"]
        if not k:
            L.append(f"| {p['scene']} | — | — | — | — | — | — | no pair |")
            continue
        b = k["best"]
        L.append(f"| {p['scene']} | `{b['vq_variant']}` | {b['vq_bpp']:.2f} | "
                 f"{b['vq_drop_pp']:+.2f} | `{b['scalar_variant']}` | {b['scalar_bpp']:.2f} | "
                 f"{b['scalar_drop_pp']:+.2f} | **{b['diff_pp']:+.2f}** |")
    L += ["", "## K3 — codebook ledger", "",
          "| asset | variant | B/prim | codebook | share of file |", "|---|---|---|---|---|"]
    for p in res["scenes"]:
        for c in p["k3"]:
            share = "n/a" if c["share"] is None else f"{100 * c['share']:.2f}%"
            bpp = "n/a" if c["bpp"] is None else f"{c['bpp']:.2f}"
            cb = "n/a" if c["codebook_bytes"] is None else f"{c['codebook_bytes']:.0f} B"
            L.append(f"| {p['scene']} | `{c['variant']}` | {bpp} | {cb} | {share} |")
    return "\n".join(L) + "\n"


def selftest() -> int:
    """Two synthetic worlds: one where the dictionary wins, one where it does not."""
    def world(dict_gain_pp: float, with_codebook: bool = True) -> dict:
        rows = []
        for name, bpp, drop in (("c10_o8_sh3", 31.8, -1.6), ("c12_o8_sh2", 26.6, -2.5),
                                ("d0_c8_o6_sh2", 11.8, -6.0), ("d0_c8_o8_sh2", 13.8, -5.4),
                                ("d0_c10_o6_sh2", 12.6, -5.8)):
            rows.append(dict(variant=name, bytes_per_prim=bpp, drop_pp=drop, rate=236.0 / bpp,
                             d_psnr=0.05))
        for name, bpp, drop in (("vq6_c8_o8", 11.8, -6.0 + dict_gain_pp),
                                ("vq10_c8_o8", 12.35, -5.8 + dict_gain_pp),
                                ("vq12_c10_o8", 13.4, -5.4 + dict_gain_pp),
                                # a strong member *outside* the matched-byte band, so the
                                # K1 frontier and the K2 comparison stay independent
                                ("vq14_c8_o8", 18.0, -0.4)):
            rows.append(dict(variant=name, bytes_per_prim=bpp, drop_pp=drop,
                             rate=236.0 / bpp, d_psnr=0.02,
                             codebook_bytes=1024.0 if with_codebook else None))
        scenes = []
        for i in range(8):
            sc = [dict(r) for r in rows]
            scenes.append(dict(scene=f"s{i}", rows=sc, n_stored=5_000_000))
        return dict(scenes=scenes, meta=dict(rate_source="measured"))

    fails = []

    def check(name, cond, detail=""):
        print(f"  [{'ok' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails.append(name)

    def ledger(doc, stored=5_000_000):
        return dict(scenes=[dict(scene=sc["scene"],
                                 rows=[dict(spec=r["variant"], stored=stored)
                                       for r in sc["rows"]])
                            for sc in doc["scenes"]])

    doc = world(0.0)
    res = evaluate(doc, bytes_doc=ledger(doc))
    check("a dictionary at fewer bytes passes K1", res["K1_frontier_12x"]["verdict"],
          f"{res['K1_frontier_12x']['assets_with_member']}/8")
    check("K2 fails when the dictionaries do not beat the scalar rows",
          not res["K2_vq_vs_scalar"]["verdict"], str(res["K2_vq_vs_scalar"]["median_diff_pp"]))
    check("outcome falls back to the frontier claim", res["outcome"] == "frontier_only_vq",
          res["outcome"])
    check("the codebook share is reported", res["K3_codebook"]["verdict"],
          f"median {100 * (res['K3_codebook']['median_codebook_share'] or 0):.3f}%")

    doc = world(3.0)
    res = evaluate(doc, bytes_doc=ledger(doc))
    check("K2 passes when the dictionary wins by >= 1 pp",
          res["K2_vq_vs_scalar"]["verdict"],
          f"{res['K2_vq_vs_scalar']['assets_meeting_gap']}/8")
    check("outcome is the full claim", res["outcome"] == "vq_dictionary_holds", res["outcome"])

    res = evaluate(world(3.0))
    check("an unmeasurable ledger fails K3", not res["K3_codebook"]["verdict"],
          str(res["K3_codebook"]["n_measured_shares"]))
    check("outcome refuses to claim anything without the ledger",
          res["outcome"] == "dead_write_N18", res["outcome"])

    res = evaluate(dict(scenes=[dict(scene="s", rows=[dict(variant="c8_o8_sh3",
                                                           bytes_per_prim=31.0,
                                                           drop_pp=-1.0, rate=7.6,
                                                           d_psnr=0.1)],
                                 n_stored=1000)], meta={}))
    check("no dictionary at all is a dead end", res["outcome"] == "dead_write_N18", res["outcome"])

    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M9 verdict: dictionary-coded SH")
    ap.add_argument("--json", default="experiments/artifacts/a4/m9_rd.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-rate", type=float, default=12.0)
    ap.add_argument("--gap-pp", type=float, default=1.0)
    ap.add_argument("--window", type=float, default=0.15)
    ap.add_argument("--bytes", default=None,
                    help="m9_bytes.json; only used to turn the codebook into a share "
                         "of the file (the rd json carries no byte accounting)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    with open(args.json, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    bytes_doc = None
    if args.bytes and os.path.exists(args.bytes):
        with open(args.bytes, "r", encoding="utf-8") as fh:
            bytes_doc = json.load(fh)
    res = evaluate(doc, min_rate=args.min_rate, gap_pp=args.gap_pp, window=args.window,
                   bytes_doc=bytes_doc)
    md = render(res)
    out = args.out or os.path.splitext(args.json)[0].replace("_rd", "_report") + ".md"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md)
    print(f"WROTE {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
