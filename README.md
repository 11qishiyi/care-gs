# CARE-GS — reproduction data and code

Deposit for

> **CARE-GS: coverage-aware rate reduction for 3D Gaussian Splatting assets**
> Tianji Su, Ningbo University — submitted to the *Journal of Visual Communication and Image Representation*

The paper asks one question: **when a 3D Gaussian Splatting asset that carries a per-pixel quality guarantee is
re-compressed by whoever receives it, does the guarantee survive — and can the recipient find out without the
issuer?** The answer is that the *action family* decides (quantisation keeps it, pruning does not), and that a
recipient can audit the carrier for the price of one render pass.

This repository is the research-data deposit for that paper. It holds the measurements, the code that produced
them and the code that turns them into the published tables and figures. The manuscript itself is not archived
here; it is published by the journal.

## What is here

| path | what it is |
|---|---|
| `experiments/` | the measurement scripts, their results notes (`J1`–`J9`), and the artifact JSON every number in the paper is regenerated from (`experiments/artifacts/a4/`) |
| `tools/` | table and figure generators, the reference verifier and the submission gate |
| `submission/jvcir/tab_*.tex` | the 17 generated tables, with their generators listed in `submission/jvcir/README.md` |
| `figures_j/` | the six figures and the graphical abstract, as vector PDF and 300 dpi PNG, each produced by a script in `tools/` |
| `_pull_j5/`, `_pull_j6/`, `_pull_j7/`, `_pull_j9/` | the pulled artifacts the qualitative figure and three tables are built from (magnification patches, per-split audit pairs, quantile dumps) |
| `research/code/calib/` | the renderer wrappers and COLMAP I/O the measurement scripts import |
| `results_v120/` | a single derived audit bound that the deposit also carries |

## Reproduce

Everything that produces a **number in the paper** runs on CPU from the artifacts in `experiments/artifacts/a4/`:

```bash
python experiments/j3_ablations.py --check     # every printed number traced to its artifact
python tools/jvcir_tables.py                   # the 11 j1/j2/j3-driven tables
python tools/jvcir_resolution.py               # tab_resolution.tex
python tools/j6_singlepass_analyse.py          # tab_singlepass.tex, tab_singlepass_abstain.tex
python experiments/j8_rate.py                  # tab_j8.tex
python experiments/j9_tables.py                # tab_j9.tex
python experiments/j4_report.py                # tab_viewlevel.tex  (reads _pull_j4/)
```

and the figures the same way:

```bash
python tools/jvcir_fig_framework.py  && python tools/jvcir_fig_frontier.py
python tools/jvcir_fig_viewlevel.py  && python tools/jvcir_fig_audit.py
python tools/jvcir_fig_decibel.py    && python tools/jvcir_fig_qual.py
python tools/jvcir_fig_graphical.py
```

Regenerated files come out byte-identical to the ones committed; if one does not, that artifact and that table have
drifted.

`tools/verify_jvcir.py` is the submission gate. It cross-checks a manuscript against the tables and artifacts, so it
runs in the author's working copy (it needs the manuscript source, which is not part of this deposit).

## Citing

`CITATION.cff` names the paper. Released as tag `v1.1.0`; a copy of the deposit archive is attached to that release.

## License

Code: MIT (`LICENSE`). The rendered patches under `_pull_j5/` and the table artifacts are derived from the
Mip-NeRF 360 captures (Barron et al., CVPR 2022), used under that dataset's terms.