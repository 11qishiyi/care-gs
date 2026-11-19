# J4 results — the shipped quantile, held fixed, against rate

**Round J4, 2026-11-18. MatPool instance 2142563 (A100-PCIE-40GB, region 16, ¥2.80/h).**
Criteria were pre-registered in `J4_PLAN.md` before the sweep started. Verdicts below are the script's, not a
reading of it: `experiments/j4_report.py` computes them from `_pull_j4/{m1_manifest,j4_coverage}.json` and writes
`experiments/artifacts/a4/j4_report.{json,md}` plus `submission/jvcir/tab_viewlevel.tex`.

## Setup

| item | value |
|---|---|
| scenes | `bicycle` (25 held-out views, 1236×822) and `stump` (16 held-out views) — the two cross-paper scenes |
| configurations | `clean` + colour ladder 96/64/48/32 bit + one geometry field at 48 bit (quaternions, scales, opacity, positions) |
| quantile | $q$ calibrated **once** on the clean model's calibration views ($\alpha = 0.1$: $q = 0.0891$ bicycle, $0.0738$ stump), then held fixed |
| evaluation | 100 random calibration/deployment splits per row; pixel coverage, view-event coverage ($\geq 90\%$ of a view's pixels covered), and a 2-view audit error |

## The table (bicycle; stump is in `j4_report.md`)

| configuration | MB | rate | PSNR | pixel cov | view cov | gap (pp) | audit (pp) |
|---|---|---|---|---|---|---|---|
| `clean` | 1447.14 | 1.00× | 24.65 | 0.910 | 0.722 | +18.77 | 3.86 |
| `gp6-6-6_c8_sh6` | 285.71 | 5.07× | 24.58 | 0.908 | 0.722 | +18.56 | 3.90 |
| `gp6-6-6_c8_sh4` | 212.13 | 6.82× | 24.56 | 0.908 | 0.722 | +18.53 | 3.89 |
| `gp6-6-6_c8_sh3` | 175.34 | 8.25× | 24.47 | 0.906 | 0.682 | +22.34 | 3.94 |
| `gp6-6-6_c8_sh2` | 138.54 | 10.45× | 23.54 | 0.874 | 0.521 | +35.34 | 4.55 |
| `gp4-6-6_c8_sh3` | 170.74 | 8.48× | 24.12 | 0.898 | 0.682 | +21.60 | 3.91 |
| `gp6-4-6_c8_sh3` | 170.74 | 8.48× | 23.54 | 0.880 | 0.478 | +40.27 | 4.28 |
| `gp6-6-4_c8_sh3` | 173.80 | 8.33× | 24.36 | 0.902 | 0.682 | +22.02 | 3.89 |
| `gp6-6-6_c7_sh3` | 173.04 | 8.36× | 24.40 | 0.904 | 0.682 | +22.16 | 3.94 |

## Verdicts (two pass, two fail — both failures are in the paper)

| | criterion | bicycle | stump | outcome |
|---|---|---|---|---|
| **C1** | coverage never rises as compression strengthens | `0.910 → 0.908 → 0.906 → 0.874` | `0.911 → 0.909 → 0.906 → 0.788` | **PASS** |
| **C2** | geometry coarsening costs ≥ 2× a colour cut at matched rate, on ≥ 3 of 4 fields | 2 of 4 (`2.72×`, `6.91×`) | 1 of 4 (`5.88×`) | **FAIL** |
| **C3** | view coverage below pixel coverage, gap growing as rate falls | gap `+18.5 → +35.3` pp | gap `+16.8 → +78.8` pp | **PASS** |
| **C4** | 2-view audit within 3.0 pp on every row | worst `4.55` pp | worst `3.22` pp | **FAIL** |

## What this changes in the manuscript

1. **New §5.7 + Table 9 + Fig. 3.** The headline is C3, and it is the strongest single number this round produced:
   at a nominal 90 % pixel guarantee, only **72 %** of views have 90 % of their pixels covered — on the *clean*
   model, before any compression. At 10.5× the view-level fraction falls to 0.00 on `stump` while pixel coverage is
   still 0.79.
2. **One claim withdrawn.** §5.3's coarse statement (pruning is dominated) stands, but the fine statement that
   *every* geometry field is worse per byte than colour does not hold at this resolution (1.4–1.8× on five of eight
   field-scene pairs). The paper now says so, with the ratio for each field.
3. **One caveat quantified.** The audit's precision degrades from 2.0 pp on the edit grid to 3.2–4.6 pp on a
   quantisation ladder — a different perturbation family, a different error. §5.5 and §6 state both.
4. **Abstract** carries the 72 % number, so the first screen includes a measured weakness rather than a cited one.

## Cost

| stage | wall clock | cost |
|---|---|---|
| rent → env → code push | 11:23–11:31 | — |
| COLMAP/images fetch (PLYs were cached) | 11:33–11:51 | — |
| sweep (compile + 2 assets × 9 configs at 1236×822) | 12:09–12:14 | — |
| analysis + pull | 12:15–12:25 | — |
| **total** | ~1 h | **≈ ¥2.8** |

Node released after the artifacts were pulled and verified.

## Reproduce

```bash
# on a node with the archives built (see J4_PLAN.md for the four environment traps)
python qfp_rd.py --archive /root/m360std --scenes bicycle,stump --variant-set j4 \
    --out /root/res/j4 --factor 1 --gt-convention archive --device cuda --fidelity
python j4_analyse.py --npz /root/res/j4 --out /root/res/j4/j4_coverage.json --n-splits 100
# locally
python experiments/j4_report.py        # scores C1-C4, writes the table and the report
python tools/jvcir_fig_viewlevel.py    # Fig. 3
```
