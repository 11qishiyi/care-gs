"""Score M11 (per-primitive mode selection) against its registered criteria.

P1  near-lossless shelf at 12x: at least 6/8 assets own a ``msc`` member that is at
    >= 12x, loses at most 1.0 pp of coverage, and does not gain PSNR from the
    archive's exposure mismatch (``0 <= d_psnr <= 0.3``).
P2  bytes-for-bytes: at a matched measured rate (within +/-10%) an ``msc`` member must
    lose at least 0.5 pp less coverage than the best single-family member, on 6/8.
P3  18-20x: an ``msc`` member loses at most 1.0 pp.  If the grid does not reach that
    window at all the criterion is reported ``under_covered``, never ``fail``
    (the M7 lesson: a criterion needs a matching grid, otherwise it measures nothing).
"""
import argparse
import json
import os
import sys

import common as C

MSC_TAG = "msc"
COMPETITORS = ("scalar", "vq", "rvq")


def is_msc(name: str) -> bool:
    return MSC_TAG in name.split("_")[0] or MSC_TAG in name


def family_of(name: str) -> str:
    head = name.split("_")
    for tok in head:
        if tok.startswith("msc"):
            return "msc"
        if tok.startswith("rvq"):
            return "rvq"
        if tok.startswith("vq"):
            return "vq"
        if tok.startswith("p") and tok[1:].isdigit():
            return "prune"
        if tok == "clean":
            return "clean"
    return "scalar"


def _need(n: int, frac: float = 0.75) -> int:
    import math
    return max(1, int(math.ceil(frac * n)))


def _rows(doc):
    for sc in doc["scenes"]:
        for r in sc["rows"]:
            r.setdefault("scene", sc["scene"])
            yield sc["scene"], r


def p1(doc, min_rate=12.0, max_drop=1.0, lo_dpsnr=0.0, hi_dpsnr=0.3, frac=0.75):
    scenes = [s["scene"] for s in doc["scenes"]]
    hits = {}
    for scene, r in _rows(doc):
        if family_of(r["variant"]) != "msc":
            continue
        d = float(r.get("d_psnr") or 0.0)
        if (float(r["rate"]) >= min_rate and float(r["drop_pp"]) >= -max_drop
                and lo_dpsnr <= d <= hi_dpsnr):
            best = hits.get(scene)
            if best is None or float(r["drop_pp"]) > float(best["drop_pp"]):
                hits[scene] = r
    need = _need(len(scenes), frac)
    return {"name": "P1_near_lossless_12x", "assets_with_member": len(hits),
            "assets_total": len(scenes), "need": need, "members": hits,
            "verdict": len(hits) >= need}


