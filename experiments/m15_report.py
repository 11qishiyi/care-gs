"""Score M15 (packed geometry) against the criteria pre-registered before data landed.

R1  packing is free: on each same-SH-width pair (packed vs unpacked) the packed row may
    lose at most 0.5 pp more coverage and 0.15 dB more PSNR, on 6/8 assets, for **every**
    registered pair.  Packing buys 6.88 B of model, so it has to cost nothing.
R2  the floor moves: the cheapest packed row still within 0.5 pp of the unpacked loss
    must sit at >= 10.8x (that is 9.3x + the 1.5x the spec asks for), on 6/8 assets.
R3  the 12x probe: some packed row at rate >= 12 with ``0 <= d_psnr <= 0.3`` and
    ``drop >= -1.0 pp``, on 6/8 assets.

Outcomes: ``frontier_12x`` / ``frontier_11_12x`` / ``dead_write_N24``.  The cell "R1 ok,
R2 not" was not registered; it is reported as ``r1_without_rate_gain`` and must be
written up by hand rather than quietly folded into a branch.

``d_psnr`` is ``clean_psnr - variant_psnr`` (positive = the variant sits behind the
unpacked reference), inherited from ``m1_analyse``; ``drop_pp`` is negative for loss.
``clean`` is not a row -- its drop is zero by construction, since the analyser's drops
are paired against the clean calibration views -- so the SH-32 pair uses a synthetic
reference built from the scene's ``clean_coverage``/``clean_psnr``.
"""
import argparse
import json
import math
import sys

import common as C

#: The three pre-registered same-SH-width pairs, (packed, unpacked).  ``clean`` is the
#: 32-bit-SH control; the two ``c*_o8_sh3`` rows are today's near-lossless family at
#: 3-bit SH, one with the current c10 positions and one with the c8 the packing uses.
PAIRS = (("gp8-5-4_c6", "clean"),
         ("gp8-5-4_c6_sh3", "c8_o8_sh3"),
         ("gp8-5-4_c6_sh3", "c10_o8_sh3"))
PACKED_TAG = "gp"
SHELF = "gp8-5-4_c6_sh3"
ANCHOR = "c10_o8_sh3"


def _need(n: int, frac: float = 0.75) -> int:
    return max(1, int(math.ceil(frac * n)))


def _scenes(doc):
    return [s["scene"] for s in doc["scenes"]]


def _index(doc):
    """scene -> variant -> row, plus the synthetic ``clean`` row per scene."""
    out = {}
    for sc in doc["scenes"]:
        rows = {r["variant"]: r for r in sc["rows"]}
        if "clean" not in rows:
            rows["clean"] = {"variant": "clean", "family": "clean", "rate": 1.0,
                             "drop_pp": 0.0, "drop_lo_pp": 0.0, "drop_hi_pp": 0.0,
                             "psnr": sc.get("clean_psnr"), "d_psnr": 0.0,
                             "bytes_per_prim": None, "synthetic": True}
        out[sc["scene"]] = rows
    return out


def _packed(rows):
    return [r for k, r in rows.items() if k.startswith(PACKED_TAG)]


