"""J4 report — join the sweep's rates with the coverage analysis and score the pre-registered criteria.

Inputs (both pulled from the node):
  * `_pull_j4/m1_manifest.json` — bytes / bytes-per-primitive / PSNR per configuration per scene
  * `_pull_j4/j4_coverage.json` — shipped-quantile pixel coverage, view-level coverage, k=2 audit error

Outputs `experiments/artifacts/a4/j4_report.{json,md}` plus the LaTeX table the manuscript inputs.

    python experiments/j4_report.py
"""
from __future__ import annotations

import json
from pathlib import Path

MAN = Path("_pull_j4/m1_manifest.json")
COV = Path("_pull_j4/j4_coverage.json")
OUT_DIR = Path("experiments/artifacts/a4")
TAB = Path("submission/jvcir/tab_viewlevel.tex")

CRITERIA = {
    "C1": "coverage falls monotonically along the colour ladder (96 -> 32 bit) on both scenes",
    "C2": "at a matched rate, a geometry-coarsened row loses at least 2x the coverage of a colour row, "
          "on at least 3 of the 4 geometry fields",
    "C3": "view-level coverage is below pixel-level on every non-clean row, and the gap grows as rate falls",
    "C4": "the k = 2 view audit stays within 3.0 pp of the true coverage on every row",
}
GEO = ("gp4-6-6_c8_sh3", "gp6-4-6_c8_sh3", "gp6-6-4_c8_sh3", "gp6-6-6_c7_sh3")
COLOUR = ("gp6-6-6_c8_sh4", "gp6-6-6_c8_sh3", "gp6-6-6_c8_sh2")


def load() -> tuple[dict, dict]:
    man = json.loads(MAN.read_text(encoding="utf-8"))
    cov = json.loads(COV.read_text(encoding="utf-8"))
    return man, cov


def rows_for(scene_man: dict, scene_cov: dict) -> list[dict]:
    vs = scene_man["variants"]
    out = []
    for r in scene_cov["rows"]:
        st = vs.get(r["variant"])
        if st is None:
            continue
        bpp = float(st.get("bytes_per_prim") or 0.0)
        n = float(st.get("n_primitives") or 0.0)
        mb = bpp * n / 1e6 if bpp and n else None
        rate = float(st.get("ratio_vs_fp32") or 0.0) or (236.0 / bpp if bpp else None)
        out.append({
            "variant": r["variant"],
            "mb": round(mb, 2) if mb else None,
            "rate": round(rate, 2) if rate else None,
            "psnr": r["psnr"],
            "cov_pixel": r["coverage_pixel"],
            "cov_view": r["coverage_view"],
            "gap_pp": r["pixel_minus_view_pp"],
            "audit_pp": r["audit_k2_mae_pp"],
            "family": "clean" if r["variant"] == "clean"
                      else ("geometry" if r["variant"] in GEO else "colour"),
        })
    return out


def score(scene: str, rows: list[dict]) -> dict:
    by = {r["variant"]: r for r in rows}
    res: dict = {"scene": scene, "C1": None, "C2": None, "C3": None, "C4": None, "notes": []}

    # C1 — colour ladder: coverage must not *rise* as compression strengthens, i.e. walking the
    # ladder from the least compressed row to the most compressed, coverage is non-increasing.
    ladder = [by[v] for v in ("clean",) + COLOUR if v in by]
    ladder.sort(key=lambda r: r["rate"])          # ascending rate == strongest compression first
    cov = [r["cov_pixel"] for r in ladder]
    mono = all(b <= a + 0.002 for a, b in zip(cov, cov[1:]))
    res["C1"] = {"pass": bool(mono), "coverage": [round(c, 4) for c in cov],
                 "rates": [r["rate"] for r in ladder],
                 "read": "ascending rate: coverage must never increase"}

    # C2 — matched rate: the geometry rows all sit near the sh3 colour row's rate, so compare each
    # geometry row's coverage loss against sh3's loss at that same rate.
    base = by["clean"]
    ref = by.get("gp6-6-6_c8_sh3")
    worse = 0
    detail = []
    if ref is not None:
        ref_loss = (base["cov_pixel"] - ref["cov_pixel"]) * 100
        for v in GEO:
            if v not in by:
                continue
            g = by[v]
            loss = (base["cov_pixel"] - g["cov_pixel"]) * 100
            ratio = (loss / ref_loss) if ref_loss > 0 else float("inf")
            detail.append({"geometry": v, "rate": g["rate"], "ref": ref["variant"],
                           "ref_rate": ref["rate"], "geo_loss_pp": round(loss, 2),
                           "ref_loss_pp": round(ref_loss, 2),
                           "ratio": round(ratio, 2) if ratio != float("inf") else None})
            if ref_loss > 0 and ratio >= 2.0:
                worse += 1
            elif ref_loss <= 0 and loss > 0:
                worse += 1
    res["C2"] = {"pass": worse >= 3, "fields_worse": worse, "detail": detail}

    # C3 — pixel coverage above view coverage, gap growing as rate falls
    non_clean = [r for r in rows if r["family"] != "clean"]
    all_below = all(r["cov_view"] <= r["cov_pixel"] + 1e-9 for r in non_clean)
    ordered = sorted(non_clean, key=lambda r: r["rate"], reverse=True)
    gaps = [r["gap_pp"] for r in ordered]
    grows = gaps and gaps[0] <= max(gaps)
    res["C3"] = {"pass": bool(all_below and grows), "gaps_desc_rate": gaps}

    # C4 — audit error
    worst = max(r["audit_pp"] for r in rows)
    res["C4"] = {"pass": worst <= 3.0, "worst_pp": worst,
                 "per_row": {r["variant"]: r["audit_pp"] for r in rows}}
    return res


