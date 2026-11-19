"""M16: place our measured curve on the published axes and judge the two protocol criteria.

Why this exists.  Every M-series number is *relative*: coverage loss against our own clean
render, at our own checkpoints, at ``--factor 4``.  Published compressed-3DGS numbers
(HAC, PCGS, ContextGS) are absolute: PSNR on the standard 30k checkpoints at images_4,
with the model size in MB.  Two things have to be true before any external claim:

* **C1 protocol** -- our ``clean`` render must reproduce the published 3DGS PSNR.  If it
  does not, the difference is our checkpoint or our resize, not compression, and no
  comparison is admissible.
* **C2 equal-size** -- at each published operating point (its own MB, per scene), our best
  variant that fits in that many bytes must match its PSNR.  This is the only comparison
  the papers' own tables support, because they publish one rate point per method.

Both criteria are pre-registered in ``experiments/METHOD_PLAN.md`` before the run, with the
reference numbers in ``experiments/published_3dgs.json``.

Usage::

    python experiments/m16_compare.py --rd m16_rd.json --bytes m16_bytes.json \
        --published experiments/published_3dgs.json --out m16_compare.md
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cmp_points as CP  # noqa: E402

#: C1: how close the clean render has to be to the published 3DGS row.  The scene counts are
#: fractions of the 9-scene protocol (7/9 and 6/9) so a selftest on two synthetic scenes does
#: not need a different rule from the real run.
C1_TOL_DB = 0.35
C1_FRAC = 7 / 9
C1_MEAN_TOL = 0.25

#: C2: our variant must fit the published size and not lose PSNR.
C2_SIZE_SLACK = 1.05
C2_FRAC = 6 / 9
C2_PSNR_TOL = 0.0


def _need(n: int, frac: float) -> int:
    return max(1, int(-(-n * frac // 1)))  # ceil without importing math


def _fmt(v, nd=2):
    return "-" if v is None else f"{v:.{nd}f}"


#: Suffixes our archives carry that the published tables do not.  `bicycle_mirror` is the same
#: scene as `bicycle`: the suffix only records where the checkpoint came from, and leaving it on
#: makes every row fall through to ``no candidate``.  A pruned-and-finetuned archive
#: (`bicycle_mirror_ft`, `stump_mirror_k0.2`) is the same scene too, and belongs on the C2 curve,
#: but C1 must compare the *unpruned* model, so `clean_row` prefers the shortest source name.
SCENE_SUFFIXES = ("_mirror", "_sweep", "_abs", "_selftrain", "_official", "_ft")


def canon(scene: str) -> str:
    """Strip every archive suffix, not just one: ``bicycle_mirror_ft`` -> ``bicycle``."""
    s = scene
    changed = True
    while changed:
        changed = False
        for suf in SCENE_SUFFIXES:
            if s.endswith(suf) and len(s) > len(suf):
                s = s[: -len(suf)]
                changed = True
                break
        if not changed and "_k" in s:
            head, _, tail = s.rpartition("_k")
            try:
                float(tail)
            except ValueError:
                pass
            else:
                s = head
                changed = True
    return s


def canon_rows(rows: list) -> list:
    out = []
    for r in rows:
        q = dict(r)
        q["src"] = r["scene"]
        q["scene"] = canon(r["scene"])
        out.append(q)
    return out


def clean_row(rows: list) -> dict:
    """One clean row per scene: the model that was never pruned."""
    out = {}
    for r in rows:
        if r["variant"] != "clean":
            continue
        cur = out.get(r["scene"])
        if cur is None or len(r.get("src", r["scene"])) < len(cur.get("src", cur["scene"])):
            out[r["scene"]] = r
    return out


def best_within_size(rows: list, scene: str, budget_mb: float):
    cand = [r for r in rows if r["scene"] == scene
            and r["mb"] <= budget_mb and r.get("psnr") is not None]
    if not cand:
        return None
    return max(cand, key=lambda r: r["psnr"])


def c1(rows: list, pub: dict) -> dict:
    ref = pub["methods"]["3dgs"]
    clean = clean_row(rows)
    out = []
    for scene, r in sorted(ref.items()):
        ours = clean.get(scene)
        d = None if ours is None or ours.get("psnr") is None else ours["psnr"] - r["psnr"]
        out.append({"scene": scene, "ours": None if not ours else ours.get("psnr"),
                    "ref": r["psnr"], "delta": d,
                    "ssim_delta": None if not ours or ours.get("ssim") is None else ours["ssim"] - r["ssim"],
                    "lpips_delta": None if not ours or ours.get("lpips") is None else ours["lpips"] - r["lpips"]})
    ds = [o["delta"] for o in out if o["delta"] is not None]
    ok = sum(1 for d in ds if abs(d) <= C1_TOL_DB)
    mean_abs = st.fmean([abs(d) for d in ds]) if ds else None
    verdict = None
    if len(ds) == len(ref):
        verdict = bool(ok >= _need(len(ds), C1_FRAC)
                       and mean_abs is not None and mean_abs <= C1_MEAN_TOL)
    return {"rows": out, "n_ok": ok, "n": len(ds), "mean_abs": mean_abs, "verdict": verdict}


def c2(rows: list, pub: dict, method: str) -> dict:
    ref = pub["methods"][method]
    out = []
    for scene, r in sorted(ref.items()):
        budget = r["mb"] * C2_SIZE_SLACK
        pick = best_within_size(rows, scene, budget)
        if pick is None:
            out.append({"scene": scene, "ref_mb": r["mb"], "ref_psnr": r["psnr"],
                        "variant": None, "mb": None, "psnr": None,
                        "d_psnr": None, "d_ssim": None, "d_lpips": None, "ok": False})
            continue
        out.append({
            "scene": scene, "ref_mb": r["mb"], "ref_psnr": r["psnr"],
            "variant": pick["variant"], "mb": pick["mb"], "psnr": pick["psnr"],
            "d_psnr": pick["psnr"] - r["psnr"],
            "d_ssim": None if pick.get("ssim") is None else pick["ssim"] - r["ssim"],
            "d_lpips": None if pick.get("lpips") is None else pick["lpips"] - r["lpips"],
            "ok": bool(pick["psnr"] - r["psnr"] >= C2_PSNR_TOL),
        })
    ds = [o["d_psnr"] for o in out if o["d_psnr"] is not None]
    ok = sum(1 for o in out if o["ok"])
    verdict = None
    if len(ds) == len(ref):
        verdict = bool(ok >= _need(len(ds), C2_FRAC) and st.fmean(ds) >= C2_PSNR_TOL)
    return {"rows": out, "n_ok": ok, "n": len(ds),
            "mean": st.fmean(ds) if ds else None, "verdict": verdict}


def smallest(rows: list) -> list:
    """The cheapest variant we have per scene -- how close our range gets to 5-25 MB."""
    out = []
    for scene in sorted({r["scene"] for r in rows}):
        cand = [r for r in rows if r["scene"] == scene and r.get("mb") is not None]
        if not cand:
            continue
        pick = min(cand, key=lambda r: r["mb"])
        out.append({"scene": scene, "variant": pick["variant"], "mb": pick["mb"],
                    "psnr": pick.get("psnr")})
    return out


def render(rows: list, pub: dict, res: dict) -> str:
    L = []
    L.append("# M16 -- our curve on the published axes\n")
    L.append(f"reference: `{pub['_sources']['3dgs']}`; protocol {pub['protocol']}\n")

    a = res["c1"]
    v = {True: "**PASS**", False: "**FAIL**", None: "n/a"}[a["verdict"]]
    L.append("## C1 protocol (does our clean render reproduce the published 3DGS?)\n")
    L.append(f"{v} -- {a['n_ok']}/{a['n']} scenes within {C1_TOL_DB} dB "
             f"(need {_need(a['n'], C1_FRAC)}), mean |delta| {_fmt(a['mean_abs'])} dB "
             f"(need <= {C1_MEAN_TOL})\n")
    L.append("| scene | ours | published 3DGS | delta dB | dSSIM | dLPIPS |")
    L.append("|---|---|---|---|---|---|")
    for o in a["rows"]:
        L.append(f"| {o['scene']} | {_fmt(o['ours'])} | {_fmt(o['ref'])} | "
                 f"{'+' if (o['delta'] or 0) >= 0 else ''}{_fmt(o['delta'])} | "
                 f"{_fmt(o['ssim_delta'], 3)} | {_fmt(o['lpips_delta'], 4)} |")

    for m in ("hac", "pcgs"):
        b = res["c2"][m]
        v = {True: "**PASS**", False: "**FAIL**", None: "n/a"}[b["verdict"]]
        L.append(f"\n## C2 equal size vs `{m}`\n")
        L.append(f"{v} -- {b['n_ok']}/{b['n']} scenes at or above its PSNR within its own size "
                 f"(need {_need(b['n'], C2_FRAC)}), mean dPSNR "
                 f"{'+' if (b['mean'] or 0) >= 0 else ''}{_fmt(b['mean'])} dB\n")
        L.append("| scene | its MB | its PSNR | our variant | our MB | our PSNR | dPSNR | ok |")
        L.append("|---|---|---|---|---|---|---|---|")
        for o in b["rows"]:
            if o["variant"] is None:
                L.append(f"| {o['scene']} | {o['ref_mb']:.1f} | {o['ref_psnr']:.2f} | "
                         f"*no candidate* | - | - | - | no |")
                continue
            L.append(f"| {o['scene']} | {o['ref_mb']:.1f} | {o['ref_psnr']:.2f} | "
                     f"`{o['variant']}` | {o['mb']:.1f} | {o['psnr']:.2f} | "
                     f"{'+' if o['d_psnr'] >= 0 else ''}{o['d_psnr']:.2f} | "
                     f"{'yes' if o['ok'] else 'no'} |")

    L.append("\n## how far down our own range goes\n")
    L.append("| scene | cheapest variant | MB | PSNR |")
    L.append("|---|---|---|---|")
    for o in res["smallest"]:
        L.append(f"| {o['scene']} | `{o['variant']}` | {o['mb']:.2f} | {_fmt(o['psnr'])} |")
    return "\n".join(L) + "\n"


def evaluate(rows: list, pub: dict) -> dict:
    rows = canon_rows(rows)
    return {"c1": c1(rows, pub),
            "c2": {m: c2(rows, pub, m) for m in ("hac", "pcgs")},
            "smallest": smallest(rows)}


def selftest() -> int:
    pub = {"protocol": {"x": 1}, "_sources": {"3dgs": "synthetic"},
           "methods": {
               "3dgs": {"a": {"mb": 1000.0, "psnr": 25.0, "ssim": 0.75, "lpips": 0.25},
                        "b": {"mb": 800.0, "psnr": 21.0, "ssim": 0.60, "lpips": 0.35}},
               "hac": {"a": {"mb": 30.0, "psnr": 24.9, "ssim": 0.74, "lpips": 0.26},
                       "b": {"mb": 20.0, "psnr": 21.1, "ssim": 0.59, "lpips": 0.36}},
               "pcgs": {"a": {"mb": 20.0, "psnr": 25.0, "ssim": 0.74, "lpips": 0.27},
                        "b": {"mb": 15.0, "psnr": 21.2, "ssim": 0.58, "lpips": 0.38}},
               }}
    # a clean that matches protocol, and a curve that meets hac on 'a' but not 'b'
    rows = [
        {"scene": "a", "variant": "clean", "mb": 1000.0, "psnr": 25.05, "ssim": 0.75, "lpips": 0.25},
        {"scene": "b", "variant": "clean", "mb": 800.0, "psnr": 21.05, "ssim": 0.60, "lpips": 0.35},
        {"scene": "a", "variant": "x", "mb": 28.0, "psnr": 25.10, "ssim": 0.74, "lpips": 0.25},
        {"scene": "a", "variant": "y", "mb": 60.0, "psnr": 25.50, "ssim": 0.75, "lpips": 0.24},
        {"scene": "b", "variant": "x", "mb": 18.0, "psnr": 20.90, "ssim": 0.59, "lpips": 0.36},
    ]
    res = evaluate(rows, pub)
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'ok' if cond else 'FAIL'}] {name}{'' if not detail else ': ' + detail}")

    chk("C1 passes on a clean that matches", res["c1"]["verdict"] is True,
        f"{res['c1']['n_ok']}/{res['c1']['n']}")
    chk("C2 hac counts 'a' only", res["c2"]["hac"]["n_ok"] == 1)
    chk("C2 hac fails the 6-of-9 gate on 2 scenes", res["c2"]["hac"]["verdict"] is False)
    chk("C2 pcgs has no candidate at its 20 MB point", res["c2"]["pcgs"]["n_ok"] == 0)
    chk("cheapest pick per scene", [o["variant"] for o in res["smallest"]] == ["x", "x"])
    # a clean 0.5 dB low must fail the protocol gate
    bad = [dict(r) for r in rows]
    for r in bad:
        if r["variant"] == "clean":
            r["psnr"] -= 0.5
    res2 = evaluate(bad, pub)
    chk("C1 fails when clean is 0.5 dB off", res2["c1"]["verdict"] is False)
    # no candidate at all -> n/a, not a silent pass
    thin = [r for r in rows if r["variant"] == "clean"]
    res3 = evaluate(thin, pub)
    chk("a scene with no candidate is 'no', not a pass",
        res3["c2"]["hac"]["n_ok"] == 0 and res3["c2"]["hac"]["verdict"] is None)
    # the md renders
    md = render(rows, pub, res)
    chk("render has all three sections",
        "C1 protocol" in md and "C2 equal size vs `hac`" in md and "our own range" in md)
    chk("render shows the failing scene", "| b |" in md)
    print("=" * 60)
    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rd", default="")
    ap.add_argument("--bytes", default="")
    ap.add_argument("--published", default=os.path.join(HERE, "published_3dgs.json"))
    ap.add_argument("--out", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not (args.rd and args.bytes):
        ap.error("--rd and --bytes are required (or --selftest)")
    rows = CP.collect(args.bytes, args.rd)
    pub = json.load(open(args.published, encoding="utf-8"))
    res = evaluate(rows, pub)
    md = render(rows, pub, res)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(md)
        print(f"WROTE {args.out}")
    else:
        print(md)
    if args.json:
        json.dump(res, open(args.json, "w", encoding="utf-8"), indent=1)
        print(f"WROTE {args.json}")
    print("C1", res["c1"]["verdict"], f"{res['c1']['n_ok']}/{res['c1']['n']}")
    for m, b in res["c2"].items():
        print(f"C2 {m}", b["verdict"], f"{b['n_ok']}/{b['n']}", "mean", b["mean"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
