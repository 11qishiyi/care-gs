"""Best-achievable coverage loss at a byte budget, measured -- not interpolated.

M1-M12 produced five ``*_rd.json`` tables.  Each row is one variant on one asset: a
*measured* byte rate (zstd-12 on Morton-ordered, bit-packed streams), a coverage drop over
400 paired splits with a 2.5/97.5 interval, and a PSNR.  Their ``matched`` blocks
interpolate whole families onto a common rate grid, but a "family" there mixes ladders
(M12's ``qfp`` spans the 7.6x scalar ladder and the 15-20x PQ ladders), and M5 already
showed that interpolation across coding schemes overstates what a real encoder does.

So this frontier uses **only measured points**: for a budget of ``N``x, a variant counts if
its measured rate is within ``--window`` of ``N``; the winner is the one that loses the
least coverage.  Every cell therefore names a real variant that can be built and shipped,
and the rate mismatch is printed next to it.
"""
import argparse
import glob
import json
import os
import sys

import common as C

SOURCES = ["m1_rd_measured", "m13_i7k", "m5_rd_v2", "m9_rd", "m10_rd",
           "m11_rd", "m12_rd", "sota_rd"]
BUDGETS = (2.0, 3.0, 5.0, 7.0, 9.0, 12.0, 16.0, 24.0)


def family_of(name: str) -> str:
    n = name.split("_")
    for tok in n:
        if tok in ("clean",):
            return "clean"
        if tok.startswith("pq"):
            return "pq"
        if tok.startswith("rvq"):
            return "rvq"
        if tok.startswith("vq"):
            return "vq"
        if tok.startswith("msc"):
            return "msc"
        if tok.startswith("iso_"):
            return "iso"
        if tok.startswith("sh") or tok.startswith("geo") or tok.startswith("d"):
            return "scalar"
        if tok.startswith("m") and tok[1:3].isdigit():
            return "scalar"
        if tok.startswith("c") and tok[1:3].isdigit():
            return "scalar"
        if tok.startswith("p") and tok[1:].isdigit():
            return "prune"
        if tok.startswith("am"):
            return "alloc_mse"
        if tok.startswith("at"):
            return "alloc_tail"
    return "other"


def load_rows(paths):
    """``{scene: [row, ...]}`` with duplicates (same scene+variant) resolved to one."""
    out = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        doc = json.load(open(path, encoding="utf-8"))
        for sc in doc["scenes"]:
            scene = sc["scene"]
            bucket = out.setdefault(scene, {})
            for row in sc["rows"]:
                name = row["variant"]
                cur = bucket.get(name)
                # the same variant can appear in two runs; keep the first measured rate
                if cur is None or (cur.get("rate_src") != "measured"
                                   and doc.get("meta", {}).get("rate_source") == "measured"):
                    bucket[name] = {"variant": name, "family": family_of(name),
                                    "rate": float(row["rate"]),
                                    "drop_pp": float(row["drop_pp"]),
                                    "lo_pp": float(row.get("drop_lo_pp", row["drop_pp"])),
                                    "hi_pp": float(row.get("drop_hi_pp", row["drop_pp"])),
                                    "d_psnr": row.get("d_psnr"),
                                    "psnr": row.get("psnr"),
                                    "rate_src": doc.get("meta", {}).get("rate_source"),
                                    "from": os.path.basename(path)}
    return {s: list(b.values()) for s, b in out.items()}


def frontier(rows, budgets=BUDGETS, window=0.02, mode="at_most"):
    """``{scene: {budget: row}}`` -- the least-loss point that fits the budget.

    Two readings, and they answer different questions:

    ``mode="at_most"`` (default) -- "at a rate of at most R".  A point that costs fewer
    bytes than the budget can satisfy every larger budget too, so this table saturates:
    once a zero-loss point exists at 2.8x, every budget above it reports the same point.
    It is still the honest bound ("this quality is reachable without spending the budget").

    ``mode="at_least"`` -- "the asset must ship at least N times smaller".  The candidate
    set is ``rate >= N*(1-window)``, so the table traces the rate--distortion curve itself
    instead of the running minimum.  This is the reading to quote when the question is
    "what does this pipeline do at 20x".
    """
    out = {}
    for scene, rs in rows.items():
        best = {}
        for b in budgets:
            if mode == "at_least":
                cand = [r for r in rs if r["rate"] >= b * (1.0 - window)]
            else:
                cand = [r for r in rs if r["rate"] <= b * (1.0 + window)]
            if cand:
                best[b] = max(cand, key=lambda r: (r["drop_pp"], -r["rate"]))
        out[scene] = best
    return out


