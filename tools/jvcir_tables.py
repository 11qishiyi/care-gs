"""Generate the JVCIR manuscript's tables from the verified artifacts.

Every table is written to `submission/jvcir/tab_*.tex` from a JSON artifact, so the manuscript
cannot contain a stale number: `tools/verify_jvcir.py` regenerates and diffs.

    python tools/jvcir_tables.py            # write tables
    python tools/jvcir_tables.py --check    # write to a temp dir and diff (exit 1 on drift)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

A4 = Path("experiments/artifacts/a4")
OUT = Path("submission/jvcir")


HEAD = [r"\footnotesize", r"\setlength{\tabcolsep}{2.8pt}"]


def esc(s: str) -> str:
    return str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- tables
def tab_container(j3: dict) -> str:
    rows = j3["ladder"]
    base_mb = rows[0]["mb"]
    base_db = rows[0]["psnr"]
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{The container ladder on \texttt{bicycle} (6{,}131{,}954 primitives, 25 held-out views). "
         r"Each row changes one thing against the row above it. Ratio is against the fp32 PLY (1447 MB).}",
         r"\label{tab:container}",
         r"\begin{tabular}{lp{4.5cm}rrrrr}", r"\toprule",
         r"stage & what it changes & file & B/prim & PSNR & $\Delta$PSNR & ratio \\", r"\midrule"]
    for r in rows:
        d_mb = r["mb"] - base_mb
        d_db = r["psnr"] - base_db
        L.append(f"{esc(r['label'])} & {esc(r['detail'])} & {r['mb']:.2f} MB & {r['bpp']:.2f} & "
                 f"{r['psnr']:.2f} & {d_db:+.2f} & {r['ratio']:.2f}$\\times$ \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_bits(j3: dict) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Bit width, one field at a time. Panel A holds the colour block fixed (48 bit) and moves one "
         r"geometry field on a finetuned \texttt{bicycle} model. Panel B holds geometry fixed "
         r"(\texttt{gp6-6-6\_c8}) and moves the colour budget.}",
         r"\label{tab:bits}",
         r"\begin{tabular}{llrrr}", r"\toprule",
         r"\multicolumn{5}{l}{\emph{Panel A: geometry, one field at a time}} \\",
         r"spec & what it turns & bytes & PSNR & SSIM \\", r"\midrule"]
    rows = j3["midrate"]
    ctrl = rows[0]
    for r in rows:
        what = "reference point" if r is ctrl else esc(r["what"]).replace("->", r"$\rightarrow$")
        L.append(f"\\texttt{{{esc(r['spec'])}}} & {what} & {r['bytes']:,} & "
                 f"{r['psnr']:.2f} & {r['ssim']:.4f} \\\\")
    L += [r"\midrule",
          r"\multicolumn{5}{l}{\emph{Panel B: colour budget}} \\",
          r"colour bits & what it turns & file & PSNR & -- \\", r"\midrule"]
    for r in j3["colour_budget"]:
        L.append(f"{r['bits']} & colour block only & {r['mb']:.2f} MB & {r['psnr']:.2f} & -- \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_frontier(j1: dict) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Largest measured rate whose coverage loss stays within a tolerance $\varepsilon$, with the "
         r"configuration that achieves it. ``none'' in the last column means no pruning configuration on that "
         r"asset is admissible at that tolerance, so the empty column at $\varepsilon \le 1$ pp is a statement "
         r"about admissibility, not about tuning.}",
         r"\label{tab:frontier}",
         r"\begin{tabular}{rlrrrr}", r"\toprule",
         r"$\varepsilon$ (pp) & asset & configuration & rate & drop (pp) & best pruning rate \\", r"\midrule"]
    eps_keys = list(j1["e1"])
    for eps in eps_keys:
        per = j1["e1"][eps]
        for i, (name, row) in enumerate(per.items()):
            any_ = row["any"]
            prn = row["prune"]
            lead = f"${eps}$" if i == 0 else ""
            prune_cell = f"{prn['rate']:.2f}$\\times$" if prn else "none"
            if any_ is None:
                L.append(f"{lead} & {esc(name)} & -- & -- & -- & {prune_cell} \\\\")
            else:
                L.append(f"{lead} & {esc(name)} & \\texttt{{{esc(any_['variant'])}}} & "
                         f"{any_['rate']:.2f}$\\times$ & {any_['drop_pp']:+.2f} & {prune_cell} \\\\")
        L.append(r"\midrule" if eps != eps_keys[-1] else r"\bottomrule")
    L += [r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_collision(j1: dict) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Matched-rate collision at $\varepsilon = 1$ pp: at the rate the planner chooses, what the "
         r"fidelity-first and the pruning-first choice cost in coverage.}",
         r"\label{tab:collision}",
         r"\begin{tabular}{lrrllrr}", r"\toprule",
         r"asset & rate & planner & drop & fidelity-first & its drop & prune-first drop \\", r"\midrule"]
    for r in j1["e2"]:
        pf = r["prune_first"]
        L.append(f"{esc(r['scene'])} & {r['rate']:.2f}$\\times$ & {esc(r['planner']['variant'])} & "
                 f"{r['planner']['drop_pp']:+.2f} & {esc(r['fidelity_first']['variant'])} & "
                 f"{r['fidelity_first']['drop_pp']:+.2f} & "
                 f"{(('%.2f' % pf['drop_pp']) if pf else '--')} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_planners(j1: dict) -> str:
    order = ["oracle", "carp", "maxrate", "safe8", "prune_safe"]
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Four planners, one tolerance, leave-one-asset-out. Only the oracle sees the target asset's "
         r"coverage; every planner sees its measured rates. ``Violations'' counts assets shipped outside the "
         r"tolerance.}",
         r"\label{tab:planners}",
         r"\begin{tabular}{lrrrrrr}", r"\toprule",
         r"planner & \multicolumn{2}{c}{rate / oracle} & \multicolumn{2}{c}{violations} & \multicolumn{2}{c}{mean excess (pp)} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
         r" & $\varepsilon{=}1$ & $\varepsilon{=}5$ & $\varepsilon{=}1$ & $\varepsilon{=}5$ & "
         r"$\varepsilon{=}1$ & $\varepsilon{=}5$ \\", r"\midrule"]
    for k in order:
        a = j1["e2b"]["1.0"]["aggregate"][k]
        b = j1["e2b"]["5.0"]["aggregate"][k]
        fmt = lambda v: "--" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
        L.append(f"{esc(k)} & {fmt(a['mean_rate_vs_oracle'])} & {fmt(b['mean_rate_vs_oracle'])} & "
                 f"{a['violations']}/{a['n']} & {b['violations']}/{b['n']} & "
                 f"{fmt(a['mean_excess_pp_when_violating'])} & {fmt(b['mean_excess_pp_when_violating'])} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_decision(j2: dict) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Two decision rules for ``ship or do not ship'' against a tolerance, on 56 cells. A false "
         r"accept ships an asset with a guarantee it does not meet. ``prior'' is the leave-one-asset-out median "
         r"loss; ``audit'' re-renders on the shipped calibration views and counts residuals under the unchanged "
         r"quantile.}",
         r"\label{tab:decision}",
         r"\begin{tabular}{lrrrr}", r"\toprule",
         r"$\varepsilon$ (pp) & prior accuracy & prior false accepts & audit accuracy & audit false accepts \\",
         r"\midrule"]
    for eps in j2["meta"]["eps"]:
        a = j2["prior"][str(eps)]
        b = j2["audit"][str(eps)]["0.0"]
        L.append(f"{eps} & {a['accuracy']:.3f} & {a['false_accept']}/{a['n']} & "
                 f"{b['accuracy']:.3f} & {b['false_accept']}/{b['n']} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_prune(j3: dict) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Same model, same container, five pruning scores at half the primitives (\texttt{bonsai}, "
         r"1{,}244{,}819 primitives). BD-rate is measured on \texttt{bicycle} over four colour budgets without "
         r"finetuning.}",
         r"\label{tab:prune}",
         r"\begin{tabular}{lrrrr}", r"\toprule",
         r"arm & primitives & file & PSNR & $\Delta$PSNR \\", r"\midrule"]
    for r in j3["prune_score"]:
        d = "--" if r["d_psnr"] is None else f"{r['d_psnr']:+.2f}"
        L.append(f"{esc(r['arm'])} & {r['prims']:,} & {r['mb']:.2f} MB & {r['psnr']:.2f} & {d} \\\\")
    L += [r"\midrule"]
    for r in j3["bd_rate"]:
        L.append(f"BD-rate, {esc(r['arm'])} & \\multicolumn{{3}}{{r}}{{{r['bd_rate_pct']:+.2f}\\,\\%}} "
                 f"({r['points']} points) \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_cost(j3: dict) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Decode cost measured end to end (container $\rightarrow$ tensors), Peak is the decoder's "
         r"peak resident memory. The last four rows are the encoder side on \texttt{bicycle}.}",
         r"\label{tab:cost}",
         r"\begin{tabular}{llrrrr}", r"\toprule",
         r"scene & spec & file & decode (s) & peak (GB) & PSNR \\", r"\midrule"]
    for r in j3["cost"]:
        L.append(f"{esc(r['scene'])} & \\texttt{{{esc(r['spec'])}}} & {r['bytes']:,} B & {r['decode_s']:.2f} & "
                 f"{r['decode_kb'] / 1e6:.2f} & {r['psnr']:.2f} \\\\")
    L += [r"\midrule"]
    for r in j3["encode_cost"]:
        L.append(f"\\multicolumn{{2}}{{l}}{{{esc(r['stage'])}}} & -- & {r['seconds']:.2f} & -- & -- \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_gap(j3: dict) -> str:
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Our best row at or below each published file size. Positive gap = we are behind. The "
         r"published numbers are transcribed in \texttt{experiments/published\_3dgs.json}; the 0.55 dB protocol "
         r"bias measured in Section 4.1 is stated, not folded in.}",
         r"\label{tab:gap}",
         r"\begin{tabular}{llrrrrr}", r"\toprule",
         r"scene & method & their file & their PSNR & our file & our PSNR & gap (dB) \\", r"\midrule"]
    for r in j3["gap"]:
        L.append(f"{esc(r['scene'])} & {esc(r['method'])} & {r['their_mb']:.2f} MB & {r['their_psnr']:.2f} & "
                 f"{r['ours_mb']:.2f} MB & {r['ours_psnr']:.2f} & {r['gap_db']:+.2f} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_bitstream(j3: dict) -> str:
    total = sum(r["coded"] for r in j3["streams"])
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Bitstream composition of the shipped near-lossless point "
         r"(\texttt{gp8-6-6\_c9\_sh3}, 83.41 MB, 6{,}131{,}954 primitives). ``raw'' is the payload before the "
         r"\texttt{zstd} frames, ``coded'' after; the last column is bytes per primitive.}",
         r"\label{tab:bitstream}",
         r"\begin{tabular}{llrrrr}", r"\toprule",
         r"stream & what it carries & raw (MB) & coded (MB) & share & B/prim \\", r"\midrule"]
    for r in j3["streams"]:
        bpp = r["coded"] * 1e6 / 6_131_954
        L.append(f"\\texttt{{{r['name']}}} & {esc(r['what'])} & {r['raw']:.2f} & {r['coded']:.2f} & "
                 f"{100 * r['coded'] / total:.1f}\\% & {bpp:.2f} \\\\")
    L += [r"\midrule",
          f"\\multicolumn{{2}}{{l}}{{total}} & {sum(r['raw'] for r in j3['streams']):.2f} & {total:.2f} & "
          f"100.0\\% & {total * 1e6 / 6_131_954:.2f} \\\\",
          r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


def tab_perceptual(j3: dict) -> str:
    rows = j3["perceptual"]
    base = rows[0]["lpips"]
    L = [r"\begin{table}[t]", r"\centering", r"\small", *HEAD,
         r"\caption{Perceptual metrics at half the bytes on one model (\texttt{bicycle}, 48-bit colour, "
         r"LPIPS with a VGG backbone). Every arm keeps the same container; only the pruning score changes.}",
         r"\label{tab:perceptual}",
         r"\begin{tabular}{lrrrrr}", r"\toprule",
         r"arm & file & PSNR & SSIM & LPIPS & $\Delta$LPIPS \\", r"\midrule"]
    for r in rows:
        d = r["lpips"] - base
        L.append(f"{esc(r['arm'])} & {r['mb']:.2f} MB & {r['psnr']:.2f} & {r['ssim']:.4f} & "
                 f"{r['lpips']:.4f} & {d:+.4f} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(L)


BUILDERS = {
    "tab_container": (tab_container, "j3_ablations.json"),
    "tab_bits": (tab_bits, "j3_ablations.json"),
    "tab_bitstream": (tab_bitstream, "j3_ablations.json"),
    "tab_perceptual": (tab_perceptual, "j3_ablations.json"),
    "tab_frontier": (tab_frontier, "j1_reliability.json"),
    "tab_collision": (tab_collision, "j1_reliability.json"),
    "tab_planners": (tab_planners, "j1_reliability.json"),
    "tab_decision": (tab_decision, "j2_audit_decision.json"),
    "tab_prune": (tab_prune, "j3_ablations.json"),
    "tab_cost": (tab_cost, "j3_ablations.json"),
    "tab_gap": (tab_gap, "j3_ablations.json"),
}


def build(outdir: Path) -> dict[str, str]:
    cache: dict[str, dict] = {}
    out: dict[str, str] = {}
    for name, (fn, src) in BUILDERS.items():
        if src not in cache:
            cache[src] = load(A4 / src)
        out[name] = fn(cache[src])
    outdir.mkdir(parents=True, exist_ok=True)
    for name, body in out.items():
        (outdir / f"{name}.tex").write_text(body, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not args.check:
        build(OUT)
        print(f"wrote {len(BUILDERS)} tables to {OUT}")
        return 0
    tmp = OUT / "_regen"
    fresh = build(tmp)
    drift = []
    for name, body in fresh.items():
        f = OUT / f"{name}.tex"
        if not f.exists():
            drift.append(f"{name}: missing in {OUT}")
        elif f.read_text(encoding="utf-8") != body:
            drift.append(f"{name}: differs from regenerated")
    for f in tmp.glob("*.tex"):
        f.unlink()
    tmp.rmdir()
    if drift:
        print("TABLE DRIFT")
        for d in drift:
            print("  -", d)
        return 1
    print(f"tables OK: {len(fresh)} regenerate byte-identically")
    return 0


if __name__ == "__main__":
    sys.exit(main())
