"""Score M12 (product quantisation of the SH block) against its registered criteria.

Q1  bytes for bytes: within +/-10% of a measured rate, the best ``pq`` member must lose
    at least 0.5 pp less coverage than the best single-codebook member (``vq*``), on 6/8
    assets.  This is the whole question -- PQ is only interesting if it dominates VQ at
    the same budget.
Q2  the absolute shelf: at >= 16x a ``pq`` member must lose at most 1.0 pp without
    gaining PSNR from the archive's exposure mismatch (``0 <= d_psnr <= 0.3``), on 6/8.

Outcomes: ``pq_holds`` (Q1 and Q2), ``pq_beats_vq_only`` (Q1 only), ``dead_write_N21``.
"""
import argparse
import json
import math
import sys

import common as C

PQ_TAG = "pq"
VQ_TAG = "vq"


def family_of(name: str) -> str:
    for tok in name.split("_"):
        if tok.startswith("pq"):
            return "pq"
        if tok.startswith("rvq"):
            return "rvq"
        if tok.startswith("vq"):
            return "vq"
        if tok.startswith("msc"):
            return "msc"
        if tok == "clean":
            return "clean"
        if tok.startswith("p") and tok[1:].isdigit():
            return "prune"
    return "scalar"


def _need(n: int, frac: float = 0.75) -> int:
    return max(1, int(math.ceil(frac * n)))


def _rows(doc):
    for sc in doc["scenes"]:
        for r in sc["rows"]:
            yield sc["scene"], r


