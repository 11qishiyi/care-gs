"""Build the JVCIR deposit bundle (Option C): code, data, tables, figures, provenance.

Deterministic: files are sorted and every entry gets the same fixed timestamp, so re-running the
script on unchanged inputs produces a byte-identical archive.

    python tools/make_deposit_jvcir.py
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(".")
OUT = Path("submission/jvcir/deposit_jvcir.zip")
STAMP = (2026, 11, 18, 0, 0, 0)

CODE = [
    "experiments/j1_reliability.py",
    "experiments/j2_audit_decision.py",
    "experiments/j3_ablations.py",
    "tools/jvcir_tables.py",
    "tools/verify_jvcir.py",
    "tools/jvcir_compliance.py",
    "tools/jvcir_fig_framework.py",
    "tools/jvcir_fig_frontier.py",
    "tools/jvcir_fig_viewlevel.py",
    "tools/jvcir_fig_audit.py",
    "tools/jvcir_fig_decibel.py",
    "tools/jvcir_fig_graphical.py",
    "tools/verify_refs.py",
    "tools/jvcir_fig_qual.py",
    "tools/jvcir_resolution.py",
    "tools/j6_singlepass_analyse.py",
    "tools/j6_sigma_sensitivity.py",
    "experiments/casget.sh",
    "experiments/j6_cas_fetch.sh",
    "experiments/j6_fix_data.sh",
    "experiments/j6_finish3.sh",
    "experiments/j5_render.py",
    "experiments/j5_pack.py",
    "experiments/j5_fetch_all.sh",
    "experiments/j5_fix_images2.sh",
    "tools/jvcir_survey.py",
    "experiments/j4_analyse.py",
    "experiments/j4_report.py",
    "experiments/j4_sweep.sh",
    "experiments/j4_go.sh",
    "tools/make_deposit_jvcir.py",
]
DATA = [
    "experiments/artifacts/a4/j1_reliability.json",
    "experiments/artifacts/a4/j1_reliability.md",
    "experiments/artifacts/a4/j2_audit_decision.json",
    "experiments/artifacts/a4/j2_audit_decision.md",
    "experiments/artifacts/a4/j3_ablations.json",
    "experiments/artifacts/a4/j3_ablations.md",
    "experiments/artifacts/a4/m5_rd_v2.json",
    "experiments/artifacts/a4/m24_encode_streams.txt",
    "experiments/artifacts/a4/sota_table.md",
    "results_v120/audit_bound_nobonsai.json",
    "experiments/J1_RESULTS.md",
    "experiments/J4_RESULTS.md",
    "experiments/J4_PLAN.md",
    "experiments/artifacts/a4/j4_report.json",
    "experiments/artifacts/a4/j4_report.md",
    "experiments/artifacts/a4/j5_fig_audit.json",
    "experiments/artifacts/a4/j5_fig_decibel.json",
    "experiments/artifacts/a4/j5_fig_qual.json",
    "experiments/artifacts/a4/j5_resolution.json",
    "experiments/artifacts/a4/j6_singlepass.json",
    "experiments/artifacts/a4/j6_sigma_sensitivity.json",
    "_pull_j6/audit_single.json",
    "_pull_j5/j5_pack.json",
    "_pull_j5/bicycle_gt_patch.png",
    "_pull_j5/bicycle_clean.png", "_pull_j5/bicycle_gp6-6-6_c8_sh6.png",
    "_pull_j5/bicycle_gp6-6-6_c8_sh3.png", "_pull_j5/bicycle_p50.png",
    "_pull_j5/bicycle_full.jpg",
    "_pull_j4/j4_coverage.json",
    "_pull_j4/m1_manifest.json",
    "experiments/PAPER_NUMBERS.md",
    "experiments/published_3dgs.json",
]
TABLES = sorted(str(p) for p in Path("submission/jvcir").glob("tab_*.tex"))
FIGURES = ["figures_j/fig1_framework.pdf", "figures_j/fig1_framework.png",
           "figures_j/fig2_frontier.pdf", "figures_j/fig2_frontier.png",
           "figures_j/fig5_viewlevel.pdf", "figures_j/fig5_viewlevel.png",
           "figures_j/fig3_audit.pdf", "figures_j/fig3_audit.png",
           "figures_j/fig4_decibel.pdf", "figures_j/fig4_decibel.png",
           "figures_j/graphical_abstract.pdf", "figures_j/graphical_abstract.png",
           "figures_j/fig6_qualitative.pdf", "figures_j/fig6_qualitative.png"]
DOCS = ["submission/jvcir/main.tex", "submission/jvcir/refs.bib", "submission/jvcir/highlights.txt",
        "submission/jvcir/README.md", "submission/jvcir/CHECKLIST.md", "submission/jvcir/COVER_LETTER.md",
        "submission/jvcir/REBUTTAL_FAQ.md", "review/CARE_GS_GAP_2026-11-18.md",
        "review/JVCIR_BEST_PRACTICE_2026-11-18.md", "review/JVCIR_SURVEY_2026-11.md",
        "review/REFS_VERIFY.json", "experiments/J5_PLAN.md", "experiments/J5_RESULTS.md",
        "experiments/J6_RESULTS.md"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> None:
    entries: dict[str, Path] = {}
    for group, files in (("code", CODE), ("data", DATA), ("tables", TABLES),
                         ("figures", FIGURES), ("docs", DOCS)):
        for f in files:
            p = ROOT / f
            if not p.exists():
                print(f"  !! missing {f}")
                continue
            entries[f"{group}/{p.name}"] = p

    prov = {
        "bundle": "CARE-GS (JVCIR submission) deposit",
        "built": "2026-11-18",
        "note": "numbers in the manuscript are regenerated from data/ by code/ and checked by "
                "code/verify_jvcir.py; each entry below carries a content hash",
        "files": {k: {"sha256_16": sha(v), "bytes": v.stat().st_size} for k, v in sorted(entries.items())},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, entries[name].read_bytes())
        info = zipfile.ZipInfo("PROVENANCE.json", date_time=STAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, json.dumps(prov, indent=2, ensure_ascii=False) + "\n")

    print(f"wrote {OUT} ({OUT.stat().st_size:,} B, {len(entries) + 1} entries)")
    for k in sorted(entries):
        print(f"  {k:52s} {entries[k].stat().st_size:>9,} B")


if __name__ == "__main__":
    main()


