# J4 — coverage–rate curve + view-level coverage (COMPLETED 2026-11-18 12:25; results in `J4_RESULTS.md`)

**Why this round.** The competitor survey (`review/CARE_GS_GAP_2026-11-18.md`) says the empty slot our paper can fill
is *coverage as a function of bitrate* for a 3D asset, and that our weakest cited claim is the per-pixel-vs-view-level
gap (VSCP's 89.9 % vs 61.4 %) — currently we only cite it. Both need per-view residuals for **container** operating
points, which no existing artifact has: the M5 grid has rates and aggregate coverage but not residuals, and the v120
audit grid has residuals but for *edit* variants, not for a colour/geometry ladder.

**Node.** MatPool instance **2142563**, A100-PCIE-40GB, region 16, ¥2.80/h, image `Pytorch 2.6.0_cuda_12.4` (634285),
rented 2026-11-18 11:23. The three released PLYs were still cached in `/mnt/m35cache` (bicycle 1.52 GB, bonsai 309 MB,
stump 1.23 GB), which removes the download that dominated previous rounds; only COLMAP + `images_4` are fetched
(hf-mirror, `alexmkwizu/gaussian_training_datasets`).

**Sweep.** `experiments/qfp_rd.py --variant-set j4` on `bicycle,stump`, `--factor 4`, `--gt-convention archive`,
`--fidelity --lpips-net alex`. The J4 ladder is the colour budget at fixed geometry (`sh6/sh4/sh3/sh2` = 96/64/48/32
bit) plus one geometry field at fixed colour (`gp4-6-6`, `gp6-4-6`, `gp6-6-4`, `c7`), with `clean` as reference.
Each row packs per-view residuals, so coverage, view-level coverage and the audit can all be computed afterwards.

## Criteria (written before the run; the run is already launched, no number seen)

| | criterion | pass condition |
|---|---|---|
| **J4-C1** | coverage falls as rate falls, along the colour ladder, on both scenes | drop ≥ 0 at every step and monotone within 1 pp of noise |
| **J4-C2** | the action-family asymmetry reproduces per view | at a matched rate, the geometry-coarsened row loses ≥ 2× the coverage of the colour row, on ≥ 3 of 4 geometry fields |
| **J4-C3** | view-level coverage is below pixel-level, and the gap grows as rate falls | view-event coverage (≥90 % of pixels covered) < pixel coverage on every non-clean row; gap at the lowest rate > gap at the highest |
| **J4-C4** | the audit stays usable at every operating point | 2-view audit MAE ≤ 3.0 pp on every row |

If C1 fails, the colour ladder is not a rate axis and the figure is abandoned; if C3 fails, the paper keeps citing
VSCP instead of measuring the gap (and says so).

## Deliverables if the criteria hold

1. `figures_j/fig3_coverage_rate.pdf` — coverage vs rate, two scenes, both families, tolerance band.
2. `submission/jvcir/tab_viewlevel.tex` — pixel coverage vs view-event coverage vs audit error, per operating point.
3. §5.2/§5.6 text: replace the cited VSCP caveat with our own measured gap, and add one sentence to §6 saying it is
   now measured rather than inherited.
4. `experiments/artifacts/a4/j4_*.json` + a `J4_RESULTS.md` in the same shape as J1/J2, including any failed criterion.

## Cost log

| time | event | cost |
|---|---|---|
| 11:23 | node rented (A100 40 GB, ¥2.80/h) | — |
| 11:26 | env probed: torch 2.6.0+cu124, CUDA ok, 12 cores, 90 GB RAM | — |
| 11:30 | code bundle pushed (60 KB tgz, chunked base64), `py_compile` ok | — |
| 11:31 | deps installed: `gsplat==1.5.3 --no-deps`, rich, jaxtyping, ninja, plyfile, zstandard | — |
| 11:33 | COLMAP/images fetch started (bicycle 194 imgs, stump 125 imgs, ~200 MB) | — |
| 11:42 | `j4_go.sh` launched detached (waits for images → archives → sweep → `/root/j4.done`) | — |
| 11:51 | archives built for bicycle + stump from the cached PLYs | — |
| 11:51 | sweep failed #1: `ModuleNotFoundError: common` | — |
| 11:58 | sweep failed #2: `ModuleNotFoundError: dump_artifacts` | — |
| 12:03 | sweep failed #3: `J4_VARIANTS` was a tuple, `_variants()` expects a comma string | — |
| 12:05 | sweep failed #4: gsplat needs `packaging` (installed with `--no-deps`) | — |
| 12:07 | sweep started but at **factor 4 on images_4** = 309×206 — wrong protocol, killed | — |
| 12:09 | relaunched at **factor 1** → 1236×822, 25 views, i.e. the paper's protocol | ~¥2.2 so far |

**Four environment lessons, recorded so the next round does not rediscover them**: (i) `gsplat --no-deps` leaves
`packaging` missing and the failure surfaces deep inside `gsplat/cuda/_backend.py`, not at install time; (ii) the
node-side bundle must include `experiments/common.py`, `experiments/m1_analyse.py` and
`experiments/dump_artifacts.py` — `qfp_rd` imports them lazily, so `py_compile` does not catch the omission;
(iii) registry entries in `VARIANT_SETS` are comma-separated **strings**, not tuples; (iv) `--factor` multiplies on
top of the archive resolution, so an `images_4` archive needs `--factor 1` or the render is 4× too small.

Release the node as soon as the artifacts are pulled (the user pre-approved release).