def q1(doc, window=0.10, gap_pp=0.5, frac=0.75):
    scenes = [s["scene"] for s in doc["scenes"]]
    per_scene, diffs = {}, []
    for scene in scenes:
        mine = [r for s, r in _rows(doc) if s == scene and family_of(r["variant"]) == "pq"]
        theirs = [r for s, r in _rows(doc) if s == scene and family_of(r["variant"]) == "vq"]
        best = None
        for m in mine:
            rate = float(m["rate"])
            near = [t for t in theirs if abs(float(t["rate"]) - rate) <= window * rate]
            if not near:
                continue
            rival = max(near, key=lambda t: float(t["drop_pp"]))
            diff = float(m["drop_pp"]) - float(rival["drop_pp"])
            if best is None or diff > best["diff_pp"]:
                best = {"diff_pp": diff, "pq": m["variant"], "rival": rival["variant"],
                        "pq_drop_pp": float(m["drop_pp"]),
                        "rival_drop_pp": float(rival["drop_pp"]),
                        "pq_rate": rate, "rival_rate": float(rival["rate"])}
        per_scene[scene] = best
        if best is not None:
            diffs.append(best["diff_pp"])
    ok = [d for d in diffs if d >= gap_pp]
    need = _need(len(scenes), frac)
    return {"name": "Q1_pq_beats_vq_at_matched_bytes", "per_scene": per_scene,
            "n_compared": len(diffs), "n_passing": len(ok),
            "median_pp": (sorted(diffs)[len(diffs) // 2] if diffs else None),
            "min_pp": (min(diffs) if diffs else None),
            "max_pp": (max(diffs) if diffs else None),
            "need": need, "verdict": len(ok) >= need}


def q2(doc, min_rate=16.0, max_drop=1.0, lo_dpsnr=0.0, hi_dpsnr=0.3, frac=0.75):
    scenes = [s["scene"] for s in doc["scenes"]]
    covered, hits = [], {}
    for scene in scenes:
        rows = [r for s, r in _rows(doc) if s == scene and family_of(r["variant"]) == "pq"
                and float(r["rate"]) >= min_rate]
        if rows:
            covered.append(scene)
        good = [r for r in rows if float(r["drop_pp"]) >= -max_drop
                and lo_dpsnr <= float(r.get("d_psnr") or 0.0) <= hi_dpsnr]
        if good:
            hits[scene] = max(good, key=lambda r: float(r["drop_pp"]))
    need = _need(len(scenes), frac)
    if len(covered) < need:
        return {"name": "Q2_shelf_at_16x", "status": "under_covered",
                "covered": covered, "need": need, "verdict": None}
    return {"name": "Q2_shelf_at_16x", "status": "measured", "covered": covered,
            "assets_with_member": len(hits), "need": need, "members": hits,
            "verdict": len(hits) >= need}


def evaluate(doc, **kw):
    q1r = q1(doc, **{k: v for k, v in kw.items() if k in ("window", "gap_pp", "frac")})
    q2r = q2(doc, **{k: v for k, v in kw.items() if k in
                     ("min_rate", "max_drop", "lo_dpsnr", "hi_dpsnr", "frac")})
    if q1r["verdict"] and q2r.get("verdict"):
        outcome = "pq_holds"
    elif q1r["verdict"]:
        outcome = "pq_beats_vq_only"
    else:
        outcome = "dead_write_N21"
    return {"criteria": {"Q1": q1r, "Q2": q2r}, "outcome": outcome}


def render(res, source=""):
    out = ["# M12: product quantisation of the SH block", ""]
    if source:
        out += [f"source: `{source}`", ""]
    out += [f"**outcome** `{res['outcome']}`", "",
            "| criterion | verdict | detail |", "|---|---|---|"]
    for key, c in res["criteria"].items():
        v = c.get("verdict")
        vs = {True: "PASS", False: "FAIL", None: "n/a"}[v]
        if c.get("status") == "under_covered":
            detail = f"grid misses it (covered {len(c['covered'])}/{c['need']})"
        elif key == "Q1":
            detail = (f"{c['n_passing']}/{c['n_compared']} assets (need {c['need']}), "
                      f"median {c['median_pp']:+.2f} pp") if c["median_pp"] is not None \
                else "no matched pair"
        else:
            detail = f"{c['assets_with_member']}/{len(c['covered'])} covered (need {c['need']})"
        out.append(f"| {c['name']} | {vs} | {detail} |")
    out += ["", "## Q1 matched-byte comparison", "",
            "| asset | pq | rate | drop | vq | rate | drop | diff |",
            "|---|---|---|---|---|---|---|---|"]
    for scene, b in sorted(res["criteria"]["Q1"]["per_scene"].items()):
        if b is None:
            out.append(f"| {scene} | - | - | - | - | - | - | no matched pair |")
            continue
        out.append(f"| {scene} | `{b['pq']}` | {b['pq_rate']:.2f}x | {b['pq_drop_pp']:+.2f} | "
                   f"`{b['rival']}` | {b['rival_rate']:.2f}x | {b['rival_drop_pp']:+.2f} | "
                   f"{b['diff_pp']:+.2f} |")
    out += ["", "## Q2 members at >= 16x", "",
            "| asset | variant | rate | drop pp | dPSNR |", "|---|---|---|---|---|"]
    for scene, r in sorted(res["criteria"]["Q2"].get("members", {}).items()):
        out.append(f"| {scene} | `{r['variant']}` | {float(r['rate']):.2f}x | "
                   f"{float(r['drop_pp']):+.2f} | {float(r.get('d_psnr') or 0):+.3f} |")
    out.append("")
    return "\n".join(out)


def _synth(gain_pp, n=8, dpsnr_ok=True, vq_drop=-1.9, pq_drop=None, rate=17.0,
           pq_rate=17.2):
    scenes = []
    for i in range(n):
        rows = [
            {"variant": "clean", "rate": 1.0, "drop_pp": 0.0, "d_psnr": 0.0},
            {"variant": "vq12_c8_o8", "rate": rate, "drop_pp": vq_drop, "d_psnr": 0.0},
            {"variant": "pq3-4_c8_o8", "rate": pq_rate,
             "drop_pp": vq_drop + gain_pp if pq_drop is None else pq_drop,
             "d_psnr": 0.05 if dpsnr_ok else -1.0},
        ]
        scenes.append({"scene": f"s{i}", "rows": rows})
    return {"scenes": scenes}


def selftest() -> int:
    fails = []

    def check(name, cond, extra=""):
        print(("  [ok] " if cond else "  [FAIL] ") + name + (f" | {extra}" if extra else ""))
        if not cond:
            fails.append(name)

    win = evaluate(_synth(1.2))
    tie = evaluate(_synth(0.2))
    shelf = evaluate(_synth(0.1, pq_drop=-0.4, vq_drop=-0.5))
    check("a clear win passes Q1", win["criteria"]["Q1"]["verdict"])
    check("a clear win holds Q2", win["criteria"]["Q2"]["verdict"])
    check("a clear win is pq_holds", win["outcome"] == "pq_holds", win["outcome"])
    check("a 0.2 pp gain fails Q1", not tie["criteria"]["Q1"]["verdict"],
          f"{tie['criteria']['Q1']['median_pp']:+.2f}")
    check("Q1 failure alone is dead_write_N21", tie["outcome"] == "dead_write_N21",
          tie["outcome"])
    check("Q2 can pass while Q1 fails (a shelf without a bytes-for-bytes win)",
          (not shelf["criteria"]["Q1"]["verdict"]) and shelf["criteria"]["Q2"]["verdict"],
          f"Q1={shelf['criteria']['Q1']['verdict']} Q2={shelf['criteria']['Q2']['verdict']}")
    low = evaluate(_synth(1.2, dpsnr_ok=False))
    check("a PSNR gain from the archive is not a shelf member",
          not low["criteria"]["Q2"]["verdict"])
    miss_doc = _synth(1.2)
    for sc in miss_doc["scenes"]:
        sc["rows"] = [r for r in sc["rows"] if float(r["rate"]) < 16.0]
    check("Q2 reports under_covered when the family starts below 16x",
          evaluate(miss_doc)["criteria"]["Q2"]["status"] == "under_covered")
    check("rendering names the outcome", "outcome" in render(win))
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