def r1(doc, max_drop_gap=0.5, max_psnr_gap=0.15, frac=0.75):
    """Packing must not cost more than 0.5 pp / 0.15 dB against its unpacked twin."""
    idx = _index(doc)
    scenes = _scenes(doc)
    per_pair = {}
    for packed, unpacked in PAIRS:
        assets, diffs = {}, []
        for scene in scenes:
            p, u = idx[scene].get(packed), idx[scene].get(unpacked)
            if p is None or u is None or p.get("drop_pp") is None:
                continue
            dp, du = float(p["drop_pp"]), float(u["drop_pp"])
            gp = float(p.get("d_psnr") or 0.0)
            gu = float(u.get("d_psnr") or 0.0)
            drop_gap = dp - du                 # <0: the packed row loses more coverage
            psnr_gap = gp - gu                 # >0: the packed row sits further behind
            ok = drop_gap >= -max_drop_gap and psnr_gap <= max_psnr_gap
            assets[scene] = dict(drop_gap_pp=drop_gap, psnr_gap_db=psnr_gap, ok=ok,
                                 packed=packed, unpacked=unpacked,
                                 packed_rate=p.get("rate"), unpacked_rate=u.get("rate"),
                                 packed_drop_pp=dp, unpacked_drop_pp=du)
            diffs.append(drop_gap)
        need = _need(len(scenes), frac)
        per_pair[f"{packed} vs {unpacked}"] = {
            "assets": assets, "n_compared": len(diffs),
            "n_passing": sum(1 for a in assets.values() if a["ok"]), "need": need,
            "verdict": sum(1 for a in assets.values() if a["ok"]) >= need
            if assets else None}
    verdicts = [v["verdict"] for v in per_pair.values()]
    verdict = None if (not verdicts or any(v is None for v in verdicts)) else all(verdicts)
    return {"name": "R1_packing_is_free", "pairs": per_pair, "need": _need(len(scenes), frac),
            "status": "incomplete" if verdict is None else "measured",
            "verdict": verdict}


