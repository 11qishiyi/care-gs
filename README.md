# CARE-GS — reproduction repository

Code, derived tables, figures and the manuscript for

> **CARE-GS: coverage-aware rate reduction for 3D Gaussian Splatting assets**
> Tianji Su, Ningbo University — submitted to the *Journal of Visual Communication and Image Representation*

The paper asks one question: **when a 3D Gaussian Splatting asset that carries a per-pixel quality guarantee is
re-compressed by whoever receives it, does the guarantee survive — and can the recipient find out without the
issuer?** The answer is that the *action family* decides (quantisation keeps it, pruning does not), and that a
recipient can audit the carrier for the price of one render pass.

## What is here

| path | what it is |
|---|---|
| `submission/jvcir/` | the manuscript (`main.tex`), bibliography, every generated table, the highlights file, the cover letter and the submission checklist |
| `figures_j/` | the six figures, as vector PDF and 300 dpi PNG, each produced by a script in `tools/` |
| `tools/` | table and figure generators, the compliance helper, the reference verifier and the submission gate |
| `experiments/` | the measurement scripts, their results notes (`J1`–`J6`), and the artifact JSON every number in the paper is regenerated from |
| `review/` | the venue survey, the gap analyses, the design notes and the citation-verification output |
| `_pull_j5/`, `_pull_j6/` | the small pulled artifacts two figures and two tables are built from (magnification patches, per-split audit pairs) |
| `research/code/calib/` | the renderer wrappers and COLMAP I/O the measurement scripts import |

## Reproduce

Everything that produces a **number in the paper** runs on CPU from the artifacts in `experiments/artifacts/a4/`:

```bash
python experiments/j3_ablations.py --check     # every printed number traced to its artifact
python tools/jvcir_tables.py                   # the 13 artifact-backed tables
python tools/jvcir_resolution.py               # the audit-resolution tables
python tools/j6_singlepass_analyse.py          # the measured single-pass tables (needs _pull_j6)
python tools/jvcir_fig_frontier.py             # Fig. 2
python tools/jvcir_fig_audit.py                # Fig. 3
python tools/jvcir_fig_decibel.py              # Fig. 4
python tools/jvcir_fig_qual.py                 # Fig. 6 (needs _pull_j5)
cd submission/jvcir && pdflatex main && bibtex main && pdflatex main && pdflatex main
cd ../.. && python tools/verify_jvcir.py       # the gate: 11 sections, exit 0 required
```

The three **rendering** rounds (`J4`, `J5`, `J6`) need a CUDA GPU and the Mip-NeRF 360 assets; their scripts and
their inputs are recorded in `experiments/J*_PLAN.md` and their outcomes — including the two criteria that failed —
in `experiments/J*_RESULTS.md`. Two things cannot be rebuilt: the four `*_i7k` checkpoints (trained on rented nodes
that no longer exist) and the original `stump` checkpoint (the public mirror now serves a copy with non-finite
scales). Both are stated in the manuscript.

## What to read first

- `submission/jvcir/main.pdf` — the paper.
- `review/JVCIR_BEST_PRACTICE_2026-11-18.md` — what this journal actually publishes, measured on 514 articles,
  and exactly where this manuscript sits against it.
- `experiments/J5_RESULTS.md`, `experiments/J6_RESULTS.md` — the two rounds that report failures rather than wins.

## Verification, not decoration

`tools/verify_jvcir.py` is not a linter. It regenerates every table byte-identically from the artifacts, checks that
the range quoted in the prose equals the range computed from the data, checks that the figure labels equal the
render manifest, checks that no paragraph appears twice, and checks that every DOI and arXiv identifier resolves to
the title it claims to be. A number that cannot be traced is treated as a defect.

## Licence and citation

Code: MIT (`LICENSE`). Manuscript text and figures: CC BY 4.0. If you use the artifacts, cite the paper; the
machine-readable citation is in `CITATION.cff`.
