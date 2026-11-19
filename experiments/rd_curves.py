"""Matched-rate curves across every family we have measured.

This is the artefact the paper's RD table needs, and it also repairs the design flaw
M10's L3 had: instead of comparing two families' *best points inside a band* (which
silently lets one family buy a better point with a higher rate), every family is
interpolated to the same rate grid, per asset, before anything is compared.

    python experiments/rd_curves.py --json experiments/artifacts/a4/m10_rd.json \
        --json experiments/artifacts/a4/m9_rd.json --json experiments/artifacts/a4/m5_rd_v2.json \
        --rates 5,7,9,12,16,20,24

Families are recognised from the variant name, exactly as ``m1_analyse`` does it:
``clean`` / ``p*`` (pruning) / ``iso_*`` / ``vq*`` / ``rvq*`` / everything else that is
quantised (``c*``, ``m*``, ``d*``, ``q*``, ``sh*``, ``g*``).
"""
import argparse
import json
import os
import re
import sys

FAMILY_ORDER = ("prune", "scalar", "vq", "rvq")

#: one ladder per family: the knob that the codec actually sweeps.  Variants outside
#: their ladder are still measured, they just are not part of the family curve (they
#: are corners and hybrids, which belong in the tables, not in an RD curve).
LADDERS = {
    "prune": re.compile(r"^p\d+$"),
    "scalar": re.compile(r"^(d\d+_)?c\d+_o8_sh\d+$"),
    "vq": re.compile(r"^vq\d+_c8_o8$"),
    "rvq": re.compile(r"^rvq\d+-\d+_c8_o8$"),
}


def family_of(name: str) -> str:
    if name == "clean":
        return "clean"
    if name.startswith("rvq"):
        return "rvq"
    if name.startswith("vq"):
        return "vq"
    if name.startswith("iso_"):
        return "iso"
    if name.startswith("p") and name[1:2].isdigit():
        return "prune"
    return "scalar"


def interp(points, target):
    """Linear interpolation inside the measured range; ``None`` outside it.

    ``points`` is a list of ``(rate, value)``.  Nothing is ever extrapolated: a rate
    the asset does not cover is reported as missing, not as a guess.
    """
    pts = sorted((float(r), float(v)) for r, v in points if r is not None and v is not None)
    if not pts:
        return None
    if target < pts[0][0] or target > pts[-1][0]:
        return None
    for (r0, v0), (r1, v1) in zip(pts, pts[1:]):
        if r0 <= target <= r1:
            if r1 == r0:
                return v0
            w = (target - r0) / (r1 - r0)
            return v0 + w * (v1 - v0)
    return pts[-1][1]


def envelope(points):
    """Lower envelope: walk rates upwards, keep a point only when it improves the loss.

    ``points`` is ``[(rate, value, name), ...]``; the result is monotone in rate, which
    is what makes interpolation between its knots meaningful (a family's RD curve is
    the best member at each rate, not the average of all of them).
    """
    pts = sorted((float(r), float(v), n) for r, v, n in points
                 if r is not None and v is not None)
    kept, best = [], None
    for r, v, n in pts:
        if best is None or v > best + 1e-12:
            kept.append((r, v, n))
            best = v
    return kept


def collect(docs):
    """``{scene: {family: [(rate, drop), ...]}}`` merged across every dump."""
    scenes = {}
    for doc in docs:
        for sc in doc.get("scenes", []):
            key = sc.get("scene")
            fam_map = scenes.setdefault(key, {})
            for row in sc.get("rows", []):
                name = row.get("variant")
                if not name or name == "clean":
                    continue
                rate, drop = row.get("rate"), row.get("drop_pp")
                if rate is None or drop is None:
                    continue
                fam = family_of(name)
                pat = LADDERS.get(fam)
                if pat is not None and not pat.match(name):
                    continue
                fam_map.setdefault(fam, []).append(
                    (float(rate), float(drop), name))
    return scenes


def curves(scenes, rates):
    """Per-asset, per-family interpolated drops, plus the per-rate means."""
    out = {}
    for scene, fam_map in scenes.items():
        out[scene] = {}
        for fam, rows in fam_map.items():
            out[scene][fam] = {str(r): interp([(a, b) for a, b, _ in rows], r)
                               for r in rates}
    means = {}
    for fam in FAMILY_ORDER:
        means[fam] = {}
        for r in rates:
            vals = [out[s][fam][str(r)] for s in out
                    if fam in out[s] and out[s][fam][str(r)] is not None]
            means[fam][str(r)] = dict(mean=(sum(vals) / len(vals)) if vals else None,
                                      n=len(vals))
    return out, means