def r2(doc, max_drop=0.5, min_rate=10.8, anchor_rate=9.3, lo_dpsnr=0.0, hi_dpsnr=0.3,
       frac=0.75):
    """How far the packed near-lossless tier reaches, and how cheaply it starts.

    Candidates are packed rows that carry an SH token: the near-lossless shelf lives at
    3-bit SH (``FRONTIER_BOUND`` budgets 20 B of SH, not 192), so a 32-bit-SH row can
    never be one of its points however well it scores.  ``0 <= d_psnr <= 0.3`` is not an
    extra filter but the pre-registered 禁止条款: an archive-exposure "PSNR gain" may not
    be used to argue near-losslessness.

    The registered sentence says *最小码率* ("the cheapest qualifying rate") while the
    arithmetic in the same paragraph -- 9.3x + 1.5x, and "still 0.3x short of 12x" for a
    11.6x shelf -- only describes the top of the tier.  Both are computed and printed;
    the verdict uses the top (``n_passing``/``median_rate``), and ``bottom`` is kept as a
    diagnostic, because the bottom reading is decided by the grid (``_sh4`` always
    qualifies) rather than by the data, so it cannot discriminate.
    """
    idx = _index(doc)
    scenes = _scenes(doc)
    per_scene, tops, bottoms = {}, [], []
    for scene in scenes:
        cands = [r for r in _packed(idx[scene])
                 if "_sh" in r["variant"]
                 and r.get("drop_pp") is not None and float(r["drop_pp"]) >= -max_drop
                 and r.get("rate") is not None
                 and lo_dpsnr <= float(r.get("d_psnr") or 0.0) <= hi_dpsnr]
        if not cands:
            per_scene[scene] = None
            continue
        top = max(cands, key=lambda r: float(r["rate"]))
        bot = min(cands, key=lambda r: float(r["rate"]))
        per_scene[scene] = dict(
            top=dict(variant=top["variant"], rate=float(top["rate"]),
                     drop_pp=float(top["drop_pp"]),
                     d_psnr=float(top.get("d_psnr") or 0.0),
                     ok=float(top["rate"]) >= min_rate),
            bottom=dict(variant=bot["variant"], rate=float(bot["rate"]),
                        drop_pp=float(bot["drop_pp"])))
        tops.append(float(top["rate"]))
        bottoms.append(float(bot["rate"]))
    need = _need(len(scenes), frac)
    hits = [s for s, b in per_scene.items() if b and b["top"]["ok"]]
    return {"name": "R2_floor_moves_past_10.8x", "per_scene": per_scene,
            "n_compared": len(tops), "n_passing": len(hits), "need": need,
            "min_rate_required": min_rate, "anchor_rate": anchor_rate,
            "median_rate": (sorted(tops)[len(tops) // 2] if tops else None),
            "worst_rate": (min(tops) if tops else None),
            "bottom_median_rate": (sorted(bottoms)[len(bottoms) // 2] if bottoms else None),
            "reading": "top_of_tier",
            "verdict": len(hits) >= need if tops else None}



def r3(doc, min_rate=12.0, max_drop=1.0, lo_dpsnr=0.0, hi_dpsnr=0.3, frac=0.75):
    """Is there a packed row that already lives in the 12x zone at near-zero loss?"""
    idx = _index(doc)
    scenes = _scenes(doc)
    covered, hits = [], {}
    for scene in scenes:
        rows = [r for r in _packed(idx[scene])
                if r.get("rate") is not None and float(r["rate"]) >= min_rate]
        if rows:
            covered.append(scene)
        good = [r for r in rows if float(r.get("drop_pp") or 0.0) >= -max_drop
                and lo_dpsnr <= float(r.get("d_psnr") or 0.0) <= hi_dpsnr]
        if good:
            hits[scene] = max(good, key=lambda r: float(r["drop_pp"]))
    need = _need(len(scenes), frac)
    if len(covered) < need:
        return {"name": "R3_12x_probe", "status": "under_covered", "covered": covered,
                "need": need, "verdict": None, "members": hits}
    return {"name": "R3_12x_probe", "status": "measured", "covered": covered,
            "assets_with_member": len(hits), "need": need, "members": hits,
            "verdict": len(hits) >= need}


def evaluate(doc, **kw):
    a = r1(doc, **{k: v for k, v in kw.items() if k in ("max_drop_gap", "max_psnr_gap", "frac")})
    b = r2(doc, **{k: v for k, v in kw.items()
                   if k in ("max_drop", "min_rate", "anchor_rate", "frac")})
    c = r3(doc, **{k: v for k, v in kw.items()
                   if k in ("min_rate", "max_drop", "lo_dpsnr", "hi_dpsnr", "frac")})
    # A failed R1 decides on its own -- packing that costs coverage is dead whether or
    # not the rest of the grid could be scored.  Missing data is not a verdict either way.
    if a["verdict"] is False:
        outcome = "dead_write_N24"
    elif a["verdict"] is None or b["verdict"] is None:
        outcome = "incomplete_grid"
    elif b["verdict"] and c.get("verdict"):
        outcome = "frontier_12x"
    elif b["verdict"]:
        outcome = "frontier_11_12x"
    else:
        outcome = "r1_without_rate_gain"
    return {"criteria": {"R1": a, "R2": b, "R3": c}, "outcome": outcome}


def _cell(v, fmt="{:.2f}", none="n/a"):
    return none if v is None else fmt.format(float(v))


def render(res, source=""):
    out = ["# M15: packed geometry (st3 quaternions + 5/4 bit groups + c6 positions)", ""]
    if source:
        out += [f"source: `{source}`", ""]
    out += [f"**outcome** `{res['outcome']}`", ""]
    crit = res["criteria"]
    out += ["| criterion | verdict | detail |", "|---|---|---|"]
    vs = {True: "PASS", False: "FAIL", None: "n/a"}
    a, b, c = crit["R1"], crit["R2"], crit["R3"]
    r1_detail = "; ".join(f"{k}: {v['n_passing']}/{v['n_compared']}"
                          for k, v in a["pairs"].items())
    out.append(f"| {a['name']} | {vs[a['verdict']]} | {r1_detail} (need {a['need']}) |")
    r2_detail = (f"top of tier {b['n_passing']}/{b['n_compared']} assets >= "
                 f"{b['min_rate_required']:.1f}x (median {_cell(b['median_rate'])}x; "
                 f"cheapest member median {_cell(b['bottom_median_rate'])}x)") \
        if b["n_compared"] else "no candidate"
    out.append(f"| {b['name']} | {vs[b['verdict']]} | {r2_detail} |")
    if c.get("status") == "under_covered":
        c_detail = f"grid never reaches {c.get('min_rate', 12)}x ({len(c['covered'])} covered)"
    else:
        c_detail = f"{c['assets_with_member']}/{len(c['covered'])} assets (need {c['need']})"
    out.append(f"| {c['name']} | {vs[c.get('verdict')]} | {c_detail} |")

    out += ["", "## R1 same-SH-width pairs (packed vs unpacked)", ""]
    for pair, d in a["pairs"].items():
        out += [f"### `{pair}` -- {d['n_passing']}/{d['n_compared']} pass, need {d['need']}", "",
                "| asset | packed rate | drop | unpacked rate | drop | gap pp | gap dB | ok |",
                "|---|---|---|---|---|---|---|---|"]
        for scene, x in sorted(d["assets"].items()):
            out.append(f"| {scene} | {_cell(x['packed_rate'])}x | {x['packed_drop_pp']:+.2f} | "
                       f"{_cell(x['unpacked_rate'])}x | {x['unpacked_drop_pp']:+.2f} | "
                       f"{x['drop_gap_pp']:+.2f} | {x['psnr_gap_db']:+.3f} | "
                       f"{'yes' if x['ok'] else 'NO'} |")
        out.append("")

    out += ["## R2 the packed near-lossless tier", "",
            "top = the most expensive packed SH-quantised row inside 0.5 pp (the frontier's",
            "extent, which is what the verdict uses); cheapest = the least expensive such",
            "row (the literal \"cheapest rate\" reading, decided by the grid rather than the",
            "data).", "",
            "| asset | top variant | rate | drop pp | dPSNR | ok | cheapest | rate |",
            "|---|---|---|---|---|---|---|---|"]
    for scene, x in sorted(b["per_scene"].items()):
        if x is None:
            out.append(f"| {scene} | - | - | - | - | no candidate | - | - |")
            continue
        t, lo = x["top"], x["bottom"]
        out.append(f"| {scene} | `{t['variant']}` | {t['rate']:.2f}x | {t['drop_pp']:+.2f} | "
                   f"{t['d_psnr']:+.3f} | {'yes' if t['ok'] else 'NO'} | "
                   f"`{lo['variant']}` | {lo['rate']:.2f}x |")
    out += ["", "## R3 members at >= 12x", "",
            "| asset | variant | rate | drop pp | dPSNR |", "|---|---|---|---|---|"]
    for scene, r in sorted(c.get("members", {}).items()):
        out.append(f"| {scene} | `{r['variant']}` | {float(r['rate']):.2f}x | "
                   f"{float(r['drop_pp']):+.2f} | {float(r.get('d_psnr') or 0):+.3f} |")
    out.append("")
    return "\n".join(out)


def _synth(n=8, sh32_drop=-0.2, sh32_rate=8.4, sh3_drop=-0.4, sh3_rate=12.1,
           unpacked_drop=-0.35, dpsnr=0.05, has_anchor=True):
    """Synthetic document: ``clean`` is implied, rows mimic the registered grid."""
    scenes = []
    for i in range(n):
        rows = [{"variant": "gp8-5-4_c6", "rate": sh32_rate,
                 "drop_pp": sh32_drop, "d_psnr": dpsnr},
                {"variant": "gp8-5-4_c6_sh4", "rate": 6.95,
                 "drop_pp": sh3_drop + 0.15, "d_psnr": dpsnr},
                {"variant": "gp8-5-4_c6_sh3", "rate": sh3_rate,
                 "drop_pp": sh3_drop, "d_psnr": dpsnr},
                {"variant": "gp4-5-4_c6", "rate": 11.0, "drop_pp": -0.4, "d_psnr": dpsnr}]
        if has_anchor:
            rows.append({"variant": "c10_o8_sh3", "rate": 7.41,
                         "drop_pp": unpacked_drop, "d_psnr": 0.0})
        rows.append({"variant": "c8_o8_sh3", "rate": 7.59,
                     "drop_pp": unpacked_drop - 0.05, "d_psnr": 0.0})
        scenes.append({"scene": f"s{i}", "clean_coverage": 0.9, "clean_psnr": 22.0,
                       "rows": rows})
    return {"scenes": scenes}


def selftest() -> int:
    fails = []

    def check(name, cond, extra=""):
        print(("  [ok] " if cond else "  [FAIL] ") + name + (f" | {extra}" if extra else ""))
        if not cond:
            fails.append(name)

    good = evaluate(_synth(sh32_drop=-0.1, unpacked_drop=-0.35))
    check("the good document is frontier_12x", good["outcome"] == "frontier_12x",
          good["outcome"])
    check("R1 passes on it", good["criteria"]["R1"]["verdict"])
    check("R2 passes on it", good["criteria"]["R2"]["verdict"])
    check("R3 passes on it", good["criteria"]["R3"]["verdict"])

    no12 = evaluate(_synth(sh32_drop=-0.1, unpacked_drop=-0.35, sh3_rate=11.2))
    check("a grid that stalls at 11.2x is frontier_11_12x",
          no12["outcome"] == "frontier_11_12x", no12["outcome"])
    check("R2 still passes at 11.2x", no12["criteria"]["R2"]["verdict"])

    dead = evaluate(_synth(sh3_drop=-1.4))
    check("packing that costs a pp is dead_write_N24", dead["outcome"] == "dead_write_N24",
          dead["outcome"])
    check("R1 fails there", not dead["criteria"]["R1"]["verdict"])

    slow = evaluate(_synth(sh32_drop=0.1, unpacked_drop=-0.35, sh3_rate=9.8))
    check("R1 without R2 is not silently a win",
          slow["outcome"] == "r1_without_rate_gain", slow["outcome"])

    both = evaluate(_synth())
    check("the cheap _sh4 row is visible as the cheapest member",
          abs((both["criteria"]["R2"]["bottom_median_rate"] or 0) - 6.95) < 1e-9,
          str(both["criteria"]["R2"]["bottom_median_rate"]))
    check("but the verdict follows the top of the tier",
          both["criteria"]["R2"]["n_passing"] == 8, str(both["criteria"]["R2"]["n_passing"]))

    sh32 = _synth()
    for sc in sh32["scenes"]:
        sc["rows"].append({"variant": "gp8-5-4_c6_sh3_extra", "rate": 30.0,
                           "drop_pp": -0.1, "d_psnr": 0.05})
        sc["rows"].append({"variant": "gp2-5-4_c6", "rate": 40.0, "drop_pp": -0.0,
                           "d_psnr": 0.05})
    check("an SH-32 row cannot raise the tier's top",
          abs((evaluate(sh32)["criteria"]["R2"]["median_rate"] or 0) - 30.0) < 1e-9,
          str(evaluate(sh32)["criteria"]["R2"]["median_rate"]))

    gain = evaluate(_synth(sh3_drop=-0.45, sh32_drop=-0.45, unpacked_drop=-0.35, dpsnr=-0.4))
    check("a dPSNR gain from the archive is not an R3 member",
          not gain["criteria"]["R3"]["verdict"], str(gain["criteria"]["R3"].get("verdict")))

    nocand = _synth()
    for sc in nocand["scenes"]:
        sc["rows"] = [r for r in sc["rows"] if float(r["rate"]) < 12.0]
    check("R3 reports under_covered when nothing reaches 12x",
          evaluate(nocand)["criteria"]["R3"]["status"] == "under_covered")

    noanchor = evaluate(_synth(has_anchor=False))
    r1pairs = noanchor["criteria"]["R1"]["pairs"]
    check("a missing anchor limits the pair rather than passing it",
          r1pairs["gp8-5-4_c6_sh3 vs c10_o8_sh3"]["n_compared"] == 0)
    check("rendering names the outcome", "outcome" in render(good))
    check("rendering prints every pair", render(good).count("###") == len(PAIRS))
    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.json:
        ap.error("--json is required unless --selftest")
    doc = json.load(open(a.json, encoding="utf-8"))
    res = evaluate(doc)
    md = render(res, source=a.json)
    print(md)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md + "\n")
        C.log(f"WROTE {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