def p2(doc, window=0.10, gap_pp=0.5, frac=0.75):
    scenes = [s["scene"] for s in doc["scenes"]]
    per_scene, diffs = {}, []
    for scene in scenes:
        mine = [r for s, r in _rows(doc) if s == scene and family_of(r["variant"]) == "msc"]
        theirs = [r for s, r in _rows(doc) if s == scene and family_of(r["variant"]) in COMPETITORS]
        best = None
        for m in mine:
            rate = float(m["rate"])
            near = [t for t in theirs if abs(float(t["rate"]) - rate) <= window * rate]
            if not near:
                continue
            rival = max(near, key=lambda t: float(t["drop_pp"]))
            diff = float(m["drop_pp"]) - float(rival["drop_pp"])
            if best is None or diff > best["diff_pp"]:
                best = {"diff_pp": diff, "msc": m["variant"], "rival": rival["variant"],
                        "msc_drop_pp": float(m["drop_pp"]),
                        "rival_drop_pp": float(rival["drop_pp"]),
                        "msc_rate": rate, "rival_rate": float(rival["rate"])}
        per_scene[scene] = best
        if best is not None:
            diffs.append(best["diff_pp"])
    ok = [d for d in diffs if d >= gap_pp]
    need = _need(len(scenes), frac)
    return {"name": "P2_beats_families_at_matched_bytes", "per_scene": per_scene,
            "n_compared": len(diffs), "n_passing": len(ok),
            "median_pp": (sorted(diffs)[len(diffs) // 2] if diffs else None),
            "need": need, "verdict": len(ok) >= need}


def p3(doc, lo=18.0, hi=20.0, max_drop=1.0, frac=0.75):
    scenes = [s["scene"] for s in doc["scenes"]]
    covered, hits = [], {}
    for scene in scenes:
        rows = [r for s, r in _rows(doc) if s == scene and family_of(r["variant"]) == "msc"
                and lo <= float(r["rate"]) <= hi]
        if rows:
            covered.append(scene)
            best = max(rows, key=lambda r: float(r["drop_pp"]))
            if float(best["drop_pp"]) >= -max_drop:
                hits[scene] = best["variant"]
    need = _need(len(scenes), frac)
    if len(covered) < need:
        return {"name": "P3_floor_at_18_20x", "status": "under_covered",
                "covered": covered, "need": need, "verdict": None}
    return {"name": "P3_floor_at_18_20x", "status": "measured", "covered": covered,
            "assets_with_member": len(hits), "need": need, "members": hits,
            "verdict": len(hits) >= need}


def evaluate(doc, **kw):
    p1r = p1(doc, **{k: v for k, v in kw.items() if k in
                     ("min_rate", "max_drop", "lo_dpsnr", "hi_dpsnr", "frac")})
    p2r = p2(doc, **{k: v for k, v in kw.items() if k in ("window", "gap_pp", "frac")})
    p3r = p3(doc, **{k: v for k, v in kw.items() if k in ("lo", "hi", "max_drop", "frac")})
    if p1r["verdict"] and p3r.get("verdict"):
        outcome = "msc_holds"
    elif p1r["verdict"]:
        outcome = "frontier_only_msc"
    elif p2r["verdict"]:
        outcome = "msc_beats_families"
    else:
        outcome = "dead_write_N20"
    return {"criteria": {"P1": p1r, "P2": p2r, "P3": p3r}, "outcome": outcome}


def render(res, source=""):
    out = ["# M11: per-primitive mode selection", ""]
    if source:
        out.append(f"source: `{source}`")
        out.append("")
    out.append(f"**outcome** `{res['outcome']}`")
    out.append("")
    out.append("| criterion | verdict | detail |")
    out.append("|---|---|---|")
    for key, c in res["criteria"].items():
        v = c.get("verdict")
        vs = {True: "PASS", False: "FAIL", None: "n/a"}[v]
        if c.get("status") == "under_covered":
            detail = f"grid misses {c['name']} (covered {len(c['covered'])}/{c['need']})"
        elif key == "P1":
            detail = f"{c['assets_with_member']}/{c['assets_total']} assets (need {c['need']})"
        elif key == "P2":
            med = c["median_pp"]
            detail = (f"{c['n_passing']}/{c['n_compared']} assets (need {c['need']}), "
                      f"median {med:+.2f} pp" if med is not None else "no matched pair")
        else:
            detail = f"{c['assets_with_member']}/{len(c['covered'])} covered (need {c['need']})"
        out.append(f"| {c['name']} | {vs} | {detail} |")
    out.append("")
    out.append("## P1 members at >= 12x")
    out.append("")
    out.append("| asset | variant | rate | drop pp | dPSNR |")
    out.append("|---|---|---|---|---|")
    for scene, r in sorted(res["criteria"]["P1"]["members"].items()):
        out.append(f"| {scene} | `{r['variant']}` | {float(r['rate']):.2f}x | "
                   f"{float(r['drop_pp']):+.2f} | {float(r.get('d_psnr') or 0):+.3f} |")
    out.append("")
    out.append("## P2 matched-byte comparison")
    out.append("")
    out.append("| asset | msc | rate | drop | rival | rate | drop | diff |")
    out.append("|---|---|---|---|---|---|---|---|")
    for scene, b in sorted(res["criteria"]["P2"]["per_scene"].items()):
        if b is None:
            out.append(f"| {scene} | - | - | - | - | - | - | no matched pair |")
            continue
        out.append(f"| {scene} | `{b['msc']}` | {b['msc_rate']:.2f}x | {b['msc_drop_pp']:+.2f} | "
                   f"`{b['rival']}` | {b['rival_rate']:.2f}x | {b['rival_drop_pp']:+.2f} | "
                   f"{b['diff_pp']:+.2f} |")
    out.append("")
    return "\n".join(out)


def _synth(gain_pp, n=8, dpsnr_ok=True, base_drop=-0.8, rate=13.0):
    """A world where every asset has an msc member ``gain_pp`` better than rivals."""
    scenes = []
    for i in range(n):
        rows = [
            {"variant": "clean", "rate": 1.0, "drop_pp": 0.0, "d_psnr": 0.0},
            {"variant": "c8_o8_sh3", "rate": rate, "drop_pp": base_drop,
             "d_psnr": 0.0 if dpsnr_ok else -0.5},
            {"variant": "vq12_c8_o8", "rate": rate * 1.02, "drop_pp": base_drop + 0.1,
             "d_psnr": 0.0 if dpsnr_ok else -0.5},
            {"variant": "msc12-4-a1_c8_o8", "rate": rate * 1.04,
             "drop_pp": base_drop + gain_pp, "d_psnr": 0.05 if dpsnr_ok else -1.0},
            {"variant": "msc12-4-a2_c8_o8", "rate": 19.0,
             "drop_pp": -0.5 if dpsnr_ok else -1.2, "d_psnr": 0.1 if dpsnr_ok else -1.0},
        ]
        scenes.append({"scene": f"s{i}", "rows": rows})
    return {"scenes": scenes}


def selftest() -> int:
    fails = []
    wins = evaluate(_synth(2.0))
    good = evaluate(_synth(0.2))

    def check(name, cond, extra=""):
        print(("  [ok] " if cond else "  [FAIL] ") + name + (f" | {extra}" if extra else ""))
        if not cond:
            fails.append(name)

    check("a clear winner passes P1", wins["criteria"]["P1"]["verdict"])
    check("a clear winner passes P2", wins["criteria"]["P2"]["verdict"])
    check("a clear winner is msc_holds", wins["outcome"] == "msc_holds", wins["outcome"])
    check("a 0.2 pp gap fails P2", not good["criteria"]["P2"]["verdict"])
    check("a 0.2 pp gap still passes P1", good["criteria"]["P1"]["verdict"])
    off = evaluate(_synth(2.0, dpsnr_ok=False))
    check("a PSNR gain from the archive's exposure mismatch is not near-lossless",
          not off["criteria"]["P1"]["verdict"])
    miss_doc = _synth(2.0)
    for sc in miss_doc["scenes"]:
        sc["rows"] = [r for r in sc["rows"] if r["rate"] < 18.0]
    miss = evaluate(miss_doc)
    check("P3 reports under_covered rather than fail",
          miss["criteria"]["P3"]["status"] == "under_covered"
          and miss["criteria"]["P3"]["verdict"] is None)
    check("rendering contains the outcome", "outcome" in render(wins))
    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--bytes", default=None, help="m11_bytes.json (measured rates)")
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
