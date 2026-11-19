"""M17: what our pipeline can report at HAC's own operating point (pre-registered C5).

M16 lost 4.97 dB to HAC on bicycle at HAC's size, but it had measured exactly one pruning
setting (keep 20 %, 1500 steps).  This script reads the M17 pilot -- three pruning/finetune
configurations on bicycle, each compressed with the unchanged M16 grid -- and answers one
question: **is there any measured point of ours at or below 27.54 MB that reaches 24.50 dB?**

The budget is HAC's measured bicycle size and the threshold is HAC's 25.05 dB minus the 0.55 dB
protocol bias that C1 measured on that same scene.  Both numbers were fixed in METHOD_PLAN.md
before any M17 data existed.

Usage::

    python experiments/m17_report.py --rd m17_rd.json --bytes m17_bytes.json --out m17_report.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cmp_points as CP

#: HAC and PCGS, bicycle, as measured by their own papers (published_3dgs.json).
BUDGETS = {
    "HAC": (27.54, 25.05),
    "PCGS": (19.09, 25.12),
}
#: C1 measured our protocol 0.55 dB below the published one on this scene, so the bar for
#: "matches HAC after that bias" is 25.05 - 0.55.  Pre-registered; not a free parameter.
PROTOCOL_BIAS_DB = 0.55
#: The order the configurations are reported in: base model, then each prune/finetune pair.
CONFIG_ORDER = ["base", "k50_pre", "k50_ft", "k35_pre", "k35_ft",
                "k50l3_pre", "k50l3_ft", "k35l3_pre", "k35l3_ft"]


def config_of(scene: str, base: str) -> str:
    """`bicycle_k50_ft` -> `k50_ft`, `bicycle` -> `base`."""
    if scene == base:
        return "base"
    tail = scene[len(base):].lstrip("_")
    return tail or "base"


def build(rd_json: str, bytes_json: str, base: str) -> list:
    """One record per (config, variant) with absolute size and fidelity."""
    rows = CP.collect(bytes_json, rd_json)
    for r in rows:
        r["config"] = config_of(r["scene"], base)
    return rows


def best_under(rows: list, mb: float):
    cand = [r for r in rows if r.get("mb") is not None and r["mb"] <= mb
            and r.get("psnr") is not None and r["variant"] != "clean"]
    if not cand:
        return None
    return max(cand, key=lambda r: r["psnr"])


def clean_of(rows: list):
    clean = [r for r in rows if r["variant"] == "clean"]
    return max(clean, key=lambda r: r["psnr"]) if clean else None


def evaluate(rows: list, base_psnr: float | None = None) -> dict:
    """Per-configuration summary plus the C5 verdict.

    ``base_psnr`` exists because the base model's byte measurement is not repeated in this round
    (it is the 6.1 M-primitive PLY, whose M16 rows already exist); the caller passes the measured
    24.52 dB so the "vs base" column stays defined.
    """
    per = {}
    #: Every configuration the artifacts actually contain, base first, then the pre-registered
    #: order, then anything else alphabetically.  A round that adds a keep fraction should not have
    #: to edit this file for its rows to appear.
    cfgs = sorted({r["config"] for r in rows},
                  key=lambda c: (c != "base", CONFIG_ORDER.index(c) if c in CONFIG_ORDER else 99, c))
    for cfg in cfgs:
        sub = [r for r in rows if r["config"] == cfg]
        if not sub:
            continue
        c = clean_of(sub)
        per[cfg] = {
            "n": max(r["n"] for r in sub),
            "clean_psnr": (c or {}).get("psnr"),
            "clean_mb": (c or {}).get("mb"),
            "best_hac": best_under(sub, BUDGETS["HAC"][0]),
            "best_pcgs": best_under(sub, BUDGETS["PCGS"][0]),
            "variants": len({r["variant"] for r in sub if r["variant"] != "clean"}),
        }
    #: The finetune's contribution, paired by name: `<tag>_ft` against `<tag>_pre`.
    for cfg in list(per):
        if not cfg.endswith("_ft"):
            continue
        pre, ft = per.get(cfg[:-3] + "_pre"), per[cfg]
        if pre and ft and pre["clean_psnr"] and ft["clean_psnr"]:
            ft["ft_gain_db"] = ft["clean_psnr"] - pre["clean_psnr"]
    base = per.get("base") or {}
    if not base and base_psnr is not None:
        per["base"] = {"n": 0, "clean_psnr": base_psnr, "clean_mb": None,
                       "best_hac": None, "best_pcgs": None, "variants": 0}
        base = per["base"]
    thr = BUDGETS["HAC"][1] - PROTOCOL_BIAS_DB
    best = best_under([r for r in rows if r["config"] != "base"], BUDGETS["HAC"][0])
    verdict = "no_data"
    if best is not None:
        verdict = "competitive_at_hac_size" if best["psnr"] >= thr else "representation_bound_confirmed"
    return {
        "per_config": per,
        "base_psnr": base.get("clean_psnr"),
        "threshold_db": thr,
        "budget_mb": BUDGETS["HAC"][0],
        "best_under_budget": best,
        "verdict": verdict,
    }


def render(res: dict, title: str = "M17 pilot: our frontier at HAC's operating point (bicycle)") -> str:
    base = res.get("base_psnr")
    L = []
    L.append(f"# {title}")
    L.append("")
    L.append(f"Base model: {base:.2f} dB" if base else "Base model: missing")
    L.append("")
    hb, hp = BUDGETS["HAC"]
    pb, pp = BUDGETS["PCGS"]
    L.append(f"| configuration | primitives | clean dB | vs base | ft gain | "
             f"best <= {hb:.2f} MB | best <= {pb:.2f} MB |")
    L.append("|---|---|---|---|---|---|---|")
    for cfg in res["per_config"]:
        d = res["per_config"].get(cfg)
        if not d:
            continue
        db = f"{d['clean_psnr'] - base:+.2f}" if (d["clean_psnr"] and base) else "--"
        fg = f"{d['ft_gain_db']:+.2f}" if d.get("ft_gain_db") is not None else "--"
        def cell(b):
            if not b:
                return "*none*"
            return f"`{b['variant']}` {b['mb']:.2f} MB / {b['psnr']:.2f} dB"
        L.append(f"| `{cfg}` | {d['n']:,} | "
                 f"{d['clean_psnr']:.2f} | {db} | {fg} | {cell(d['best_hac'])} | {cell(d['best_pcgs'])} |")
    L.append("")
    thr = res["threshold_db"]
    b = res["best_under_budget"]
    L.append(f"## C5: best row at or below {res['budget_mb']:.2f} MB must reach {thr:.2f} dB")
    L.append("")
    if b:
        L.append(f"Best: `{b['variant']}` on `{b['scene']}` -- {b['mb']:.2f} MB / {b['psnr']:.2f} dB "
                 f"({b['psnr'] - thr:+.2f} dB against the bar, {b['psnr'] - hp:+.2f} dB against HAC's own row).")
    else:
        L.append("No compressed row of ours fits inside the budget at all.")
    L.append("")
    L.append(f"**Verdict: `{res['verdict']}`**")
    L.append("")
    return "\n".join(L)


def selftest() -> None:
    def row(scene, variant, mb, psnr, n=1000):
        return {"scene": scene, "variant": variant, "config": config_of(scene, "bicycle"),
                "mb": mb, "psnr": psnr, "n": n, "rate": 236 / 8.0,
                "bytes_per_prim": 8.0, "family": "x", "ssim": None, "lpips": None,
                "drop_pp": 0.0}

    rows = [
        row("bicycle", "clean", 1447.0, 24.52),
        row("bicycle", "vq12_c8_o8", 72.17, 23.86),
        row("bicycle_k50_ft", "clean", 289.0, 23.10),
        row("bicycle_k50_ft", "vq12_c8_o8", 24.00, 21.40),
        row("bicycle_k50_ft", "c10_o8_sh3", 30.80, 23.05),
    ]
    res = evaluate(rows)
    assert res["verdict"] == "representation_bound_confirmed", res["verdict"]
    # c10 at 30.8 MB is outside the budget, so the 24 MB VQ row is the one that answers C5.
    assert abs(res["best_under_budget"]["psnr"] - 21.40) < 1e-9
    assert abs(res["threshold_db"] - 24.50) < 1e-9
    assert res["per_config"]["base"]["best_hac"] is None          # 72 MB is over the budget
    assert "ft_gain_db" not in res["per_config"]["k50_ft"]        # no pre row -> no gain recorded

    rows2 = rows + [row("bicycle_k50_ft", "c8_o8_sh3", 27.00, 24.60)]
    res2 = evaluate(rows2)
    assert res2["verdict"] == "competitive_at_hac_size", res2["verdict"]
    assert abs(res2["best_under_budget"]["mb"] - 27.00) < 1e-9

    # ft gain is measured against the un-finetuned model at the same keep fraction.
    rows3 = rows + [row("bicycle_k50_pre", "clean", 289.0, 20.10)]
    assert abs(evaluate(rows3)["per_config"]["k50_ft"]["ft_gain_db"] - 3.0) < 1e-9

    assert config_of("bicycle_k35_pre", "bicycle") == "k35_pre"
    assert config_of("bicycle", "bicycle") == "base"
    txt = render(res)
    assert "representation_bound_confirmed" in txt and "C5" in txt
    print("m17_report selftest: ALL PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rd")
    ap.add_argument("--bytes")
    ap.add_argument("--out")
    ap.add_argument("--base", default="bicycle")
    ap.add_argument("--base-psnr", type=float, default=None,
                    help="clean dB of the unpruned model, when its rows are not in this round")
    ap.add_argument("--title", default="M17 pilot: our frontier at HAC's operating point (bicycle)")
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.rd and a.bytes):
        ap.error("--rd and --bytes are required")
    rows = build(a.rd, a.bytes, a.base)
    res = evaluate(rows, base_psnr=a.base_psnr)
    txt = render(res, a.title)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
        print("WROTE", a.out)
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), indent=1)
        print("WROTE", a.json)
    if not a.out:
        print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
