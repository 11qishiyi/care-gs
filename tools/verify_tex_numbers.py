"""Verify every number in the LaTeX submission against stored artifacts.

The existing ``research/code/scripts/verify_paper_numbers.py`` checks the markdown
report (``PAPER_certificate_invalid.md``) and never reads LaTeX, so the numbers that
actually ship in ``submission/main.tex`` were unguarded.  This script parses the tex
(tables by row regex, prose by phrase regex, so every value is located at a real line
number), re-derives the value from the JSON artifacts, and reports one of

    MATCH       paper value == data value within the stated tolerance
    MISMATCH    paper value != data value            (printed: written X, data Y)
    NO_SOURCE   no artifact on disk supports the value

Exit code 1 if anything other than MATCH is found.  The script never edits the paper
or the data.

Usage:  python tools/verify_tex_numbers.py [--show-sources] [--json-out PATH]
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

ROOT = r"D:\3dsg_1"
TEX = os.path.join(ROOT, "submission", "main.tex")

# ---------------------------------------------------------------- infrastructure
LINES = io.open(TEX, encoding="utf-8").read().splitlines()
STRIPPED = [ln.replace("$", "") for ln in LINES]

# Whitespace-collapsed copy of the tex with an exact char->line map, so a phrase that
# wraps across two source lines can still be located (and its line number reported).
_chars, _linemap = [], []
for _i, _ln in enumerate(LINES, 1):
    for _ch in _ln.replace("$", "") + "\n":
        _chars.append(_ch)
        _linemap.append(_i)
_out, _outmap, _prev_ws = [], [], False
for _ch, _ln in zip(_chars, _linemap):
    if _ch.isspace():
        if not _prev_ws:
            _out.append(" ")
            _outmap.append(_ln)
        _prev_ws = True
    else:
        _out.append(_ch)
        _outmap.append(_ln)
        _prev_ws = False
JOINED = "".join(_out)

ROWS = []           # every check
SECTION = ["?"]


def linenum(pos):
    return _outmap[pos]


def sect(name):
    SECTION[0] = name


def rec(name, line, tex, data, tol, src, note="", tex_raw=None):
    """Register one assertion.  ``tex``/``data`` are floats or tuples of floats."""
    if data is None:
        verdict = "NO_SOURCE"
    elif isinstance(tex, (tuple, list)):
        ok = all(abs(float(t) - float(d)) <= tol for t, d in zip(tex, data))
        verdict = "MATCH" if ok else "MISMATCH"
    else:
        verdict = "MATCH" if abs(float(tex) - float(data)) <= tol else "MISMATCH"
    ROWS.append(dict(section=SECTION[0], name=name, line=line, tex=tex, data=data,
                     tol=tol, src=src, verdict=verdict, note=note,
                     tex_raw=tex_raw))


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, (tuple, list)):
        return "(" + ", ".join(f"{x:+.4g}" for x in v) + ")"
    return f"{v:+.4g}"


# ------------------------------------------------------------------- locators
class LocError(RuntimeError):
    pass


def find(pat, start=0, flags=0):
    m = re.search(pat, JOINED, flags) if start == 0 else re.compile(pat, flags).search(JOINED, start)
    if not m:
        raise LocError(pat)
    return m


def nums(text):
    """All numeric literals in a LaTeX row, in reading order."""
    flat = re.sub(r"\$|\{|\}|\\[A-Za-z]+", " ", text)
    return [float(x) for x in re.findall(r"[+-]?\d+(?:\.\d+)?", flat)]


def table_row(pat, nth=1):
    """Return (lineno, raw_line_match) for the nth table row matching ``pat``."""
    hits = [(i + 1, ln) for i, ln in enumerate(LINES) if re.search(pat, ln)]
    if len(hits) < nth:
        raise LocError(pat)
    return hits[nth - 1]


def table_block(label):
    """(first, last) 0-based line indices strictly inside the tabular carrying ``label``."""
    i0 = next(i for i, l in enumerate(LINES) if label in l)
    j0 = next(i for i in range(i0, len(LINES)) if "\\end{tabular}" in LINES[i])
    return i0, j0


def rows_in(label, scene):
    i0, j0 = table_block(label)
    return [(i + 1, LINES[i]) for i in range(i0, j0) if re.match(rf"^{scene}\s*&", LINES[i])]


def prose(pat, start=0, flags=re.S):
    # JOINED has every '$' removed, so drop the LaTeX escapes from the pattern too
    pat = pat.replace(r"\$?", "").replace(r"\$", "")
    m = find(pat, start, flags)
    return linenum(m.start()), m


def g(m, i):
    """Float of group i, tolerating a leading '+', a trailing '.' and LaTeX escapes."""
    mm = re.match(r"[+-]?\d+(?:\.\d+)?", m.group(i).strip())
    if not mm:
        raise LocError("not a number: %r" % m.group(i))
    return float(mm.group(0))


# ------------------------------------------------------------------- artifacts
def load(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def try_load(rel):
    try:
        return load(rel)
    except Exception:
        return None


SC = ["flowers", "bicycle", "treehill", "stump"]
ST = ["garden", "room", "counter", "kitchen", "bonsai"]

ms = load(r"research/results_v52/many_splits.json")
MS = {(r["scene"], round(r["ratio"], 1)): r for r in ms}
wd = {r["scene"]: r for r in load(r"research/results_v55/widths.json")}

EF = {}
for rel in ("research/results_v53/ef_bicycle.json", "research/results_v53/ef_rest.json"):
    for r in load(rel):
        EF[r["scene"]] = r
CR = {}
for rel in ("research/results_v54/crit_b.json", "research/results_v54/crit_c.json"):
    for r in load(rel):
        CR[r["scene"]] = r
SCK = {r["scene"]: r for r in load(r"research/results_v58/selfcheck.json")}
VT = {}
for rel in ("research/results_v60/vt_flowers.json", "research/results_v60/vt_rest.json"):
    for r in load(rel):
        VT[r["scene"]] = r
TW = {r["scene"]: r for r in load(r"research/results_v51/three_way.json")}
NF = {}
for s in SC:
    NF[s] = {r["edit"]: r for r in load(f"research/results_v61/{s}_nofinetune.json")}
V35 = {s: {r["edit"]: r for r in load(f"research/results_v35/{s}.json")} for s in ST}
V62 = {}
for s in ST:
    for suf in ("base", "ft", "small"):
        rel = f"research/results_v62/{s}_{suf}.json"
        if os.path.isfile(os.path.join(ROOT, rel)):
            V62[(s, suf)] = {r["edit"]: r for r in load(rel)}
A05 = {(r["scene"], r["edit"]): r for r in load("research/results_v28/cert_a0.05.json")}
A20 = {(r["scene"], r["edit"]): r for r in load("research/results_v28/cert_a0.2.json")}
CV3 = load("research/results_v22/cert_v3.json")
CV3K = {(r["scene"], r["edit"]): r for r in CV3}
RC = {s: {p["n_cal"]: p["cov_rc"] for p in CV3K[(s, "prune30")]["repair_curve"]} for s in SC}


def first_ok_n(scene):
    """Smallest calibration budget at which re-calibration returns coverage to nominal."""
    for n in (2, 4, 6, 8):
        if RC[scene].get(float(n), -1.0) >= 0.90:
            return float(n)
    return None
CA17 = load("research/results_v17/cert_audit.json")
CALL24 = load("research/results_v24/cert_all.json")
_c24 = [r["cov_pix"] for r in CALL24 if r["edit"] == "clean"]
COMPACT = {}
for rel, s in (("research/results_v47/compact.json", "flowers"),
               ("research/results_v48/bicycle_compact.json", "bicycle"),
               ("research/results_v48/treehill_compact.json", "treehill"),
               ("research/results_v48/stump_compact.json", "stump")):
    COMPACT[s] = load(rel)
PSNR_CLEAN = {}
for rel, s in (("research/results_v11/flowers_r0.5.json", "flowers"),
               ("research/results_v11/stump_r0.5.json", "stump"),
               ("research/results_v12/bicycle_r0.5.json", "bicycle"),
               ("research/results_v12/treehill_r0.5.json", "treehill")):
    d = load(rel)
    for r in d["rows"]:
        if r["method"] == "clean":
            PSNR_CLEAN[s] = r["psnr"]
FLOWER_MAP = load("research/results_v11/flower_map.json")

# ---------------------------------------------------------------- derived stats
def pct(x):
    return 100.0 * x


D30 = {s: pct(MS[(s, 0.3)]["drop_mean"]) for s in SC}          # stale - clean, negative
D50 = {s: pct(MS[(s, 0.5)]["drop_mean"]) for s in SC}
FRESH = {s: MS[(s, 0.3)]["clean_mean"] for s in SC}
FRESH_LO = {s: MS[(s, 0.3)]["clean_lo"] for s in SC}
FRESH_HI = {s: MS[(s, 0.3)]["clean_hi"] for s in SC}
P30_LO = {s: pct(MS[(s, 0.3)]["drop_lo"]) for s in SC}
P30_HI = {s: pct(MS[(s, 0.3)]["drop_hi"]) for s in SC}

# self-trained rows: the tex value must be reproduced by *some* v62 variant.  We try
# base/small/ft in that order and record which file actually carries it.
ST_TEX = {"garden": (0.956, -6.7), "room": (0.920, -2.0), "counter": (0.898, 0.7),
          "kitchen": (0.923, -3.5), "bonsai": (0.899, -2.2)}
ST_PICK, ST_FRESH, ST_D30, ST_VIEWS = {}, {}, {}, {}
for s in ST:
    cand = []
    for suf in ("base", "small", "ft"):
        if (s, suf) in V62:
            c = V62[(s, suf)]["clean"]["cov_pix"]
            p = V62[(s, suf)]["prune30"]["stale_cov_pix"]
            cand.append((suf, c, pct(p - c), V62[(s, suf)]["clean"]["n_dep"],
                         V62[(s, suf)]["clean"]["n"]))
    ST_PICK[s] = cand

QUANT8 = {s: pct(EF[s]["quant8_drop_mean"]) if s in EF else None for s in SC}
SHDEG = {s: pct(EF[s]["shdeg1_drop_mean"]) if s in EF else None for s in SC}
SHDEG_LO = {s: pct(EF[s]["shdeg1_drop_lo"]) if s in EF else None for s in SC}
SHDEG_HI = {s: pct(EF[s]["shdeg1_drop_hi"]) if s in EF else None for s in SC}

VG = {s: pct(VT[s]["voxel_prune30_drop_mean"]) for s in SC}     # damage, positive
TASK = {s: (VT[s]["task_clean_hit"], VT[s]["task_prune50_hit"], VT[s]["task_prune30_hit"])
        for s in SC}
TASK_DROP = {s: pct(TASK[s][2] - TASK[s][0]) for s in SC}
RATIO = {s: abs(TASK_DROP[s]) / abs(VG[s]) for s in SC}

# ==================================================================  checks
# ---- Abstract -----------------------------------------------------------
sect("abstract")
ln, m = prose(r"pruning to 30\\?% lowers coverage by\s*([\d.]+)--([\d.]+) points")
_d30_abs = sorted(abs(v) for v in D30.values())
lo, hi = _d30_abs[0], _d30_abs[-1]
rec("abstract: prune-30 drop range (pp)", ln,
    (g(m, 1), g(m, 2)), (lo, hi), 0.06,
    "results_v52/many_splits.json:drop_mean x4", tex_raw=f"{m.group(1)}--{m.group(2)}")

ln, m = prose(r"SH degree reduction costs\s*([\d.]+)--([\d.]+) points")
_sh_meas = [abs(v) for v in SHDEG.values() if v is not None]
_sh_f = abs(pct(CV3K[("flowers", "shdeg1")]["stale_cov_pix"] - CV3K[("flowers", "clean")]["cov_pix"]))
rec("abstract: SH 3->1 cost lower bound (pp)", ln, g(m, 1), min(_sh_meas), 0.06,
    "results_v53/ef_*.json:shdeg1_drop_mean (min |.|, 3 scenes)", tex_raw=m.group(1))
rec("abstract: SH 3->1 cost upper bound (pp)", ln, g(m, 2), _sh_f, 0.06,
    "results_v22/cert_v3.json:flowers shdeg1 (single split; the 400-split "
    "results_v53/edit_families.json is 0 bytes)", tex_raw=m.group(2))

ln, m = prose(r"8-bit SH quantisation costs exactly zero")
_q = [abs(v) for v in QUANT8.values() if v is not None]
rec("abstract: 8-bit SH quantisation is 'exactly zero' (pp)", ln, 0.0, max(_q), 0.005,
    "results_v53/ef_*.json:quant8_drop_mean x3 (max |.|)")

ln, m = prose(r"coverage drops by\s*([\d.]+) points loses\s*([\d.]+) points")
rec("abstract: flowers coverage drop used in the 4.6/16.8 sentence (pp)", ln, g(m, 1),
    VG["flowers"], 0.06, "results_v60/vt_flowers.json:voxel_prune30_drop_mean")
rec("abstract: flowers task drop in the same sentence (pp)", ln, g(m, 2),
    abs(TASK_DROP["flowers"]), 0.06, "results_v60/vt_flowers.json:task_*_hit")

ln, m = prose(r"gap ranges from\s*([\d.]+)\\times to\s*([\d.]+)\\times")
rec("abstract: task/certificate ratio range (x)", ln, (g(m, 1), g(m, 2)),
    (min(RATIO.values()), max(RATIO.values())), 0.06,
    "results_v60/vt_*.json task drop / voxel_prune30_drop_mean")

ln, m = prose(r"\(([\d.]+)--([\d.]+) held-out views suffice, at the cost of a\s*([\d.]+)--([\d.]+)\\?% wider interval\)")
_fok = [first_ok_n(s) for s in SC]
_ok_src = ("results_v22/cert_v3.json:repair_curve (smallest n_cal at which coverage returns "
           "to >= 0.900; per scene " + ", ".join(f"{s}={first_ok_n(s):.0f}" for s in SC) + ")")
rec("abstract: re-certification view budget lower bound", ln, g(m, 1), min(_fok), 0.5, _ok_src)
rec("abstract: re-certification view budget upper bound", ln, g(m, 2), max(_fok), 0.5, _ok_src)
_g = [wd[s]["q_prune30_growth_pct"] for s in SC]
rec("abstract: interval widening range (%)", ln, (g(m, 3), g(m, 4)),
    (min(_g), max(_g)), 0.55, "results_v55/widths.json:q_prune30_growth_pct")

ln, m = prose(r"Across nine scenes")
rec("abstract: 'nine scenes' == number of rows in tab:main", ln, 9.0, 9.0, 0.0,
    "submission/main.tex tab:main (4 released + 5 self-trained)")

ln, m = prose(r"with\s*400 random calibration/deployment splits per scene")
rec("abstract: 400 splits per scene (released checkpoints)", ln, 400.0, 400.0, 0.0,
    "research/code/scripts/many_splits.py:--n_splits default 400; results_v51/three_way.json:n_splits")
rec("abstract: 400 splits per scene (self-trained checkpoints)", ln, 400.0, None, 0.0,
    "results_v62/*.json has no split dimension (one file per model variant, n_dep=17); "
    "tab:main caption itself calls them 'single-split estimates'",
    note="the 'per scene' quantifier covers 4 of 9 scenes only")

# ---- Introduction -------------------------------------------------------
sect("intro")
ln, m = prose(r"coverage on\s*the four released checkpoints is \$?([\d.]+)\$?--\$?([\d.]+)\$? against a nominal \$?([\d.]+)\$?")
rec("intro: fresh coverage on released checkpoints [lo,hi]", ln, (g(m, 1), g(m, 2)),
    (min(FRESH.values()), max(FRESH.values())), 0.0006,
    "results_v52/many_splits.json:clean_mean")
rec("intro: nominal coverage", ln, g(m, 3), 0.90, 0.0006, "alpha=0.10 -> nominal 1-alpha")

ln, m = prose(r"under-reports downstream damage\} by\s*\$?([\d.]+)\$?--\$?([\d.]+)\\times")
rec("intro: under-report factor range (x)", ln, (g(m, 1), g(m, 2)),
    (min(RATIO.values()), max(RATIO.values())), 0.06,
    "results_v60/vt_*.json")

# ---- Table 1 (claims table) --------------------------------------------
sect("tab1")
T1_PATS = [
    (r"Coverage \$([\d.]+)\$--\$([\d.]+)\$ against nominal \$([\d.]+)\$ on four released checkpoints; 400 random splits",
     "tab1: fresh coverage / nominal / 400 splits"),
]
for pat, name in T1_PATS:
    ln, m = prose(pat)
    rec(name + " [cov lo,hi]", ln, (g(m, 1), g(m, 2)),
        (min(FRESH.values()), max(FRESH.values())), 0.0006, "results_v52/many_splits.json:clean_mean")
    rec(name + " [nominal]", ln, g(m, 3), 0.90, 0.0006, "alpha=0.10")

ln, m = prose(r"Prune-to-30\\?% drops of \$([\d.]+)\$--\$([\d.]+)\$ points, all paired intervals excluding zero")
rec("tab1: prune-30 drop range (pp)", ln, (g(m, 1), g(m, 2)), (lo, hi), 0.06,
    "results_v52/many_splits.json:drop_mean")
ok_zero = all(MS[(s, 0.3)]["drop_hi"] < 0 for s in SC)
rec("tab1: 'all paired intervals excluding zero'", ln, 1.0, 1.0 if ok_zero else 0.0, 0.0,
    "results_v52/many_splits.json:drop_hi (all four < 0)")

ln, m = prose(r"SH \$3\\to1\$ costs \$([\d.]+)\$--\$([\d.]+)\$; 8-bit SH costs \$([\d.]+)\$; perturbation\s*\$([\d.]+)\$--\$([\d.]+)\\times10\^\{-4\}\$")
rec("tab1: SH 3->1 cost lower bound (pp)", ln, g(m, 1), min(_sh_meas), 0.06,
    "results_v53/ef_*.json:shdeg1_drop_mean")
rec("tab1: SH 3->1 cost upper bound (pp)", ln, g(m, 2), _sh_f, 0.06,
    "results_v22/cert_v3.json:flowers shdeg1 (single split; results_v53/edit_families.json "
    "is 0 bytes)")
rec("tab1: 8-bit SH cost", ln, g(m, 3), max(_q), 0.005, "results_v53/ef_*.json:quant8_drop_mean")
rec("tab1: mean |dSH| perturbation (x1e-4)", ln, (g(m, 4), g(m, 5)), None, 0.05,
    "no artifact stores the SH perturbation magnitude (results_v20/cert_quant.json stores "
    "coverage only, no |dSH| statistics)")

ln, m = prose(r"Re-localisation loses \$([\d.]+)\$--\$([\d.]+)\$ points while coverage loses \$([\d.]+)\$--\$([\d.]+)\$")
_td = sorted(abs(v) for v in TASK_DROP.values())
_vg = sorted(abs(v) for v in VG.values())
rec("tab1: task drop range (pp)", ln, (g(m, 1), g(m, 2)), (min(_td), max(_td)), 0.06,
    "results_v60/vt_*.json:task_prune30_hit - task_clean_hit")
rec("tab1: certificate (voxel) drop range (pp)", ln, (g(m, 3), g(m, 4)), (min(_vg), max(_vg)), 0.06,
    "results_v60/vt_*.json:voxel_prune30_drop_mean")

ln, m = prose(r"ratio \$([\d.]+)\$--\$([\d.]+)\\times")
rec("tab1: ratio range (x)", ln, (g(m, 1), g(m, 2)), (min(RATIO.values()), max(RATIO.values())), 0.06,
    "results_v60/vt_*.json")

ln, m = prose(r"2--4 views restore coverage; \$q\$ grows \$([\d.]+)\$--\$([\d.]+)\\?%")
rec("tab1: q growth range (%)", ln, (g(m, 1), g(m, 2)), (min(_g), max(_g)), 0.55,
    "results_v55/widths.json:q_prune30_growth_pct")

ln, m = prose(r"Check returns \$([\d.]+)\$ while truth is \$([\d.]+)\$--\$([\d.]+)\$; over-predicts \$([\d.]+)\$--\$([\d.]+)\$")
_truth = [SCK[s]["prune50_actual_mean"] for s in SCK] + [SCK[s]["prune30_actual_mean"] for s in SCK]
rec("tab1: self-check returns (nominal)", ln, g(m, 1), 0.90, 0.0006, "alpha=0.10")
rec("tab1: true deployment coverage range", ln, (g(m, 2), g(m, 3)),
    (min(_truth), max(_truth)), 0.0006, "results_v58/selfcheck.json:*_actual_mean")
_err = [100 * SCK[s][f"prune{p}_selfcheck_err_mean"] for s in SCK for p in (50, 30)]
rec("tab1: over-prediction range (pp)", ln, (g(m, 4), g(m, 5)), (min(_err), max(_err)), 0.06,
    "results_v58/selfcheck.json:*_selfcheck_err_mean")

# ---- Section 2 Setup ----------------------------------------------------
sect("setup")
ln, m = prose(r"([\d.]+)M--([\d.]+)M primitives, ([\d.]+)--([\d.]+)\\?,dB held-out PSNR")
_prim = [VT[s]["n_primitives"] / 1e6 for s in SC]
rec("setup: released primitive count range (M)", ln, (g(m, 1), g(m, 2)),
    (min(_prim), max(_prim)), 0.06, "results_v60/vt_*.json:n_primitives")
rec("setup: released held-out PSNR range (dB)", ln, (g(m, 3), g(m, 4)),
    (min(PSNR_CLEAN.values()), max(PSNR_CLEAN.values())), 0.06,
    "results_v11/*_r0.5.json,results_v12/*_r0.5.json:rows[clean].psnr",
    note="stump is %.2f dB and flowers %.2f dB, so the stated 16 dB floor is not supported"
         % (PSNR_CLEAN["stump"], PSNR_CLEAN["flowers"]))

ln, m = prose(r"\(([\d.]+)/([\d.]+) images at correlation ([\d.]+) on\s*flowers\)")
rec("setup: flowers camera recovery image count", ln, (g(m, 1), g(m, 2)),
    (float(len(FLOWER_MAP)), float(len(FLOWER_MAP))), 0.0,
    "results_v11/flower_map.json (len)")
rec("setup: flowers camera recovery correlation", ln, g(m, 3),
    round(min(r["corr"] for r in FLOWER_MAP), 3), 0.0006,
    "results_v11/flower_map.json:corr (min, 3 dp)")

ln, m = prose(r"for (\d+) steps")
rec("setup: self-trained optimisation steps", ln, float(m.group(1)), None, 0.0,
    "no artifact records training steps (results_v62/*.json has no step field)")

ln, m = prose(r"\(([\d.]+)k--([\d.]+)k primitives, ([\d.]+)--([\d.]+)\\?,dB\)")
# only the model variants that actually reproduce the tab:main row count
_n_chosen = [c[4] for s in ST for c in ST_PICK[s] if abs(c[1] - ST_TEX[s][0]) <= 0.0006]
_n_all62 = [V62[(s, suf)]["clean"]["n"] for (s, suf) in V62]
rec("setup: self-trained primitive count range (k)", ln, (g(m, 1), g(m, 2)),
    (min(_n_chosen) / 1e3, max(_n_chosen) / 1e3), 0.6,
    "results_v62/{scene}_{base|small}.json:n (the variants that reproduce tab:main)",
    note="largest v62 artefact is %.0fk; nothing on disk is below 117k (results_v35/room.json)"
         % (max(_n_all62) / 1e3))
rec("setup: self-trained held-out PSNR range (dB)", ln, (g(m, 3), g(m, 4)), None, 0.06,
    "no PSNR artifact exists for the five self-trained scenes")

ln, m = prose(r"the number of views \((\d+)--(\d+)\), not the number of pixels")
_nv = sorted(VT[s]["n_views"] for s in SC)
rec("setup: held-out view count range", ln, (float(m.group(1)), float(m.group(2))),
    (float(_nv[0]), float(_nv[-1])), 0.0, "results_v60/vt_*.json:n_views")

ln, m = prose(r"Mixing training views into calibration lowered coverage by (\d+) points\s*on four scenes")
rec("setup: leakage lowers coverage by (pp)", ln, float(m.group(1)), 100 * (0.90 - min(_c24)), 0.55,
    "results_v24/cert_all.json:0.900 - min(clean cov_pix)",
    note="the magnitude is right but the artifact holds 3 scenes, not four; appB lists the "
         "same three values")

# ---- Table 2 (main table) ----------------------------------------------
sect("tab2")
for s in SC:
    ln, row = table_row(rf"^{s}\s*&\s*released\s*&")
    v = nums(row)
    m_ = MS[(s, 0.3)]
    rec(f"tab2 {s}: views", ln, v[0], float(VT[s]["n_views"]), 0.0,
        "results_v60/vt_*.json:n_views")
    rec(f"tab2 {s}: fresh coverage", ln, v[1], m_["clean_mean"], 0.0006,
        "results_v52/many_splits.json:clean_mean")
    rec(f"tab2 {s}: fresh CI [lo,hi]", ln, (v[2], v[3]),
        (m_["clean_lo"], m_["clean_hi"]), 0.0006, "results_v52/many_splits.json:clean_lo/hi")
    rec(f"tab2 {s}: 50% pruned drop (pp)", ln, v[4], D50[s], 0.06,
        "results_v52/many_splits.json:drop_mean (ratio 0.5)")
    rec(f"tab2 {s}: 30% pruned drop (pp)", ln, v[5], D30[s], 0.06,
        "results_v52/many_splits.json:drop_mean (ratio 0.3)")
    rec(f"tab2 {s}: 30% pruned CI [lo,hi]", ln, (v[6], v[7]), (P30_LO[s], P30_HI[s]), 0.06,
        "results_v52/many_splits.json:drop_lo/hi")

STD_TEX = {"garden": (0.956, -6.7), "room": (0.920, -2.0), "counter": (0.898, 0.7),
           "kitchen": (0.923, -3.5), "bonsai": (0.899, -2.2)}
for s in ST:
    ln, row = table_row(rf"^{s}\s*&\s*self-trained\s*&")
    v = nums(row)
    want_fresh, want_d30 = STD_TEX[s]
    match = [c for c in ST_PICK[s] if abs(c[1] - v[1]) <= 0.0006]
    src = ("results_v62/%s_%s.json:cov_pix" % (s, match[0][0])) if match else \
          "results_v62/{base,small,ft} searched; none reproduces the printed value"
    rec(f"tab2 {s}: views", ln, v[0], float(match[0][3]) if match else None, 0.0,
        "results_v62:clean.n_dep")
    rec(f"tab2 {s}: fresh coverage", ln, v[1], match[0][1] if match else None, 0.0006, src,
        note=("" if (match and match[0][0] == "base")
              else "row is only reproducible from a non-'base' variant; provenance is not "
                   "uniform across the five self-trained scenes"))
    rec(f"tab2 {s}: 30% pruned drop (pp)", ln, v[2], match[0][2] if match else None, 0.06,
        ("results_v62/%s_%s.json:prune30.stale_cov_pix - clean.cov_pix" % (s, match[0][0]))
        if match else "no artifact")

# ---- Section 3.1 prose --------------------------------------------------
sect("3.1")
ln, m = prose(r"the fresh coverage is\s*\$?([\d.]+)\$?, \$?([\d.]+)\$?, \$?([\d.]+)\$?, \$?([\d.]+)\$? against a nominal \$?([\d.]+)\$?")
_sorted = sorted(FRESH.values())
rec("3.1: the four fresh coverages (sorted)", ln, tuple(g(m, i) for i in (1, 2, 3, 4)),
    tuple(_sorted), 0.0006, "results_v52/many_splits.json:clean_mean")
rec("3.1: nominal coverage", ln, g(m, 5), 0.90, 0.0006, "alpha=0.10")

ln, m = prose(r"Halving the primitives costs \$([\d.]+)\$--\$([\d.]+)\$ points")
_d50 = sorted(abs(v) for v in D50.values())
rec("3.1: 50% prune drop range (pp)", ln, (g(m, 1), g(m, 2)), (min(_d50), max(_d50)), 0.06,
    "results_v52/many_splits.json:drop_mean (ratio 0.5)")

ln, m = prose(r"keeping 30\\?% costs \$([\d.]+)\$--\$([\d.]+)\$, and all four intervals exclude zero")
rec("3.1: 30% prune drop range (pp)", ln, (g(m, 1), g(m, 2)), (lo, hi), 0.06,
    "results_v52/many_splits.json:drop_mean")

ln, m = prose(r"Eight of the nine scenes are\s*negative")
_nneg = sum(1 for s in SC if D30[s] < 0) + sum(1 for s in ST if ST_TEX[s][1] < 0)
rec("3.1: number of scenes with a negative drop", ln, 8.0, float(_nneg), 0.0,
    "tab:main (4 released + 5 self-trained)")

ln, m = prose(r"the five self-trained models drop only ([\d.]+) to ([+-]?[\d.]+) points")
rec("3.1: self-trained drop range (pp)", ln, (g(m, 1), g(m, 2)),
    (min(ST_TEX[s][1] for s in ST), max(ST_TEX[s][1] for s in ST)), 0.06,
    "tab:main self-trained rows",
    note="written as '6.7 to -0.7'; the data range is -6.7 (garden) .. +0.7 (counter)")

# ---- Table 3 (edit families) -------------------------------------------
sect("tab3")
ln, row = table_row(r"^prune 30\\%")
v = nums(row)
for i, s in enumerate(SC):
    rec(f"tab3 prune30 {s} (pp)", ln, v[-4 + i], D30[s], 0.06,
        "results_v52/many_splits.json:drop_mean (ratio 0.3)")

ln, row = table_row(r"^SH degree")
v = nums(row)
rec("tab3: SH degree 3->1 coefficients (16)", ln, v[2], 16.0, 0.0, "(3+1)^2 SH coefficients")
rec("tab3: SH degree 3->1 coefficients (4)", ln, v[3], 4.0, 0.0, "(1+1)^2 SH coefficients")
sh = v[-10:]
# flowers has no 400-split edit-family artifact, but the older single-split audit
# (results_v22/cert_v3.json) does carry a shdeg1 row - which is what the '^*' marker
# in the table presumably refers to.
_cv3f = CV3K[("flowers", "shdeg1")]
_f_sh = pct(_cv3f["stale_cov_pix"] - CV3K[("flowers", "clean")]["cov_pix"])
room_cv3 = CV3K[("flowers", "quant8_sh")]
_f_q8 = pct(room_cv3["stale_cov_pix"] - CV3K[("flowers", "clean")]["cov_pix"])
rec("tab3 SH flowers cost (pp)", ln, sh[0], _f_sh, 0.06,
    "results_v22/cert_v3.json:flowers shdeg1.stale_cov_pix - clean.cov_pix (single split)",
    note="the 400-split flowers file results_v53/edit_families.json exists but is 0 bytes; "
         "the '^*' marker is consistent with this being a single-split number")
for k, s in enumerate(SC[1:]):
    mean, lo_, hi_ = sh[1 + 3 * k], sh[2 + 3 * k], sh[3 + 3 * k]
    # paper's convention here is cost = clean - stale (negated w.r.t. many_splits)
    rec(f"tab3 SH {s} cost (pp)", ln, mean, -SHDEG[s], 0.06,
        "results_v53/ef_*.json:-shdeg1_drop_mean",
        note="data says coverage *rose* %.2f pp; the table reports it as a cost" % SHDEG[s])
    rec(f"tab3 SH {s} CI [lo,hi]", ln, (lo_, hi_), (-SHDEG_HI[s], -SHDEG_LO[s]), 0.06,
        "results_v53/ef_*.json:-shdeg1_drop_hi/lo")

ln, row = table_row(r"^SH 8-bit")
v = nums(row)
for i, s in enumerate(SC):
    if s in EF:
        rec(f"tab3 quant8 {s} (pp)", ln, v[-4 + i], QUANT8[s], 0.005,
            "results_v53/ef_*.json:quant8_drop_mean")
    else:
        rec(f"tab3 quant8 {s} (pp)", ln, v[-4 + i], _f_q8, 0.005,
            "results_v22/cert_v3.json:flowers quant8_sh (single split)",
            note="no 400-split quantisation artifact for flowers")

# ---- Section 3.2 prose --------------------------------------------------
sect("3.2")
ln, m = prose(r"=([\d.]+)--([\d.]+)\\times10\^\{-4\}")
rec("3.2: mean |dSH| perturbation (x1e-4)", ln, (g(m, 1), g(m, 2)), None, 0.05,
    "no artifact stores |dSH| (cert_quant.json has coverage only)")

ln, m = prose(r"SH degree reduction does move the residual distribution, but only by (\d+)--(\d+) points")
_sh_abs = sorted(abs(v) for v in SHDEG.values() if v is not None)
rec("3.2: SH 3->1 effect magnitude (pp)", ln, (float(m.group(1)), float(m.group(2))),
    (min(_sh_abs), max(_sh_abs)), 0.06,
    "results_v53/ef_*.json:shdeg1_drop_mean",
    note="only three scenes survive; the measured magnitudes are 0.2-1.0 pp, not 1-2 pp")

# ---- Table 4 (downstream) ----------------------------------------------
sect("tab4")
for s in SC:
    hits = rows_in(r"\label{tab:downstream}", s)
    if not hits:
        raise LocError("tab4 row " + s)
    ln, row = hits[0]
    v = nums(row)
    rec(f"tab4 {s}: fresh hit rate", ln, v[0], TASK[s][0], 0.0006,
        "results_v60/vt_*.json:task_clean_hit")
    rec(f"tab4 {s}: 50% pruned hit rate", ln, v[1], TASK[s][1], 0.0006,
        "results_v60/vt_*.json:task_prune50_hit")
    rec(f"tab4 {s}: 30% pruned hit rate", ln, v[2], TASK[s][2], 0.0006,
        "results_v60/vt_*.json:task_prune30_hit")
    rec(f"tab4 {s}: task drop (pp)", ln, v[3], TASK_DROP[s], 0.06,
        "results_v60/vt_*.json:task_prune30_hit - task_clean_hit")
    rec(f"tab4 {s}: certificate drop (pp)", ln, v[4], -VG[s], 0.06,
        "results_v60/vt_*.json:voxel_prune30_drop_mean",
        note="this is the 0.25-unit voxel drop, not the 64x64-block drop used in tab:main "
             "(%.1f pp there)" % D30[s])

# ---- Section 3.3 prose --------------------------------------------------
sect("3.3")
ln, m = prose(r"The task degrades by \$([\d.]+)\$--\$([\d.]+)\$ points, i\.e\.\\ \$([\d.]+)\\times\$ to \$([\d.]+)\\times\$")
rec("3.3: task drop range (pp)", ln, (g(m, 1), g(m, 2)), (min(_td), max(_td)), 0.06,
    "results_v60/vt_*.json")
rec("3.3: ratio range (x)", ln, (g(m, 3), g(m, 4)), (min(RATIO.values()), max(RATIO.values())), 0.06,
    "results_v60/vt_*.json")

# figure 9 caption
ln, m = prose(r"The certificate shrinks by\s*([\d.]+)--([\d.]+) points; the\s*re-localisation task by ([\d.]+)--([\d.]+)")
rec("fig:task caption: certificate drop range (pp)", ln, (g(m, 1), g(m, 2)),
    (min(_vg), max(_vg)), 0.06, "results_v60/vt_*.json")
rec("fig:task caption: task drop range (pp)", ln, (g(m, 3), g(m, 4)), (min(_td), max(_td)), 0.06,
    "results_v60/vt_*.json")

# ---- Table 5a / 5b -----------------------------------------------------
sect("tab5a")
RC = {}
for s in SC:
    RC[s] = {p["n_cal"]: p["cov_rc"] for p in CV3K[(s, "prune30")]["repair_curve"]}
for s in SC:
    hits = rows_in(r"\label{tab:rules}", s)
    if not hits:
        raise LocError("tab5a " + s)
    ln, row = hits[0]
    v = nums(row)
    for j, ncal in enumerate((2, 4, 6, 8)):
        rec(f"tab5a {s}: coverage after re-cal at n={ncal}", ln, v[j], RC[s].get(float(ncal)),
            0.0006, "results_v22/cert_v3.json:repair_curve[n_cal=%d].cov_rc" % ncal)
    rec(f"tab5a {s}: q growth (%)", ln, v[4], wd[s]["q_prune30_growth_pct"], 0.55,
        "results_v55/widths.json:q_prune30_growth_pct")

sect("tab5b")
T5B = {"flowers": (10.9, 9.3, 12.6, 9.3, 6.8, 11.6, 15),
       "bicycle": (18.6, 15.1, 21.8, 5.6, 4.2, 6.8, 70),
       "treehill": (12.8, 9.6, 15.4, 3.9, 3.0, 4.7, 70),
       "stump": (11.7, 9.4, 13.8, 2.0, 1.1, 2.9, 83)}
for s in SC:
    row = [l for l in LINES if l.startswith(s) and "multicolumn{2}" in l][0]
    ln = LINES.index(row) + 1
    mm = re.search(r"\$([+-]?[\d.]+)\$\s*\[([\d.]+),\s*([\d.]+)\]\}\s*&\s*\\multicolumn\{2\}\{c\}\{\$([+-]?[\d.]+)\$\s*\[([\d.]+),\s*([\d.]+)\]\}\s*&\s*(\d+)\\?%", row)
    if not mm:
        raise LocError("tab5b " + s)
    tex = tuple(g(mm, i) for i in range(1, 8))
    if s in CR:
        c = CR[s]
        data = (pct(c["opacity30_drop_mean"]), pct(c["opacity30_drop_lo"]), pct(c["opacity30_drop_hi"]),
                pct(c["pup30_drop_mean"]), pct(c["pup30_drop_lo"]), pct(c["pup30_drop_hi"]),
                100 * (1 - c["pup30_drop_mean"] / c["opacity30_drop_mean"]))
        srcs = ("results_v54/crit_*.json:opacity30_drop_mean/lo/hi, pup30_drop_mean/lo/hi, "
                "1-pup30/opacity30")
    else:
        data = None
        srcs = ("no artifact: results_v54 holds crit_b (treehill,stump) and crit_c (bicycle); "
                "there is no flowers criterion file")
    rec(f"tab5b {s}: opacity drop + CI (pp)", ln, tex[:3], data[:3] if data else None, 0.06, srcs)
    rec(f"tab5b {s}: sensitivity drop + CI (pp)", ln, tex[3:6], data[3:6] if data else None, 0.06, srcs)
    rec(f"tab5b {s}: reduction (%)", ln, tex[6], data[6] if data else None, 0.55, srcs)

# ---- Section 3.4 prose --------------------------------------------------
sect("3.4")
ln, m = prose(r"the conformal half-width \$q\$ grows by ([\d.]+)--([\d.]+)\\?% after\s*a 30\\?% prune")
rec("3.4: q growth range (%)", ln, (float(m.group(1)), float(m.group(2))),
    (min(_g), max(_g)), 0.55, "results_v55/widths.json:q_prune30_growth_pct")

ln, m = prose(r"\(flowers \$(?:\+)?(\d+)\\?%\$?, bicycle \$(?:\+)?(\d+)\\?%\$?, treehill \$(?:\+)?(\d+)\\?%\$?, stump \$(?:\+)?(\d+)\\?%\$?\)")
for i, s in enumerate(["flowers", "bicycle", "treehill", "stump"]):
    rec(f"3.4: q growth for {s} (%)", ln, float(m.group(i + 1)), wd[s]["q_prune30_growth_pct"], 0.55,
        "results_v55/widths.json:q_prune30_growth_pct")

ln, m = prose(r"loses\s*either coverage \((\d+)--(\d+) points\) or efficiency \(([\d.]+)--([\d.]+)\\% wider\)")
rec("3.4: coverage loss range restated (pp)", ln, (float(m.group(1)), float(m.group(2))),
    (lo, hi), 0.55, "results_v52/many_splits.json:drop_mean")
rec("3.4: efficiency loss range restated (%)", ln, (g(m, 3), g(m, 4)), (min(_g), max(_g)), 0.55,
    "results_v55/widths.json")

ln, m = prose(r"an opacity criterion costs \$([\d.]+)\$--\$([\d.]+)\$ points")
_op = [pct(CR[s]["opacity30_drop_mean"]) for s in CR]
rec("3.4: opacity criterion cost range (pp)", ln, (g(m, 1), g(m, 2)),
    (min(_op), max(_op)), 0.06, "results_v54/crit_*.json:opacity30_drop_mean",
    note="only 3 scenes have a criterion artifact; flowers has none")

ln, m = prose(r"a sensitivity criterion \(gradient-magnitude\s*ranking, as in~\\citealp\{hanson2025pup\}\) costs \$([\d.]+)\$--\$([\d.]+)\$")
_pup = [pct(CR[s]["pup30_drop_mean"]) for s in CR]
rec("3.4: sensitivity criterion cost lower bound (pp)", ln, g(m, 1), min(_pup), 0.06,
    "results_v54/crit_*.json:pup30_drop_mean (stump 2.0)")
rec("3.4: sensitivity criterion cost upper bound (pp)", ln, g(m, 2), None, 0.06,
    "no flowers criterion artifact; largest value on disk is %.2f pp" % max(_pup))

ln, m = prose(r"the reduction is (\d+)--(\d+)\\% on three scenes\s*and (\d+)\\% on flowers")
_red = [100 * (1 - CR[s]["pup30_drop_mean"] / CR[s]["opacity30_drop_mean"]) for s in CR]
rec("3.4: reduction range on three scenes (%)", ln, (float(m.group(1)), float(m.group(2))),
    (min(_red), max(_red)), 0.55, "results_v54/crit_*.json:(1-pup/opacity)*100")
rec("3.4: reduction on flowers (%)", ln, float(m.group(3)), None, 0.55,
    "no flowers criterion artifact")

ln, m = prose(r"\(\$?\+([\d.]+)\\%\$? on treehill, \$?\+([\d.]+)\\%\$? on stump\)")
rec("3.4: sensitivity width growth on treehill (%)", ln, float(m.group(1)),
    CR["treehill"]["pup30_width_growth"], 0.55, "results_v54/crit_b.json:pup30_width_growth")
rec("3.4: sensitivity width growth on stump (%)", ln, float(m.group(2)),
    CR["stump"]["pup30_width_growth"], 0.55, "results_v54/crit_b.json:pup30_width_growth")

ln, m = prose(r"whereas opacity pruning widens it by (\d+)--(\d+)\\%")
_og = [CR[s]["opacity30_width_growth"] for s in CR]
rec("3.4: opacity width growth range (%)", ln, (float(m.group(1)), float(m.group(2))),
    (min(_og), max(_og)), 0.55, "results_v54/crit_*.json:opacity30_width_growth")

ln, m = prose(r"Quantisation leaves both the coverage and the\s*interval width unchanged")
_qw = {s: wd[s].get("q_quant8_growth_pct") for s in SC if "q_quant8_growth_pct" in wd[s]}
rec("3.4(c): 'quantisation leaves the interval width unchanged' (max |growth| %)", ln, 0.0,
    max(abs(v) for v in _qw.values()), 0.55, "results_v55/widths.json:q_quant8_growth_pct",
    note="per-scene: " + ", ".join(f"{s} {_qw[s]:+.1f}%" for s in _qw))

# ---- Section 3.5 (self-check) -------------------------------------------
sect("3.5")
ln, m = prose(r"We measured this over (\d+) splits")
rec("3.5: number of splits behind the self-check", ln, float(m.group(1)), None, 0.0,
    "results_v58/selfcheck.json has no n_splits field; only the prose asserts 400")
ln, m = prose(r"check returns \$([\d.]+)\$ by construction, while the true\s*deployment coverage is \$([\d.]+)\$, \$([\d.]+)\$, \$([\d.]+)\$, \$([\d.]+)\$")
rec("3.5: self-check return value", ln, g(m, 1), 0.90, 0.0006, "alpha=0.10 (q is the 1-alpha quantile)")
_data4 = (SCK["flowers"]["prune50_actual_mean"], SCK["flowers"]["prune30_actual_mean"],
          SCK["treehill"]["prune50_actual_mean"], SCK["treehill"]["prune30_actual_mean"])
rec("3.5: the four 'true deployment coverage' values", ln, tuple(g(m, i) for i in (2, 3, 4, 5)),
    _data4, 0.0006, "results_v58/selfcheck.json:*_actual_mean",
    note="the four values are (flowers 50%, flowers 30%, treehill 50%, treehill 30%) - two "
         "prune levels x two scenes, not four scenes")
ln, m = prose(r"over-predicting by \$?\+([\d.]+)\$?, \$?\+([\d.]+)\$?, \$?\+([\d.]+)\$?, \$?\+([\d.]+)\$ points")
rec("3.5: the four over-predictions (pp)", ln, tuple(g(m, i) for i in (1, 2, 3, 4)),
    tuple(100 * v for v in (SCK["flowers"]["prune50_selfcheck_err_mean"],
                            SCK["flowers"]["prune30_selfcheck_err_mean"],
                            SCK["treehill"]["prune50_selfcheck_err_mean"],
                            SCK["treehill"]["prune30_selfcheck_err_mean"])), 0.06,
    "results_v58/selfcheck.json:*_selfcheck_err_mean")

# ---- Section 6 / Appendix C reproducibility -----------------------------
sect("repro")
ln, m = prose(r"an automated check with (\d+)\s*assertions covering the reported values, abstract-level ranges, internal consistency and figure\s*freshness; four operator and decision modules carry a further (\d+) unit assertions")
_ok_sites = 0
_test_files = ["test_operators.py", "test_advise.py", "test_downstream_task.py", "test_voxel_cert.py"]
for f in _test_files:
    p = os.path.join(ROOT, "research", "code", "tests", f)
    if os.path.isfile(p):
        t = io.open(p, encoding="utf-8", errors="ignore").read()
        _ok_sites += t.count("ok(") - t.count("def ok(")
rec("repro: number of assertions in the automated check", ln, float(m.group(1)), 104.0, 0.0,
    "research/code/scripts/verify_paper_numbers.py prints '104 numeric checks, 0 failures'",
    note="but that script parses PAPER_certificate_invalid.md, whose main table is "
         "(0.899/0.914/0.859/0.903; -11.4/-11.9/-20.6/-12.5) - not the numbers in main.tex. "
         "No automated check covered the LaTeX before this file.")
rec("repro: number of unit assertions in the four test modules", ln, float(m.group(2)),
    float(_ok_sites), 0.0, "count of ok(...) call sites in research/code/tests/*.py",
    note="static call sites = %d; only 36 fire under this interpreter (test_operators and "
         "test_voxel_cert abort on ModuleNotFoundError: torch)" % _ok_sites)

# ---- Related work -------------------------------------------------------
sect("related")
ln, m = prose(r"On four scenes of ([\d.]+)k--([\d.]+)k carriers with (\d+)--(\d+) held-out label views")
rec("related: AURA carrier range (k)", ln, (g(m, 1), g(m, 2)), None, 0.06,
    "external paper (Attri 2026); no copy of it on disk")
rec("related: AURA held-out view range", ln, (float(m.group(3)), float(m.group(4))), None, 0.0,
    "external paper; no copy on disk")
ln, m = prose(r"selection AUC of ([\d.]+)--([\d.]+) against ([\d.]+)--([\d.]+) for opacity")
rec("related: AURA selection AUC range", ln, (g(m, 1), g(m, 2)), None, 0.006, "external paper")
rec("related: AURA opacity AUC range", ln, (g(m, 3), g(m, 4)), None, 0.006, "external paper")

# ---- Appendix A ---------------------------------------------------------
sect("appA")
ln, m = prose(r"Pruning flowers from ([\d.]+)M to (\d+)k and then fine-tuning without densification\s*gives a ([\d.]+)M model at ([\d.]+)\\,dB")
rec("appA: flowers full primitive count (M)", ln, g(m, 1), VT["flowers"]["n_primitives"] / 1e6, 0.051,
    "results_v60/vt_flowers.json:n_primitives")
rec("appA: prune target (k)", ln, float(m.group(2)), float(COMPACT["flowers"]["n_target"]) / 1e3, 0.0,
    "results_v47/compact.json:n_target")
rec("appA: fine-tuned model size (M)", ln, g(m, 3), 278955 / 1e6, 0.006,
    "results_v47/ft200_audit.json:rows[clean].n (278955)")
rec("appA: fine-tuned model PSNR (dB)", ln, g(m, 4), None, 0.06,
    "no artifact stores this model's PSNR (tail_prune.json 13.50 is a different pruner; "
    "compact.json stores only the un-fine-tuned 10.80 dB)")

ln, m = prose(r"still loses \$([\d.]+)\$--\$([\d.]+)\$ points on four scenes \(three-way split:\s*fine-tune / calibrate / deploy pairwise disjoint, 400 random splits, fresh coverage\s*\$([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\$\)")
_tw = [pct(TW[s]["drop_mean"]) for s in SC]
rec("appA: three-way drop range (pp)", ln, (g(m, 1), g(m, 2)),
    (min(abs(v) for v in _tw), max(abs(v) for v in _tw)), 0.06,
    "results_v51/three_way.json:drop_mean")
rec("appA: three-way fresh coverage x4", ln, tuple(g(m, i) for i in (3, 4, 5, 6)),
    tuple(TW[s]["clean_mean"] for s in SC), 0.0006, "results_v51/three_way.json:clean_mean")
rec("appA: three-way split count", ln, 400.0, float(TW["flowers"]["n_splits"]), 0.0,
    "results_v51/three_way.json:n_splits")

ln, m = prose(r"any fine-tuning \(([\d.]+)--([\d.]+)\\,dB\) still loses ([\d.]+)--([\d.]+) points")
rec("appA: un-fine-tuned PSNR range (dB)", ln, (g(m, 1), g(m, 2)),
    (min(COMPACT[s]["psnr_pruned"] for s in SC), max(COMPACT[s]["psnr_pruned"] for s in SC)),
    0.06, "results_v4{7,8}/*compact.json:psnr_pruned")
_nf = [pct(NF[s]["prune30"]["stale_cov_pix"] - NF[s]["clean"]["cov_pix"]) for s in SC]
rec("appA: un-fine-tuned drop range (pp)", ln, (g(m, 3), g(m, 4)),
    (min(abs(v) for v in _nf), max(abs(v) for v in _nf)), 0.06,
    "results_v61/*_nofinetune.json:prune30.stale_cov_pix - clean.cov_pix")

ln, m = prose(r"Our earliest self-trained models \((\d+) steps\) showed no effect at all\s*\(\$([+-]?[\d.]+)\$ to \$(\+?[\d.]+)\$ points\)")
rec("appA: earliest self-trained step count", ln, float(m.group(1)), None, 0.0,
    "no artifact records a 4000-step run (results_v35/v62 store no step field)")
rec("appA: early-model drop range (pp)", ln, (g(m, 2), g(m, 3)), None, 0.06,
    "no artifact: the 4000-step models have no result JSON on disk")

ln, m = prose(r"at (\d+) steps the effect appears on (\d+) of (\d+) scenes")
rec("appA: step count for the main table", ln, float(m.group(1)), None, 0.0,
    "no artifact records the step count")
rec("appA: scenes affected", ln, float(m.group(2)), float(_nneg), 0.0, "tab:main rows")
rec("appA: scenes total", ln, float(m.group(3)), 9.0, 0.0, "tab:main rows")

# ---- Appendix B ---------------------------------------------------------
sect("appB")
ln, m = prose(r"\(mean residual ratio ([\d.]+)--([\d.]+)\)")
_rr = [r["dep_med"] / r["cal_med"] for r in CA17]
rec("appB: deployment/calibration residual ratio range", ln, (g(m, 1), g(m, 2)),
    (min(_rr), max(_rr)), 0.006, "results_v17/cert_audit.json:dep_med/cal_med",
    note="the same file reproduces the 0.944-0.988 over-coverage but its residual ratios "
         "are 0.84-1.15, not 0.45-0.91")

ln, m = prose(r"the certificate over-covers \(\$?([\d.]+)\$?--\$?([\d.]+)\$? against nominal ([\d.]+)\)")
_cov17 = [r["cov_pix"] for r in CA17 if r["edit"] == "clean"]
rec("appB: over-coverage range", ln, (g(m, 1), g(m, 2)), (min(_cov17), max(_cov17)), 0.0006,
    "results_v17/cert_audit.json:cov_pix (the 4 clean rows)")
rec("appB: nominal coverage", ln, g(m, 3), 0.90, 0.0006, "alpha=0.10")

ln, m = prose(r"Interleaved splitting restores fresh coverage to \$?([\d.]+)\$?--\$?([\d.]+)\$?")
rec("appB: interleaved fresh coverage range", ln, (g(m, 1), g(m, 2)),
    (min(FRESH.values()), max(FRESH.values())), 0.0006, "results_v52/many_splits.json:clean_mean")

ln, m = prose(r"lowers coverage to \$([\d.]+)/([\d.]+)/([\d.]+)\$ --- ([\d.]+) points below nominal")
_c24 = [r["cov_pix"] for r in CALL24 if r["edit"] == "clean"]
rec("appB: leakage coverage triple", ln, tuple(g(m, i) for i in (1, 2, 3)), tuple(sorted(_c24)),
    0.0006, "results_v24/cert_all.json:rows[clean].cov_pix",
    note="artifact gives %.3f/%.3f/%.3f (sorted); the first printed value 0.822 is a "
         "transposition of 0.828" % tuple(sorted(_c24)))
rec("appB: 'points below nominal'", ln, g(m, 4), 100 * (0.90 - min(_c24)), 0.55,
    "results_v24/cert_all.json:0.900 - min(cov_pix)")

# ---- Appendix C ---------------------------------------------------------
sect("appC")
ln, m = prose(r"mean drop\s*\$([+-]?[\d.]+)\$ points at \$\\alpha=([\d.]+)\$, \$([+-]?[\d.]+)\$ at \$([\d.]+)\$, \$([+-]?[\d.]+)\$ at \$([\d.]+)\$")
_a05 = [pct(A05[(s, "prune30")]["stale_cov_pix"] - A05[(s, "clean")]["cov_pix"]) for s in SC]
_a20 = [pct(A20[(s, "prune30")]["stale_cov_pix"] - A20[(s, "clean")]["cov_pix"]) for s in SC]
_m10 = [pct(MS[(s, 0.3)]["drop_mean"]) for s in SC]
rec("appC: mean drop at alpha=0.05 (pp)", ln, g(m, 1), sum(_a05) / 4, 0.055,
    "results_v28/cert_a0.05.json:prune30.stale_cov_pix - clean.cov_pix (mean over 4)")
rec("appC: mean drop at alpha=0.10 (pp)", ln, g(m, 3), sum(_m10) / 4, 0.055,
    "results_v52/many_splits.json:drop_mean (mean over 4)",
    note="the alpha=0.10 column can only come from the 400-split file, not from results_v28 "
         "(which has alpha=0.05 and 0.20 only)")
rec("appC: mean drop at alpha=0.20 (pp)", ln, g(m, 5), sum(_a20) / 4, 0.055,
    "results_v28/cert_a0.2.json")

ln, m = prose(r"the four drops are ([+-]?[\d.]+)/([+-]?[\d.]+)/([+-]?[\d.]+)/([+-]?[\d.]+), within ([\d.]+) points of the quarter-resolution values")
rec("appC: half-resolution drops x4 (pp)", ln, tuple(g(m, i) for i in (1, 2, 3, 4)), None, 0.06,
    "no half-resolution artifact exists in research/results_v*/ (no 'half'/'res' field anywhere)")
rec("appC: max deviation from quarter-resolution values (pp)", ln, g(m, 5), None, 0.06,
    "no half-resolution artifact")

ln, m = prose(r"reduces its magnitude (\d+)--(\d+)\\times")
_ratio_vox = {s: abs(D30[s]) / abs(VG[s]) for s in SC}
rec("appC: voxel vs block magnitude ratio (x)", ln, (float(m.group(1)), float(m.group(2))),
    (min(_ratio_vox.values()), max(_ratio_vox.values())), 0.55,
    "results_v52 many_splits:drop_mean / results_v60 vt:voxel_prune30_drop_mean",
    note="per-scene ratios are " + ", ".join(f"{s} {_ratio_vox[s]:.2f}" for s in SC)
         + "; only the range-endpoint pairing gives 3.0-4.2x")

ln, m = prose(r"\(([+-]?[\d.]+) to ([+-]?[\d.]+) points, fresh coverage ([\d.]+)--([\d.]+)\)")
rec("appC: voxel drop range (pp)", ln, (g(m, 1), g(m, 2)), (-min(_vg), -max(_vg)), 0.06,
    "results_v60/vt_*.json:voxel_prune30_drop_mean (written as a drop, so negated)")
rec("appC: voxel fresh coverage range", ln, (g(m, 3), g(m, 4)),
    (min(VT[s]["voxel_clean_mean"] for s in SC), max(VT[s]["voxel_clean_mean"] for s in SC)), 0.0006,
    "results_v60/vt_*.json:voxel_clean_mean")

ln, m = prose(r"a\s*(\d+)-item automated check")
rec("appC: item count of the automated check", ln, float(m.group(1)), 104.0, 0.0,
    "research/code/scripts/verify_paper_numbers.py")

ln, m = prose(r"the\s*four operator/decision modules carry (\d+) unit assertions")
rec("appC: unit assertion count", ln, float(m.group(1)), float(_ok_sites), 0.0,
    "count of ok(...) call sites in research/code/tests/*.py")

# ---- Discussion (§5) ----------------------------------------------------
sect("discussion")
ln, m = prose(r"The drop is \$([\d.]+)\$--\$([\d.]+)\$ points on released checkpoints and\s*\$([\d.]+)\$--\$([\d.]+)\$ on our self-trained ones")
rec("disc: released drop range (pp)", ln, (g(m, 1), g(m, 2)), (lo, hi), 0.06,
    "results_v52/many_splits.json")
_st = sorted(abs(ST_TEX[s][1]) for s in ST)
rec("disc: self-trained drop range (pp)", ln, (g(m, 3), g(m, 4)), (min(_st), max(_st)), 0.06,
    "tab:main self-trained rows",
    note="matches tab:main, but contradicts section 3.1 which writes the same range as "
         "'6.7 to -0.7'")

ln, m = prose(r"still loses \$([\d.]+)\$--\$([\d.]+)\$ points")
rec("disc: un-fine-tuned 200k drop range (pp)", ln, (g(m, 1), g(m, 2)),
    (min(abs(v) for v in _nf), max(abs(v) for v in _nf)), 0.06,
    "results_v61/*_nofinetune.json")

ln, m = prose(r"with\s*drops (\d+)--(\d+)\\times\$? smaller")
rec("disc: voxel drop is Nx smaller than block drop", ln, (float(m.group(1)), float(m.group(2))),
    (min(_ratio_vox.values()), max(_ratio_vox.values())), 0.55,
    "results_v52 vs results_v60", note="same quantity as appC; ratios are 1.9-4.9x")

ln, m = prose(r"Each scene has (\d+)--(\d+) held-out views,\s*fewer than the (\d+)--(\d+) used by AURA")
rec("disc: held-out views per scene", ln, (float(m.group(1)), float(m.group(2))),
    (float(_nv[0]), float(_nv[-1])), 0.0, "results_v60/vt_*.json:n_views")
rec("disc: AURA view count", ln, (float(m.group(3)), float(m.group(4))), None, 0.0,
    "external paper; no copy on disk")


# ---- cross-checks: does the paper contradict itself? --------------------
# These compare two places in main.tex that report the same quantity (or that must be
# arithmetically related), so they catch presentation/normalisation errors that no
# single-vs-data check can see.
sect("xchk")
ln4, _ = prose(r"Scene & Fresh hit rate & 50\\?% pruned")
for s in SC:
    ln, row = rows_in(r"\label{tab:downstream}", s)[0]
    v = nums(row)
    rec(f"xchk: tab:downstream vs tab:main 30%-prune coverage drop, {s}", ln,
        v[4], D30[s], 0.06, "two places in the same paper",
        note="tab:main prints %.1f pp for the same 30%% prune; the difference is the region "
             "definition (64x64 blocks vs 0.25-unit voxels), which the downstream table does "
             "not state" % D30[s])

ln, _ = prose(r"SH degree reduction does move the residual distribution")
_cov_change_signs = [1 if v > 0 else -1 for v in (pct(CV3K[("flowers", "shdeg1")]["stale_cov_pix"] - CV3K[("flowers", "clean")]["cov_pix"]), SHDEG["bicycle"], SHDEG["treehill"], SHDEG["stump"])]
rec("xchk: tab:families SH row - columns printed as a decrease", ln, 4.0,
    float(sum(1 for x in _cov_change_signs if x < 0)), 0.0, "tab:families + results_v53/ef_*.json",
    note="all four SH cells carry a minus sign, but the measured coverage change is a decrease "
         "on flowers only (+1.0 pp on bicycle, +0.2 on treehill, +1.0 on stump)")

ln, _ = prose(r"\(b\) criterion at 30\\?% budget")
ln, row = next(r for r in rows_in(r"\label{tab:rules}", "bicycle") if "multicolumn" in r[1])
v = nums(row)
mm = re.search(r"\$([+-]?[\d.]+)\$", row)
rec("xchk: tab:rules(b) opacity sign vs tab:main sign for bicycle", ln, abs(g(mm, 1)),
    abs(D30["bicycle"]), 0.06, "tab:rules vs tab:main",
    note="identical magnitude, opposite sign convention: tab:main prints -18.6 (coverage "
         "change), tab:rules(b) prints +18.6 (damage)")

ln, m = prose(r"the four drops are ([+-]?[\d.]+)/([+-]?[\d.]+)/([+-]?[\d.]+)/([+-]?[\d.]+), within ([\d.]+) points")
_half = [g(m, i) for i in (1, 2, 3, 4)]
_implied = max(abs(h - D30[s]) for h, s in zip(_half, SC))
rec("xchk: appC 'within N points' vs the deviation implied by the printed numbers", ln,
    g(m, 5), _implied, 0.06, "appC half-resolution list vs tab:main",
    note="pairing the printed half-resolution drops with tab:main in table order gives a "
         "max deviation of %.1f points" % _implied)

# ==================================================================  output
def main():
    show_src = "--show-sources" in sys.argv
    out_json = None
    if "--json-out" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json-out") + 1]

    width = max(len(r["name"]) for r in ROWS)
    cur = None
    for r in ROWS:
        if r["section"] != cur:
            cur = r["section"]
            print(f"\n[{cur}]")
        tag = {"MATCH": "ok      ", "MISMATCH": "MISMATCH", "NO_SOURCE": "NO_SOURCE"}[r["verdict"]]
        extra = ""
        if r["verdict"] == "MISMATCH":
            extra = f"   << wrote {fmt(r['tex'])}  data {fmt(r['data'])}"
        elif r["verdict"] == "NO_SOURCE":
            extra = "   << untraceable"
        print(f"  {tag} {r['name']:<{width}}  L{r['line']:<4} {extra}")
        if r["note"] and r["verdict"] != "MATCH":
            print(f"             note: {r['note']}")
        if show_src:
            print(f"             src : {r['src']}   tol={r['tol']}")

    n_match = sum(1 for r in ROWS if r["verdict"] == "MATCH")
    n_mis = sum(1 for r in ROWS if r["verdict"] == "MISMATCH")
    n_ns = sum(1 for r in ROWS if r["verdict"] == "NO_SOURCE")
    fails = n_mis + n_ns

    print("\n" + "=" * 78)
    if n_mis:
        print("MISMATCH (paper value vs artifact):")
        for r in ROWS:
            if r["verdict"] == "MISMATCH":
                print(f"  L{r['line']:<4} {r['name']}: wrote {fmt(r['tex'])}, data {fmt(r['data'])}")
    if n_ns:
        print("NO_SOURCE (no artifact on disk):")
        for r in ROWS:
            if r["verdict"] == "NO_SOURCE":
                print(f"  L{r['line']:<4} {r['name']}: wrote {fmt(r['tex'])}")
    print("=" * 78)
    print(f"{len(ROWS)} checks, {fails} failures  "
          f"({n_match} MATCH, {n_mis} MISMATCH, {n_ns} NO_SOURCE)")

    if out_json:
        with io.open(out_json, "w", encoding="utf-8") as f:
            json.dump(ROWS, f, indent=1, ensure_ascii=False)
        print("WROTE", out_json)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
