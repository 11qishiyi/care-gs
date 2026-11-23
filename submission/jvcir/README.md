# JVCIR submission package — map and reproduction

**Rebuilt 2026-11-18 (rounds 2–3). `python tools/verify_jvcir.py` → PASS (exit 0), 22 pages, 6 figures, 15 tables,
48 references, 11 gate sections.**

The survey this package is built against: [`review/JVCIR_BEST_PRACTICE_2026-11-18.md`](../../review/JVCIR_BEST_PRACTICE_2026-11-18.md)
(what the journal actually publishes, measured on 514 articles from 2025–2026, plus eight full-text deep reads),
and the reproducible corpus statistics in [`review/JVCIR_SURVEY_2026-11.md`](../../review/JVCIR_SURVEY_2026-11.md)
(`python tools/jvcir_survey.py`).

| file | what it is | how it is produced |
|---|---|---|
| `main.tex` | manuscript (elsarticle, `preprint,number,3p`), 22 pages | hand-written; tables and figures `\input`/`\includegraphics` |
| `main.pdf` | compiled manuscript | `pdflatex → bibtex → pdflatex ×2` |
| `refs.bib` | 48 entries: 3DGS + compression, 2026 certificate work, 14 from this journal, statistics | locators only where verified; `python tools/verify_refs.py` resolves every one |
| `highlights.txt` | 5 bullets, all ≤ 85 characters | `tools/jvcir_compliance.py` checks |
| `tab_container.tex` | container ladder (A0–A6) | `tools/jvcir_tables.py` ← `experiments/artifacts/a4/j3_ablations.json` |
| `tab_bits.tex` | bit width one field at a time (two panels) | same |
| `tab_bitstream.tex` | bitstream composition of the shipped point | ← `artifacts/a4/m24_encode_streams.txt` |
| `tab_frontier.tex` | rate–coverage frontier by action family | ← `artifacts/a4/j1_reliability.json` |
| `tab_collision.tex` | matched-rate collision | same |
| `tab_planners.tex` | four planners, one tolerance | same |
| `tab_decision.tex` | prior vs audit decision rules (56 cells) | ← `artifacts/a4/j2_audit_decision.json` |
| `tab_prune.tex` | five pruning scores + BD-rate | ← `artifacts/a4/j3_ablations.json` |
| `tab_perceptual.tex` | PSNR / SSIM / LPIPS across the pruning arms | same |
| `tab_cost.tex` | decode time and memory, encode stages | same |
| `tab_viewlevel.tex` | pixel vs view coverage and audit error per operating point | `experiments/j4_report.py` ← `_pull_j4/*.json` |
| `tab_gap.tex` | our best row vs published operating points | ← `artifacts/a4/sota_table.md` |
| `tab_resolution.tex` | audit verdict bucketed by distance from the tolerance | `tools/jvcir_resolution.py` ← `artifacts/a4/j2_audit_decision.json` |
| `tab_abstain.tex` | what a single audit pass buys as the abstention band widens | same |
| `COVER_LETTER.md` | cover letter: fit, position, the honestly computed gap, reviewer profiles | hand-written |
| `CHECKLIST.md` | the journal's 15 hard items and the two author actions | hand-written |

Figures live in `../../figures_j/` and are generated, not drawn by hand:

```bash
python tools/jvcir_fig_framework.py    # Fig. 1, the pipeline
python tools/jvcir_fig_frontier.py     # Fig. 2, rate–coverage and the pruning dose–response
python tools/jvcir_fig_viewlevel.py    # Fig. 3, pixel vs view coverage of the shipped quantile
python tools/jvcir_fig_audit.py        # Fig. 4, audit vs prior on the 56 decision cells (+ j5_fig_audit.json)
python tools/jvcir_fig_decibel.py      # Fig. 5, why a decibel budget is not a coverage budget (+ j5_fig_decibel.json)
python tools/jvcir_fig_graphical.py    # graphical abstract (uploaded separately, not in the manuscript)
python tools/jvcir_fig_qual.py         # Fig. 6, the qualitative grid (needs _pull_j5/ from tools/pull_j5.ps1)
```

## Reproduce the whole package from the artifacts

```bash
python experiments/j3_ablations.py            # verify + refresh the ablation/cost/stream/perceptual rows
python experiments/j1_reliability.py          # rate–coverage frontier, collision, planners, pp/dB
python experiments/j2_audit_decision.py       # prior vs audit decision rules
python tools/jvcir_tables.py                  # regenerate the 12 tables
python tools/jvcir_fig_framework.py           # Fig. 1
python tools/jvcir_fig_frontier.py            # Fig. 2
python tools/jvcir_fig_viewlevel.py           # Fig. 3
python tools/jvcir_fig_audit.py               # Fig. 4
python tools/jvcir_fig_decibel.py             # Fig. 5
cd submission/jvcir && pdflatex main && bibtex main && pdflatex main && pdflatex main
cd ../.. && python tools/verify_jvcir.py      # the gate
python tools/make_deposit_jvcir.py            # the deposit archive
```

## What the gate checks (11 sections)

`tools/verify_jvcir.py` runs: compliance (250-word abstract, 5 highlights ≤85 chars, 1–7 keywords), placeholders
(only the two author-supplied slots may remain), structure (`\input` and `\includegraphics` targets), citations
(every key exists, no orphans), tables (every `tab_*.tex` regenerates byte-identically), figures (vector + ≥1200 px
raster, discovered from the manuscript, not hard-coded), provenance (`j3_ablations.py --check`), build (PDF newer
than sources, ≥8 pages, no undefined references), claims (16 headline numbers appear in the tables that carry
them), **prose** (no duplicated paragraph; the gap range and the matched-decibel claim equal the values computed
from the artifacts) and **references** (at least the journal's 2026 lower quartile of 38; `verify_refs.py`
resolves every DOI/arXiv id with `--net`).

## Author actions before upload

1. The deposit is already in place (GitHub release `v1.0.0` + Software Heritage snapshot, both named in the
   manuscript); if a citable DOI is wanted later it can be added at proof without changing the claim.
2. Fill Elsevier's declarations tool for the competing-interest `.docx` (the text is already in the manuscript).
