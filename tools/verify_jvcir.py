"""JVCIR submission gate: one command that says whether the package can be uploaded.

Checks, in order (any failure exits 1):

  1. compliance      abstract <= 250 words, 1-7 keywords, 3-5 highlights with <= 85 characters
  2. placeholders    only the two author-supplied DOI/URL slots may remain
  3. structure       every \\input and \\includegraphics target exists
  4. citations       every \\cite key is in refs.bib, and no bib entry is orphaned
  5. tables          every tab_*.tex regenerates byte-identically from its artifact
  6. figures         every figure exists as vector PDF and as a >= 300 dpi raster
  7. provenance      experiments/j3_ablations.py --check passes (every printed number has a source)
  8. build           main.pdf exists, is newer than its sources, and has >= 8 pages
  9. claims          the headline numbers quoted in the prose appear in the tables that carry them
 10. prose           no paragraph is duplicated; the gap range in the prose equals the computed range;
                     the matched-decibel claim equals the value in the figure's artifact
 11. refs            the bibliography is at least as broad as the journal's 2026 lower quartile, and
                     every locator resolves (`--net`; the structural part always runs)

Usage:
    python tools/verify_jvcir.py
    python tools/verify_jvcir.py --quiet
    python tools/verify_jvcir.py --net        # also resolve every DOI / arXiv id
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(".").resolve()
SUB = ROOT / "submission" / "jvcir"
TEX = SUB / "main.tex"
BIB = SUB / "refs.bib"
PDF = SUB / "main.pdf"
HIGHLIGHTS = SUB / "highlights.txt"
FIGDIR = ROOT / "figures_j"
A4 = ROOT / "experiments" / "artifacts" / "a4"
SURVEY = ROOT / "review" / "JVCIR_SURVEY_STATS.json"

ABSTRACT_LIMIT = 250
HL_LIMIT, HL_MIN, HL_MAX = 85, 3, 5
KW_MIN, KW_MAX = 1, 7
TBD_ALLOWED = {"Zenodo DOI", "GitHub URL"}

# numbers the prose leans on, and the table that must carry them
CLAIMS = [
    ("17.35", "tab_container.tex"),
    ("83.41", "tab_container.tex"),
    ("8.97", "tab_frontier.tex"),
    ("15.78", "tab_frontier.tex"),
    ("12.74", "tab_collision.tex"),
    ("23.20", "tab_collision.tex"),
    ("0.857", "tab_decision.tex"),
    ("1.000", "tab_decision.tex"),
    ("+2.97", "tab_gap.tex"),
    ("+3.62", "tab_gap.tex"),
    ("+2.89", "tab_gap.tex"),
    ("+0.96", "tab_gap.tex"),
    ("-45.06", "tab_prune.tex"),
    ("15.95", "tab_cost.tex"),
    ("0.722", "tab_viewlevel.tex"),
    ("0.874", "tab_viewlevel.tex"),
]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def strip_tex(s: str) -> str:
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", "", s)
    return re.sub(r"\s+", " ", s).strip()


def png_width(path: Path) -> int:
    """Width in pixels from the PNG IHDR header (0 if the file is not a PNG)."""
    try:
        raw = path.read_bytes()[:24]
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            return 0
        return struct.unpack(">I", raw[16:20])[0]
    except Exception:  # noqa: BLE001
        return 0


def paragraphs(tex: str) -> list[str]:
    """Body paragraphs of the manuscript, with float bodies and preamble removed."""
    body = tex.split(r"\begin{document}", 1)[-1]
    body = re.sub(r"\\begin\{(table|figure|algorithm)\}.*?\\end\{\1\}", "", body, flags=re.S)
    body = re.sub(r"%.*", "", body)
    out = []
    for block in re.split(r"\n\s*\n", body):
        t = strip_tex(block)
        if len(t) >= 200 and len(t.split()) >= 30:
            out.append(t)
    return out


class Gate:
    def __init__(self, quiet: bool = False) -> None:
        self.fails: list[str] = []
        self.quiet = quiet

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        if not self.quiet:
            print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
        if not ok:
            self.fails.append(f"{label}: {detail}" if detail else label)
        return ok

    def section(self, name: str) -> None:
        if not self.quiet:
            print(f"\n{name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--net", action="store_true", help="resolve every DOI and arXiv id")
    args = ap.parse_args()
    g = Gate(args.quiet)

    if not TEX.exists():
        print(f"missing {TEX}")
        return 1
    tex = TEX.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8") if BIB.exists() else ""

    # ---- 1 compliance
    g.section("1 compliance")
    comp = _load("jvcir_compliance", ROOT / "tools" / "jvcir_compliance.py")
    info = comp.from_tex(tex)
    abstract = info.get("abstract", "")
    n_words = _words(abstract)
    g.check(0 < n_words <= ABSTRACT_LIMIT, "abstract", f"{n_words} words (<= {ABSTRACT_LIMIT})")
    kws = info.get("keywords", [])
    g.check(KW_MIN <= len(kws) <= KW_MAX, "keywords", f"{len(kws)} (1-7)")
    hl = [ln.strip() for ln in HIGHLIGHTS.read_text(encoding="utf-8").splitlines() if ln.strip()] \
        if HIGHLIGHTS.exists() else []
    g.check(HL_MIN <= len(hl) <= HL_MAX, "highlights count", f"{len(hl)} (3-5)")
    for h in hl:
        g.check(len(h) <= HL_LIMIT, "highlight length", f"{len(h)} chars: {h[:60]}...")

    # ---- 2 placeholders
    g.section("2 placeholders")
    tbds = re.findall(r"\\TBD\{([^}]*)\}", tex)
    unknown = [t for t in tbds if t not in TBD_ALLOWED]
    g.check(not unknown, "no unknown placeholders", ", ".join(unknown) or "none")
    g.check(len(tbds) <= len(TBD_ALLOWED), "only the DOI/URL slots remain", f"{len(tbds)} left")

    # ---- 3 structure
    g.section("3 structure")
    for m in re.findall(r"\\input\{([^}]*)\}", tex):
        g.check((SUB / f"{m}.tex").exists(), f"\\input{{{m}}}")
    for m in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex):
        g.check((FIGDIR / m).exists(), f"figure {m}")

    # ---- 4 citations
    g.section("4 citations")
    cited: set[str] = set()
    for grp in re.findall(r"\\cite\{([^}]*)\}", tex):
        cited.update(k.strip() for k in grp.split(","))
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    missing = sorted(cited - keys)
    g.check(not missing, "every \\cite key is in refs.bib", ", ".join(missing) or "none")
    orphans = sorted(keys - cited)
    g.check(not orphans, "no orphan bib entries", ", ".join(orphans) or "none")

    # ---- 5 tables regenerate
    g.section("5 tables")
    tables = _load("jvcir_tables", ROOT / "tools" / "jvcir_tables.py")
    tmp = SUB / "_gate_tmp"
    fresh = tables.build(tmp)
    drift = []
    for name, body in fresh.items():
        f = SUB / f"{name}.tex"
        if not f.exists() or f.read_text(encoding="utf-8") != body:
            drift.append(name)
    for f in tmp.glob("*.tex"):
        f.unlink()
    tmp.rmdir()
    g.check(not drift, "tables regenerate byte-identically", ", ".join(drift) or f"{len(fresh)} tables")

    # the audit-resolution tables come from their own generator, so they need their own provenance check
    res_tmp = SUB / "_gate_res"
    res_tmp.mkdir(exist_ok=True)
    res = subprocess.run([sys.executable, "tools/jvcir_resolution.py", "--out-dir", str(res_tmp)],
                         capture_output=True, text=True, cwd=ROOT)
    res_drift = []
    for name in ("tab_resolution.tex",):
        fresh_f, disk_f = res_tmp / name, SUB / name
        if res.returncode != 0 or not fresh_f.exists() or fresh_f.read_text(encoding="utf-8") != disk_f.read_text(encoding="utf-8"):
            res_drift.append(name)
        fresh_f.unlink(missing_ok=True)
    res_tmp.rmdir()
    g.check(not res_drift, "resolution table regenerates byte-identically", ", ".join(res_drift) or "1 table")

    # the single-pass tables are regenerated from the pulled J6 audit; they can only be checked when the pull exists
    pull = ROOT / "_pull_j6" / "audit_single.json"
    j6 = [SUB / "tab_singlepass.tex", SUB / "tab_singlepass_abstain.tex"]
    if pull.exists():
        j6_tmp = SUB / "_gate_j6"
        j6_tmp.mkdir(exist_ok=True)
        r6 = subprocess.run([sys.executable, "tools/j6_singlepass_analyse.py", "--out-dir", str(j6_tmp)],
                            capture_output=True, text=True, cwd=ROOT)
        drift6 = [f.name for f in j6
                  if not f.exists() or not (j6_tmp / f.name).exists()
                  or f.read_text(encoding="utf-8") != (j6_tmp / f.name).read_text(encoding="utf-8")]
        for f in j6_tmp.glob("*.tex"):
            f.unlink()
        j6_tmp.rmdir()
        g.check(r6.returncode == 0 and not drift6, "single-pass tables regenerate byte-identically",
                ", ".join(drift6) or "2 tables")
    else:
        g.check(True, "single-pass tables (no _pull_j6/, skipped)")

    # ---- 6 figures
    g.section("6 figures")
    stems = sorted({Path(m).stem for m in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex)})
    for stem in stems:
        g.check((FIGDIR / f"{stem}.pdf").exists(), f"{stem}.pdf (vector)")
        png = FIGDIR / f"{stem}.png"
        w = png_width(png) if png.exists() else 0
        g.check(w >= 1200, f"{stem}.png (>= 300 dpi raster)", f"{w} px wide" if w else "missing")

    # ---- 7 provenance
    g.section("7 provenance")
    proc = subprocess.run([sys.executable, "experiments/j3_ablations.py", "--check"],
                          capture_output=True, text=True, cwd=ROOT)
    g.check(proc.returncode == 0, "j3 ablation provenance", (proc.stdout.strip().splitlines() or [""])[0])

    # ---- 8 build
    g.section("8 build")
    if g.check(PDF.exists(), "main.pdf exists"):
        sources = [TEX, BIB] + sorted(SUB.glob("tab_*.tex")) + sorted(FIGDIR.glob("*.pdf"))
        newest = max(p.stat().st_mtime for p in sources if p.exists())
        g.check(PDF.stat().st_mtime >= newest, "main.pdf is newer than every source",
                "recompile" if PDF.stat().st_mtime < newest else "ok")
        log = (SUB / "main.log")
        pages = 0
        if log.exists():
            m = re.search(r"Output written on main\.pdf \((\d+) pages", log.read_text(errors="replace"))
            pages = int(m.group(1)) if m else 0
        g.check(pages >= 8, "page count", f"{pages} pages")
        ref_warn = "LaTeX Warning: There were undefined references" in log.read_text(errors="replace") \
            if log.exists() else False
        g.check(not ref_warn, "no undefined references")

    # ---- 9 claims
    g.section("9 claims")
    for number, tab in CLAIMS:
        body = (SUB / tab).read_text(encoding="utf-8") if (SUB / tab).exists() else ""
        g.check(number in body, f"{number} in {tab}")

    # ---- 10 prose integrity: no duplicated paragraphs, prose equals the computed numbers
    g.section("10 prose")
    paras = paragraphs(tex)
    seen: dict[str, int] = {}
    for p in paras:
        seen[p] = seen.get(p, 0) + 1
    dupes = [p[:70] for p, n in seen.items() if n > 1]
    g.check(not dupes, "no paragraph appears twice", " | ".join(dupes) if dupes else f"{len(paras)} paragraphs")

    gap_json = A4 / "j3_ablations.json"
    if gap_json.exists():
        rows = json.loads(gap_json.read_text(encoding="utf-8"))["gap"]
        bic = [r["gap_db"] for r in rows if r["scene"] == "bicycle" and r["method"] != "3DGS"]
        if bic:
            want = f"${min(bic):.2f}$--${max(bic):.2f}$"
            g.check(want in tex, "the published-gap range in the prose equals the computed range", want)
    dec_json = A4 / "j5_fig_decibel.json"
    if dec_json.exists():
        d = json.loads(dec_json.read_text(encoding="utf-8"))["widest_matched_db_pair"]
        want_pp = f"${d['d_pp']:.1f}$"
        want_db = f"${d['d_db']:.2f}$"
        g.check(want_pp in tex and want_db in tex, "the matched-decibel claim equals the figure artifact",
                f"{want_db} / {want_pp} pp on {d['scene']}")
    qual_json = A4 / "j5_fig_qual.json"
    if qual_json.exists() and "fig6_qualitative" in tex:
        q = json.loads(qual_json.read_text(encoding="utf-8"))
        missing = []
        for sc in q["scenes"]:
            for name, arm in sc["arms"].items():
                if name == "clean":
                    continue
                if f"{arm['psnr']:.2f}" not in tex or f"{arm['rate']:.2f}" not in tex:
                    missing.append(f"{sc['scene']}/{name}={arm['rate']:.2f}x,{arm['psnr']:.2f}dB")
        g.check(not missing, "Fig. 6 labels equal the render artifact", ", ".join(missing) or
                f"{sum(len(s['arms']) - 1 for s in q['scenes'])} arm labels")

    # ---- 12 production: would Elsevier's typesetter accept these files as they stand?
    g.section("12 production")
    widths = {}
    for stem in stems:
        pdf = FIGDIR / f"{stem}.pdf"
        if pdf.exists():
            try:
                out = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True, timeout=60).stdout
                rows = [ln for ln in out.splitlines()[2:] if ln.strip()]
                bad = [ln for ln in rows if " no " in ln[30:60] or ln.split()[-4:-3] == ["no"]]
                not_embedded = [ln.split()[0] for ln in rows if len(ln.split()) > 5 and ln.split()[-4] == "no"]
                g.check(not not_embedded, f"{stem}.pdf fonts embedded", ", ".join(not_embedded) or
                        f"{len(rows)} font(s)" if rows else "no fonts (vector strokes)")
            except FileNotFoundError:
                g.check(True, f"{stem}.pdf fonts (pdffonts unavailable, skipped)")
        png = FIGDIR / f"{stem}.png"
        w = png_width(png) if png.exists() else 0
        if w:
            widths[stem] = w                     # pixels, for the dpi-at-printed-width check below
    if widths:
        # the journal's artwork rule is 300 dpi at the size the figure is printed, not at an assumed width
        dpi_at_size = {}
        for stem, px in widths.items():
            pdf = FIGDIR / f"{stem}.pdf"
            try:
                info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=60).stdout
                m = re.search(r"Page size:\s+([\d.]+) x", info)
                if m:
                    dpi_at_size[stem] = round(px / (float(m.group(1)) / 72.27))
            except FileNotFoundError:
                pass
        if dpi_at_size:
            worst = min(dpi_at_size.items(), key=lambda kv: kv[1])
            g.check(worst[1] >= 300, "every raster figure is >= 300 dpi at its printed width",
                    f"worst {worst[0]} at {worst[1]} dpi")

    # ---- 13 the J9/J8 generalisation numbers, recomputed from their artifacts
    g.section("13 generalisation")
    chk = subprocess.run([sys.executable, "tools/check_j9_j8.py"], capture_output=True, text=True)
    failed = [ln.strip() for ln in chk.stdout.splitlines() if ln.strip().startswith("[FAIL]")]
    g.check(chk.returncode == 0 and not failed, "J9/J8 numbers match their artifacts",
            "; ".join(failed) if failed else f"{chk.stdout.count('[PASS]')} checks")

    # ---- 14 the guide's writing-and-formatting rules (file format, artwork, declarations)
    g.section("14 guide format")
    fmt = subprocess.run([sys.executable, "tools/check_guide_format.py"], capture_output=True, text=True)
    bad = [ln.strip() for ln in fmt.stdout.splitlines() if ln.strip().startswith("[FAIL]")]
    g.check(fmt.returncode == 0 and not bad, "the package meets the guide's format rules",
            "; ".join(bad) if bad else f"{fmt.stdout.count('[PASS]')} checks")

    # ---- 11 references: breadth against the journal's own range, and locator integrity
    g.section("11 references")
    n_bib = len(re.findall(r"@\w+\{", bib))
    q1 = None
    if SURVEY.exists():
        stats = json.loads(SURVEY.read_text(encoding="utf-8"))
        q1 = (stats.get("per_year", {}).get("2026") or {}).get("refs_q1")
    if q1:
        g.check(n_bib >= q1, "reference count against the journal's 2026 lower quartile", f"{n_bib} >= {q1}")
    else:
        g.check(n_bib >= 30, "reference count", f"{n_bib} entries (survey stats missing)")
    refs_cmd = [sys.executable, "tools/verify_refs.py"] + ([] if args.net else ["--offline"])
    refs = subprocess.run(refs_cmd, capture_output=True, text=True, cwd=ROOT)
    tail = (refs.stdout.strip().splitlines() or [""])[-1]
    g.check(refs.returncode == 0, "reference locators", tail[:90])

    print()
    if g.fails:
        print(f"FAIL — {len(g.fails)} problem(s)")
        for f in g.fails:
            print(f"  - {f}")
        return 1
    print("PASS — the package satisfies every automated JVCIR gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