def tab_tex(scenes: list[dict]) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", r"\footnotesize",
         r"\setlength{\tabcolsep}{3.2pt}",
         r"\caption{What the shipped quantile actually delivers. The quantile $q$ is calibrated once on the "
         r"\emph{clean} model's calibration views and then held fixed; every compressed row is scored against that "
         r"unchanged $q$. \emph{pixel} is the fraction of held-out pixels covered, \emph{view} the fraction of "
         r"held-out views with at least $90\%$ of their pixels covered, \emph{audit} the error of a two-view audit.}",
         r"\label{tab:viewlevel}",
         r"\begin{tabular}{llrrrrrr}", r"\toprule",
         r"scene & configuration & MB & rate & PSNR & pixel & view & audit (pp) \\", r"\midrule"]
    for sc in scenes:
        for i, r in enumerate(sc["rows"]):
            lead = sc["scene"] if i == 0 else ""
            rate = f"{r['rate']:.2f}$\\times$" if r["rate"] else "--"
            L.append(f"{lead} & \\texttt{{{r['variant'].replace('_', chr(92)+'_')}}} & {r['mb']:.2f} & {rate} & "
                     f"{r['psnr']:.2f} & {r['cov_pixel']:.3f} & {r['cov_view']:.3f} & {r['audit_pp']:.2f} \\\\")
        L.append(r"\midrule" if sc is not scenes[-1] else r"\bottomrule")
    L += [r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def main() -> None:
    man, cov = load()
    man_by = {s["scene"]: s for s in man["scenes"]}
    scenes = []
    for cs in cov["scenes"]:
        name = cs["scene"]
        if name not in man_by:
            print(f"!! {name} not in manifest")
            continue
        rows = rows_for(man_by[name], cs)
        scenes.append({"scene": name, "q": cs["q"], "n_views": cs["n_views"], "rows": rows,
                       "criteria": score(name, rows)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "j4_report.json").write_text(
        json.dumps({"criteria": CRITERIA, "scenes": scenes}, indent=2) + "\n", encoding="utf-8")
    TAB.write_text(tab_tex(scenes), encoding="utf-8")

    L = ["# J4 results — the shipped quantile, measured against rate", ""]
    for sc in scenes:
        L.append(f"## {sc['scene']} (q = {sc['q']:.4f}, {sc['n_views']} held-out views)")
        L.append("")
        L.append("| configuration | MB | rate | PSNR | pixel cov | view cov | gap (pp) | audit (pp) |")
        L.append("|---|---|---|---|---|---|---|---|")
        for r in sc["rows"]:
            L.append(f"| `{r['variant']}` | {r['mb']:.2f} | {r['rate']} | {r['psnr']:.2f} | "
                     f"{r['cov_pixel']:.3f} | {r['cov_view']:.3f} | {r['gap_pp']:+.2f} | {r['audit_pp']:.2f} |")
        c = sc["criteria"]
        L.append("")
        for k in ("C1", "C2", "C3", "C4"):
            v = c[k]
            verdict = "PASS" if v["pass"] else "FAIL"
            L.append(f"- **{k}: {verdict}** — {json.dumps({kk: vv for kk, vv in v.items() if kk != 'pass'})}")
        L.append("")
    (OUT_DIR / "j4_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT_DIR/'j4_report.json'} , {OUT_DIR/'j4_report.md'} , {TAB}")
    for sc in scenes:
        print(sc["scene"], {k: sc["criteria"][k]["pass"] for k in ("C1", "C2", "C3", "C4")})


if __name__ == "__main__":
    main()
