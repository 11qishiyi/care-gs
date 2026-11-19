"""Emit the frontier as LaTeX tables for the paper.

Two tables:

* ``tab_frontier.tex`` -- per asset, the least-loss measured variant at each budget, as
  ``<coverage change> / <measured rate> <variant>``.  A cell is only filled when a *measured*
  point fits inside the budget; nothing is interpolated.
* ``tab_frontier_vs_prune.tex`` -- the head-to-head at equal measured bytes against the paper's own
  ``prune 30%`` row, whose rate is taken from the same measured tables.

Variant ids are compressed to a readable form (``SH8``, ``MSC12-6``, ``prune 90``) so the table
fits a column; the caption in ``main.tex`` says so.
"""
import argparse
import glob
import os
import re
import sys

import common as C
import frontier as F

BUDGETS = (2.0, 3.0, 5.0, 7.0, 12.0)
TEX_DIR = os.path.join("submission", "cviu")

_LABELS = [
    (re.compile(r"^sh(\d+)_g16$"), lambda m: f"SH{m.group(1)}"),
    (re.compile(r"^sh(\d+)_g32$"), lambda m: f"SH{m.group(1)}+fp32"),
    (re.compile(r"^m16_o8_sh(\d+)$"), lambda m: f"SH{m.group(1)}+g8"),
    (re.compile(r"^c(\d+)_o8_sh(\d+)$"), lambda m: f"SH{m.group(2)}+pos{m.group(1)}"),
    (re.compile(r"^msc(\d+)-(\d+)-a\d+_c(\d+)_o\d+$"),
     lambda m: f"MSC{m.group(1)}-{m.group(2)}"),
    (re.compile(r"^d(\d+)_m16_o8_sh(\d+)$"), lambda m: f"deg{m.group(1)}/SH{m.group(2)}"),
    (re.compile(r"^p(\d+)$"), lambda m: f"prune {m.group(1)}\\%"),
]


def label(name: str) -> str:
    for pat, fn in _LABELS:
        m = pat.match(name)
        if m:
            return fn(m)
    return name.replace("_", "\\_")


def num(x: float, digits: int = 2) -> str:
    s = f"{abs(x):.{digits}f}"
    return ("$-$" if x < 0 else ("$+$" if x > 0 else "")) + s


def _cell(row):
    if row is None:
        return "--"
    return f"{num(row['drop_pp'])} / {row['rate']:.2f}$\\times$ {label(row['variant'])}"


def render_frontier(detail, budgets=BUDGETS):
    head = ("\\begin{tabular}{l" + "r" * len(budgets) + "}\n\\toprule\n"
            "Asset & " + " & ".join(f"{b:g}$\\times$" for b in budgets) + " \\\\\n\\midrule\n")
    body = []
    for scene in sorted(detail):
        cells = " & ".join(_cell(detail[scene].get(b)) for b in budgets)
        body.append(scene.replace("_", "\\_") + " & " + cells + " \\\\\n")
    tail = "\\bottomrule\n\\end{tabular}\n"
    return head + "".join(body) + tail


def render_vs_prune(rows, exclude="prune"):
    head = ("\\begin{tabular}{lrrrr}\n\\toprule\n"
            "Asset & prune 30\\% & rate & best non-prune & $\\Delta$ \\\\\n"
            "\\midrule\n")
    body = []
    for scene in sorted(rows):
        rs = rows[scene]
        ref = [r for r in rs if r["variant"] == "p30"]
        if not ref:
            continue
        base = ref[0]
        cand = [r for r in rs if r["rate"] <= base["rate"] * 1.05
                and exclude not in r["family"]]
        if not cand:
            continue
        r = max(cand, key=lambda x: (x["drop_pp"], -x["rate"]))
        body.append(
            f"{scene.replace('_', chr(92) + '_')} & "
            f"{num(base['drop_pp'], 1)} ({base['rate']:.2f}$\\times$) & "
            f"{r['rate']:.2f}$\\times$ & "
            f"{num(r['drop_pp'])} {label(r['variant'])} & "
            f"{num(r['drop_pp'] - base['drop_pp'], 1)} \\\\\n")
    tail = "\\bottomrule\n\\end{tabular}\n"
    return head + "".join(body) + tail


def selftest() -> int:
    fails = []

    def check(name, cond, extra=""):
        print(("  [ok] " if cond else "  [FAIL] ") + name + (f" | {extra}" if extra else ""))
        if not cond:
            fails.append(name)

    check("SH ladder labels", label("sh8_g16") == "SH8", label("sh8_g16"))
    check("mixed labels", label("m16_o8_sh4") == "SH4+g8", label("m16_o8_sh4"))
    check("position coding labels", label("c12_o8_sh2") == "SH2+pos12")
    check("mode-selection labels", label("msc12-6-a1_c8_o8") == "MSC12-6")
    check("degree-truncation labels", label("d2_m16_o8_sh8") == "deg2/SH8")
    check("prune labels", label("p90") == "prune 90\\%", label("p90"))
    check("unknown names fall back to escaped text", label("weird_name") == "weird\\_name")
    check("negatives use math minus", num(-1.234) == "$-$1.23", num(-1.234))
    check("positives are signed", num(0.5) == "$+$0.50", num(0.5))
    detail = {"a": {2.0: {"drop_pp": -1.0, "rate": 1.9, "variant": "sh20_g16"}}, "b": {}}
    tex = render_frontier(detail, budgets=(2.0, 3.0))
    check("a missing point renders as a dash", "--" in tex)
    check("labels appear in the table", "SH20" in tex)
    rows = {"a": [{"variant": "p30", "family": "prune", "rate": 3.8, "drop_pp": -12.0},
                  {"variant": "sh8_g16", "family": "scalar", "rate": 3.6, "drop_pp": -0.4}]}
    t2 = render_vs_prune(rows)
    check("the challenger is the non-prune point", "SH8" in t2)
    check("the gain is signed", "$+$11.6" in t2, t2.splitlines()[4] if len(t2.splitlines()) > 4 else "")
    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join("experiments", "artifacts", "a4"))
    ap.add_argument("--out-frontier", default=os.path.join(TEX_DIR, "tab_frontier.tex"))
    ap.add_argument("--out-vs", default=os.path.join(TEX_DIR, "tab_frontier_vs_prune.tex"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    paths = []
    for tag in F.SOURCES:
        paths += sorted(glob.glob(os.path.join(a.dir, f"{tag}.json")))
    rows = F.load_rows(paths)
    fr = F.frontier(rows, budgets=BUDGETS)
    with open(a.out_frontier, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_frontier(fr))
    with open(a.out_vs, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_vs_prune(rows))
    C.log(f"WROTE {a.out_frontier}")
    C.log(f"WROTE {a.out_vs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