def best_coding(means, rates, assets):
    """At each rate: the best non-pruning family that has enough assets."""
    table = {}
    for r in rates:
        cand = [(m["mean"], fam, m["n"]) for fam, m in
                ((f, means[f][str(r)]) for f in FAMILY_ORDER if f != "prune")
                if m["mean"] is not None and m["n"] >= max(1, (2 * assets + 2) // 3)]
        top = max(cand, key=lambda t: t[0]) if cand else None
        table[str(r)] = dict(best=(top[1] if top else None),
                             best_pp=(top[0] if top else None),
                             prune_pp=(means["prune"][str(r)]["mean"]
                                       if means["prune"][str(r)]["mean"] is not None else None),
                             n=(top[2] if top else 0))
        if table[str(r)]["best_pp"] is not None and table[str(r)]["prune_pp"] is not None:
            table[str(r)]["gap_pp"] = table[str(r)]["prune_pp"] - table[str(r)]["best_pp"]
        else:
            table[str(r)]["gap_pp"] = None
    return table


def render(means, table, rates, assets):
    lines = ["# Matched-rate RD curves (coverage loss, pp; negative = worse)", "",
             f"assets: {assets}; every family interpolated per asset to the same rate, "
             "nothing extrapolated.", "",
             "| rate | " + " | ".join(FAMILY_ORDER) + " | best coding | vs prune |",
             "|---|" + "---|" * (len(FAMILY_ORDER) + 2)]
    for r in rates:
        cells = []
        for fam in FAMILY_ORDER:
            m = means[fam][str(r)]
            cells.append("-" if m["mean"] is None else f"{m['mean']:+.2f} (n={m['n']})")
        t = table[str(r)]
        best = "-" if t["best"] is None else f"{t['best']} {t['best_pp']:+.2f}"
        gap = "-" if t["gap_pp"] is None else f"{t['gap_pp']:+.2f}"
        lines.append(f"| {r:g}x | " + " | ".join(cells) + f" | {best} | {gap} |")
    return "\n".join(lines) + "\n"


def _synth():
    def sc(name, rows):
        return dict(scene=name, rows=[dict(variant=v, rate=r, drop_pp=d) for v, r, d in rows])
    return dict(scenes=[
        sc("a", [("p50", 2.0, -5.0), ("p30", 3.3, -13.0), ("p20", 5.0, -20.0),
                 ("c8_o8_sh3", 9.0, -0.7), ("c8_o8_sh2", 17.0, -2.5),
                 ("vq12_c8_o8", 18.7, -1.5), ("rvq8-4_c8_o8", 18.7, -1.1)]),
        sc("b", [("p50", 2.0, -11.0), ("p30", 3.3, -19.0), ("p20", 5.0, -23.0),
                 ("c8_o8_sh3", 9.0, -0.9), ("c8_o8_sh2", 17.0, -2.1),
                 ("vq12_c8_o8", 18.7, -1.9), ("rvq8-4_c8_o8", 18.7, -1.3)]),
        sc("c", [("p50", 2.0, -3.0), ("p30", 3.3, -7.0), ("p20", 5.0, -13.0),
                 ("c8_o8_sh3", 9.0, -0.2), ("c8_o8_sh2", 17.0, -0.6),
                 ("vq12_c8_o8", 18.7, -0.4)]),
    ])


def selftest():
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        print(f"  [{'ok' if cond else 'FAIL'}] {label} {detail}")
        ok = ok and bool(cond)

    scenes = collect([_synth()])
    check("families are recognised", sorted(scenes["a"]) == ["prune", "rvq", "scalar", "vq"],
          str(sorted(scenes["a"])))
    out, means = curves(scenes, [5.0, 9.0, 17.0, 18.7, 20.0])
    check("interpolation stays inside the range", out["a"]["prune"]["20.0"] is None,
          "20x is outside the pruning range")
    check("a measured knot reproduces its own value",
          abs(out["a"]["prune"]["5.0"] - (-20.0)) < 1e-9,
          "prune at 5x is -20.0 pp")
    check("mean only counts covered assets", means["prune"]["9.0"]["n"] == 0
          or means["prune"]["9.0"]["mean"] is None, str(means["prune"]["9.0"]))
    env = envelope([(9.0, -2.0, "coarse"), (12.0, -0.5, "better"),
                    (15.0, -0.9, "dominated")])
    check("the envelope keeps only improving points",
          [n for _, _, n in env] == ["coarse", "better"], str([n for _, _, n in env]))

    tab = best_coding(means, [17.0, 18.7, 20.0], 3)
    check("the best family is the one closest to zero loss",
          tab["17.0"]["best"] == "scalar", str(tab["17.0"]))
    check("at 18.7x a dictionary family wins",
          tab["18.7"]["best"] in ("vq", "rvq"), str(tab["18.7"]))
    check("no coverage means no gap", tab["20.0"]["gap_pp"] is None, str(tab["20.0"]))
    print("=" * 60)
    print("ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="append", default=[],
                    help="rd json (repeatable); later files may add families")
    ap.add_argument("--rates", default="5,7,9,12,16,20,24")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    docs = []
    for p in args.json:
        with open(p, "r", encoding="utf-8") as fh:
            docs.append(json.load(fh))
    if not docs:
        ap.error("at least one --json")
    rates = [float(x) for x in args.rates.split(",") if x.strip()]
    scenes = collect(docs)
    out, means = curves(scenes, rates)
    tab = best_coding(means, rates, len(scenes))
    text = render(means, tab, rates, len(scenes))
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