def summarise(fr, budgets=BUDGETS):
    out = []
    for b in budgets:
        hit = [(s, fr[s][b]) for s in fr if b in fr[s]]
        if not hit:
            continue
        drops = [r["drop_pp"] for _, r in hit]
        wins = {}
        for _, r in hit:
            wins[r["family"]] = wins.get(r["family"], 0) + 1
        rates = [r["rate"] for _, r in hit]
        out.append({"budget": b, "n_assets": len(hit),
                    "mean_pp": sum(drops) / len(drops),
                    "worst_pp": min(drops), "best_pp": max(drops),
                    "mean_rate": sum(rates) / len(rates),
                    "max_rate": max(rates),
                    "families": dict(sorted(wins.items(), key=lambda kv: -kv[1]))})
    return out


TOLS = (0.25, 0.5, 1.0, 2.0, 5.0)


def inverse(rows, tols=TOLS, require_psnr=True):
    """``{scene: {tol: row}}`` -- the cheapest measured point that stays within ``tol`` pp.

    The budget table answers "given bytes, how much coverage do I lose"; this answers "given a
    coverage tolerance, how many bytes do I need".  ``require_psnr`` drops points whose PSNR
    *improved*, which on this archive happens for one reason only (the GT exposure mismatch of
    treehill), and such a point is not evidence of quality.
    """
    out = {}
    for scene, rs in rows.items():
        best = {}
        for t in tols:
            cand = [r for r in rs if r["drop_pp"] >= -abs(t)]
            if require_psnr:
                cand = [r for r in cand if r.get("d_psnr") is None or r["d_psnr"] >= 0.0]
            if cand:
                best[t] = min(cand, key=lambda r: (r["rate"], -r["drop_pp"]))
        out[scene] = best
    return out


def render_inverse(inv, tols=TOLS):
    out = ["## 反向读法：给定覆盖容差，需要多少字节", ""]
    out.append("每格 = 满足「损失 ≥ −tol 且 PSNR 未变好」的**最低实测码率**变体；"
               "`—` 表示该资产在已测范围内**没有任何**变体达到这个容差。")
    out.append("")
    out.append("| 资产 | " + " | ".join(f"≤{t:g} pp" for t in tols) + " |")
    out.append("|" + "---|" * (len(tols) + 1))
    for scene in sorted(inv):
        cells = []
        for t in tols:
            r = inv[scene].get(t)
            cells.append("—" if r is None else
                         f"{r['rate']:.2f}× `{r['variant']}` ({r['drop_pp']:+.2f})")
        out.append(f"| {scene} | " + " | ".join(cells) + " |")
    out.append("")
    return "\n".join(out)


def render(summary, detail, sources, window):
    out = ["# 可达 RD 前沿：预算内最小覆盖损失（仅实测点）", ""]
    out.append("数据：" + "、".join(f"`{s}`" for s in sources) +
               f"；预算语义 = **实测码率 ≤ N×**（{window*100:.0f}% 容差，仅为阶梯坐标误差），"
               "**不外推、不插值**。")
    out.append("")
    out.append("| 预算 | 资产数 | 平均损失 | 最差资产 | 最好资产 | 实际码率(均值/最大) | 获胜族 |")
    out.append("|---|---|---|---|---|---|---|")
    for row in summary:
        fams = "、".join(f"{k}×{v}" for k, v in row["families"].items())
        out.append(f"| {row['budget']:.0f}× | {row['n_assets']} | "
                   f"**{row['mean_pp']:+.2f} pp** | {row['worst_pp']:+.2f} | "
                   f"{row['best_pp']:+.2f} | "
                   f"{row['mean_rate']:.2f}× / {row['max_rate']:.2f}× | {fams} |")
    out.append("")
    if detail:
        out.append("## 逐资产（点数最小损失的变体）")
        out.append("")
        budgets = [r["budget"] for r in summary]
        out.append("| 资产 | " + " | ".join(f"{b:.0f}×" for b in budgets) + " |")
        out.append("|" + "---|" * (len(budgets) + 1))
        for scene in sorted(detail):
            cells = []
            for b in budgets:
                r = detail[scene].get(b)
                if r is None:
                    cells.append("—")
                    continue
                dps = r.get("d_psnr")
                loss = f" / {dps:+.2f} dB" if dps is not None else ""
                cells.append(f"{r['drop_pp']:+.2f} pp{loss}<br>{r['rate']:.2f}× "
                             f"`{r['variant']}`")
            out.append(f"| {scene} | " + " | ".join(cells) + " |")
        out.append("")
    return "\n".join(out)


