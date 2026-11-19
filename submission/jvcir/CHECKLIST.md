# JVCIR submission checklist (hard items only)

Verified against the journal's Guide for Authors on 2026-11-18; sources in
`review/JVCIR_SCOPE_2026-11.md`.

| # | item | requirement | status |
|---|---|---|---|
| 1 | Abstract | ≤ 250 words, standalone | **PASS** (239 words, gate §1) |
| 2 | Highlights | 3–5 bullets, each ≤ 85 characters incl. spaces, separate file, "highlights" in the name | **PASS** (`highlights.txt`, 5 × 77–82) |
| 3 | Keywords | 1–7 | **PASS** (5 — the journal's own papers use 3–4) |
| 4 | Source files | `.tex` editable (a PDF alone is not a source file) | **PASS** (`main.tex` + `tab_*.tex` + `refs.bib`) |
| 5 | Figures | separate files; photos ≥300 dpi; **no multi-panel images combined into one file** | **PASS with a note**: Figs. 2, 4 and 5 are multi-panel figures *intentionally compared* (allowed exception); all six are vector PDF + 300 dpi PNG |
| 6 | Graphical abstract | encouraged, ≥1328 px wide | **READY** — `figures_j/graphical_abstract.pdf` (3086 × 1034 px PNG), `tools/jvcir_fig_graphical.py` |
| 7 | References | any consistent style at submission; numbered at proof | **PASS** (`elsarticle-num`, 48 entries, 14 from this journal; every locator resolved by `tools/verify_refs.py`) |
| 8 | CRediT | required, 14 roles | **PASS** (in the manuscript) |
| 9 | Competing interests | required, Elsevier declarations tool `.docx` | **TEXT READY**, `.docx` is an author action |
| 10 | Funding | required; fixed wording if none | **PASS** ("no specific grant" wording used) |
| 11 | Data availability | **Option C: deposit required, link required** | **BLOCKED ON AUTHOR** — two `\TBD{}` slots |
| 12 | Generative AI | declare before the reference list if used | **PASS** (section present) |
| 13 | Anonymisation | single-anonymised → **keep the author's name** | **PASS** (name and e-mail in the manuscript) |
| 14 | Page limit | none stated | **PASS** (22 pages, 15 tables) |
| 15 | Special issue | none open for this topic | **N/A** (regular submission) |

## Author actions (the only two blocking items)

1. **Zenodo DOI + GitHub URL.** Upload `deposit_jvcir.zip` (or push the repository and cut a release with Zenodo's
   GitHub integration), then replace the two `\TBD{}` macros in `main.tex`. Steps and the exact replacement text are
   in `review/DATA_DEPOSIT_GITHUB_ZENODO_2026-11.md`.
2. **Competing-interest `.docx`.** Generate it with Elsevier's declarations tool and upload it at the "attach/upload
   files" step. The declaration text is in the manuscript.

## Tone and positioning decisions (recorded so they do not regress)

1. **No priority claims.** The manuscript and the cover letter do not say "first". The verifiable fact
   (the venue's 3DGS line addresses training, not delivery) is stated as *where the paper sits*, not as a trophy,
   and the sentence carries the "to my knowledge" hedge implicitly by naming the comparison literature that lives
   outside the venue.
2. **No confession block.** The manuscript's boundaries are stated once, in Limitations, and referenced from the
   cover letter in one sentence. They are not re-listed as a "what we do not claim" section, which reads as the
   author arguing the reviewer's case for them.
3. **The gap is our own number, not the reviewer's find.** Table 11 computes the published-frontier comparison, so the
   2.97 / 3.62 dB appear in the manuscript and the cover letter before a reviewer has to discover them.
4. **Modesty where it is free, confidence where it is earned.** Claims about our own measurements are stated with
   their intervals and their failures (two of the pre-registered criteria in the J1 round failed and are reported);
   claims about other people's work are attributed and not characterised.

## After those two

```bash
python tools/verify_jvcir.py     # expects PASS, exit 0 (11 sections)
```

Then submit at Editorial Manager (`editorialmanager.com/JVCI`) with: `main.tex`, `refs.bib`, the 12 `tab_*.tex`
files, `fig1_framework.pdf` … `fig6_qualitative.pdf`, `graphical_abstract.pdf`, `highlights.txt`, `COVER_LETTER.md`
(as a PDF is fine at submission), and the declarations `.docx`.

## What to do if the editor asks about scope

The precedent to cite is the journal's own compression line (`10.1016/j.jvcir.2026.104966`,
`10.1016/j.jvcir.2026.104913`, `10.1016/j.jvcir.2025.104610`, `10.1016/j.jvcir.2026.105027`) plus its 3DGS line
(`10.1016/j.jvcir.2026.104815`, `10.1016/j.jvcir.2026.104978`, `10.1016/j.jvcir.2025.104682`). The manuscript cites
all seven; the cover letter names the two clusters explicitly. Both are quoted in `review/JVCIR_SCOPE_2026-11.md`.
