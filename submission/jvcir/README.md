# Derived tables — map and reproduction

The 17 `tab_*.tex` files in this directory are generated, not hand-written: each one is produced by a script in
`tools/` or `experiments/` from an artifact JSON in `experiments/artifacts/a4/`. They are the tables of

> **CARE-GS: coverage-aware rate reduction for 3D Gaussian Splatting assets** (Tianji Su, Ningbo University;
> submitted to the *Journal of Visual Communication and Image Representation*).

The manuscript itself is **not** archived here; it goes through the journal's submission system. This directory
exists so that every published table can be regenerated from the deposited measurements.

| table | what it is | how it is produced |
|---|---|---|
| `tab_container.tex` | container ladder (A0–A6) | `tools/jvcir_tables.py` ← `experiments/artifacts/a4/j3_ablations.json` |
| `tab_bits.tex` | bit width one field at a time (two panels) | same |
| `tab_bitstream.tex` | bitstream composition of the shipped point | ← `experiments/artifacts/a4/m24_encode_streams.txt` |
| `tab_frontier.tex` | rate–coverage frontier by action family | ← `experiments/artifacts/a4/j1_reliability.json` |
| `tab_collision.tex` | matched-rate collision | same |
| `tab_planners.tex` | four planners, one tolerance | same |
| `tab_decision.tex` | prior vs audit decision rules (56 cells) | ← `experiments/artifacts/a4/j2_audit_decision.json` |
| `tab_prune.tex` | five pruning scores + BD-rate | ← `experiments/artifacts/a4/j3_ablations.json` |
| `tab_perceptual.tex` | PSNR / SSIM / LPIPS across the pruning arms | same |
| `tab_cost.tex` | decode time and memory, encode stages | same |
| `tab_viewlevel.tex` | pixel vs view coverage, audit error per operating point | `experiments/j4_report.py` ← `_pull_j4/*.json` |
| `tab_gap.tex` | our best row vs published operating points | ← `experiments/artifacts/a4/sota_table.md` |
| `tab_resolution.tex` | audit verdict bucketed by distance from the tolerance | `tools/jvcir_resolution.py` ← `experiments/artifacts/a4/j2_audit_decision.json` |
| `tab_singlepass_abstain.tex` | what a single audit pass buys as the abstention band widens | `tools/j6_singlepass_analyse.py` ← `experiments/artifacts/a4/j6_singlepass.json` |
| `tab_j8.tex` | rate axis with both families charged the container's bytes | `experiments/j8_rate.py` ← `experiments/artifacts/a4/j9_report_mean.json` |
| `tab_j9.tex` | six tolerances × three scenes, per-channel max | `experiments/j9_tables.py` ← `experiments/artifacts/a4/j9_report_max3.json` |

## Regenerate

Everything below runs on CPU from the deposited artifacts; no rendering or training is involved.

```bash
python tools/jvcir_tables.py             # the 11 tables driven by j3/j2/j1 artifacts
python tools/jvcir_resolution.py         # tab_resolution.tex
python tools/j6_singlepass_analyse.py    # tab_singlepass.tex, tab_singlepass_abstain.tex
python experiments/j8_rate.py            # tab_j8.tex
python experiments/j9_tables.py          # tab_j9.tex
python experiments/j4_report.py          # tab_viewlevel.tex (needs the pulled _pull_j4/ dumps)
```

The figures live in `../../figures_j/` and are produced the same way:

```bash
python tools/jvcir_fig_framework.py    # Fig. 1, the pipeline
python tools/jvcir_fig_frontier.py     # Fig. 2, rate–coverage and the pruning dose–response
python tools/jvcir_fig_viewlevel.py    # Fig. 3, pixel vs view coverage of the shipped quantile
python tools/jvcir_fig_audit.py        # Fig. 4, audit vs prior on the 56 decision cells
python tools/jvcir_fig_decibel.py      # Fig. 5, why a decibel budget is not a coverage budget
python tools/jvcir_fig_qual.py         # Fig. 6, the qualitative grid (needs _pull_j5/)
python tools/jvcir_fig_graphical.py    # the graphical abstract
```

Regenerating a table rewrites the same file byte for byte; if it does not, the artifact and the table have drifted
and the number in the paper is not the number in the deposit.

## What is not here

`tools/verify_jvcir.py` is the submission gate: it cross-checks a manuscript against these tables and the artifacts.
It needs the manuscript source, which is not part of this repository, so it runs in the author's working copy rather
than here. The table and figure generators above do not need it.