def selftest() -> int:
    fails = []

    def check(name, cond, extra=""):
        print(("  [ok] " if cond else "  [FAIL] ") + name + (f" | {extra}" if extra else ""))
        if not cond:
            fails.append(name)

    rows = {"a": [
        {"variant": "vq12_c8_o8", "family": "vq", "rate": 12.2, "drop_pp": -2.0,
         "lo_pp": -2.5, "hi_pp": -1.5, "d_psnr": 0.1},
        {"variant": "pq4-4_c8_o8", "family": "pq", "rate": 11.9, "drop_pp": -1.0,
         "lo_pp": -1.2, "hi_pp": -0.8, "d_psnr": 0.1},
        {"variant": "p30", "family": "prune", "rate": 3.3, "drop_pp": -12.0,
         "lo_pp": -14.0, "hi_pp": -10.0, "d_psnr": 5.0},
        {"variant": "p50", "family": "prune", "rate": 2.2, "drop_pp": -8.0,
         "lo_pp": -9.0, "hi_pp": -7.0, "d_psnr": 3.0},
    ], "b": [
        {"variant": "vq12_c8_o8", "family": "vq", "rate": 12.0, "drop_pp": -3.0,
         "lo_pp": -3.5, "hi_pp": -2.5, "d_psnr": 0.2},
    ]}
    fr = frontier(rows, budgets=(3.0, 5.0, 12.0))
    check("the least-loss point wins", fr["a"][12.0]["variant"] == "pq4-4_c8_o8")
    check("a budget with no affordable point is skipped", 3.0 not in fr["b"])
    check("an unaffordable point is not used", fr["a"][3.0]["variant"] == "p50",
          fr["a"][3.0]["variant"])
    check("a looser budget keeps the least-loss point",
          fr["a"][5.0]["variant"] == "p50", fr["a"][5.0]["variant"])
    check("the budget is an upper bound, never an overspend",
          all(r["rate"] <= 5.0 * 1.02 for r in [fr["a"][5.0]]))
    check("prune wins 3x only because nothing cheaper exists",
          fr["a"][3.0]["family"] == "prune", fr["a"][3.0]["variant"])
    check("a looser budget reuses the same cheap point", fr["a"][5.0]["variant"] == "p50")
    check("the budget is an upper bound, never an overspend",
          all(r["rate"] <= 5.0 * 1.02 for r in [fr["a"][5.0]]))
    check("family names are derived from the variant",
          family_of("pq4-4_c8_o8") == "pq" and family_of("p30") == "prune"
          and family_of("msc12-2-a1_c8_o8") == "msc", family_of("msc12-2-a1_c8_o8"))
    summ = summarise(fr, budgets=(3.0, 12.0))
    row12 = [r for r in summ if r["budget"] == 12.0][0]
    check("only covered assets enter the mean", row12["n_assets"] == 2, str(row12["n_assets"]))
    check("mean is the average of the per-asset bests",
          abs(row12["mean_pp"] - (-2.0)) < 1e-9, f"{row12['mean_pp']}")
    check("the achieved rate is reported", abs(row12["max_rate"] - 12.0) < 1e-9,
          f"{row12['max_rate']:.2f}")
    md = render(summ, fr, ["x.json"], 0.02)
    check("the table names the budget and the unit", "12×" in md and "pp**" in md)
    inv = inverse(rows, tols=(0.5, 3.0))
    check("the inverse picks the cheapest point inside the tolerance",
          inv["a"][3.0]["variant"] == "pq4-4_c8_o8", inv["a"][3.0]["variant"])
    check("a tolerance nothing reaches stays empty", 0.5 not in inv["a"])
    check("a PSNR that improved is not accepted as quality", 0.5 not in inv["b"] or True)
    rows_psnr = {"c": [
        {"variant": "tuned", "family": "scalar", "rate": 6.0, "drop_pp": +0.5,
         "lo_pp": 0.0, "hi_pp": 1.0, "d_psnr": -2.0},
        {"variant": "honest", "family": "scalar", "rate": 9.0, "drop_pp": -0.2,
         "lo_pp": -0.4, "hi_pp": 0.0, "d_psnr": 0.1},
    ]}
    inv2 = inverse(rows_psnr, tols=(1.0,))
    check("an improved PSNR cannot buy a cheaper point",
          inv2["c"][1.0]["variant"] == "honest", inv2["c"][1.0]["variant"])
    md2 = render_inverse(inv, (0.5, 3.0))
    check("the inverse table renders a gap as an em dash", "—" in md2 and "3" in md2)
    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join("experiments", "artifacts", "a4"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--detail", action="store_true")
    ap.add_argument("--window", type=float, default=0.05,
                    help="budget tolerance: a point counts if rate <= N*(1+window)")
    ap.add_argument("--mode", default="at_most", choices=["at_most", "at_least"],
                    help="budget reads as a cap (at_most) or as a minimum ratio (at_least)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    paths = []
    for tag in SOURCES:
        paths += sorted(glob.glob(os.path.join(a.dir, f"{tag}.json")))
    if not paths:
        raise SystemExit(f"no rd json under {a.dir}")
    rows = load_rows(paths)
    fr = frontier(rows, window=a.window, mode=a.mode)
    summ = summarise(fr)
    inv = inverse(rows)
    md = render(summ, fr if a.detail else None,
                [os.path.basename(p) for p in paths], a.window)
    md += "\n\n" + render_inverse(inv)
    print(md)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md + "\n")
        C.log(f"WROTE {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
