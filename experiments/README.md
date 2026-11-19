# Revision measurements: GPU dump → CPU recomputation

The revision needs measurements the current draft does not have. This folder
contains the whole pipeline that produces them, designed so that the **GPU node is
needed for minutes only**: it renders each held-out view once per scene × variant
and ships small `.npz` artifacts back; every number in the paper is then
recomputed on a CPU-only machine with nothing but numpy.

```
GPU node  (≈5–10 min, ≥16 GB VRAM)          CPU workstation (numpy only, no torch/cv2)
──────────────────────────────────          ───────────────────────────────────────────
make_pup_variant.py   ─┐                     region_coverage.py  → pixel / block / voxel
dump_artifacts.py     ─┴─► <scene>.npz  ───► task_sweep.py       → 108-cell threshold sweep
                            dump_summary.json second_task.py      → block-matching flow task
                            pup_summary.json  (all: 400-split protocol, cluster bootstrap)
```

## Files

| file | role | where it runs | local status |
|---|---|---|---|
| `common.py` | protocol constants (`cq`, 400 splits), INRIA PLY I/O, voxel hash, coverage helpers, bootstrap | both | **verified** |
| `dump_artifacts.py` | renders every held-out view for `clean / prune50 / prune30 / pup30 / shdeg1 / quant8`; writes one npz per scene + `dump_summary.json` | **GPU** | `--dry-run` verified on CPU (schema + sizes); torch/gsplat path **not** locally runnable |
| `make_pup_variant.py` | PUP/Fisher-diagonal top-30 % PLY (via `calib/sensitivity.py`) + Fisher-vs-opacity rank correlation | **GPU** | `--dry-run` verified on CPU (ranking + PLY round-trip); Fisher/backprop path **not** locally runnable |
| `task_sweep.py` | 108-cell sweep of the patch-localisation task (patch 32/48/64 × tol 1/2/4 × peak 0.30/0.45/0.60/0.75 × search 16/24/32, 100 patches) + drop-stability analysis | **CPU** | **verified** |
| `second_task.py` | second downstream task: 3-level pyramid 9×9 block-matching displacement, hit rate ≤1 px, view-level cluster bootstrap | **CPU** | **verified** |
| `region_coverage.py` | pixel / B×B block-max / world-space voxel coverage and drop under the same 400 splits | **CPU** | **verified** (voxel = `--mode approx`, see caveats) |
| `tests/test_pipeline_cpu.py` | 10 synthetic-case tests with known answers | **CPU** | **verified** (`python -m pytest`, 0.8 s) |
| `local_verify.ps1` | runs tests + dry run + all three analyses in one go | **CPU** | **verified** |

## Remote execution (one chain)

Repo on the node is assumed to contain `research/code` (the calib modules) at
`$REPO`; the released archive is at `$ARCHIVE` with the layout
`$ARCHIVE/output/<scene>/point_cloud/iteration_40000/point_cloud.ply`.

```bash
export REPO=/workspace/3dsg          # this workspace on the node
export ARCHIVE=/workspace/data/out3dgs
export REC=/workspace/data/rev
mkdir -p "$REC" && cd "$REPO"

# 1) PUP / Fisher top-30% PLY per scene  (needs the calibration views only)
python experiments/make_pup_variant.py --archive "$ARCHIVE" \
    --out-dir "$REC/pup" --device cuda --n-views 4 2>&1 | tee "$REC/pup.log" && \

# 2) render every held-out view for every scene x variant  (the only heavy step)
python experiments/dump_artifacts.py --archive "$ARCHIVE" \
    --out "$REC/dump" --pup-dir "$REC/pup" --device cuda \
    --profile full 2>&1 | tee "$REC/dump.log" && \

# 3) bundle for transfer
tar -czf "$REC/rev_artifacts.tgz" -C "$REC" dump pup/pup_summary.json && \
du -sh "$REC/rev_artifacts.tgz"
```

Use `--profile core` (4 variants, ~2/3 the size) or `--profile compact`
(`--downsample 2`, ~1/4 the size) if the return volume matters more than pixel
resolution; see the size table below. `--no-compress` writes plain
`np.savez` (faster, ~1.3× bigger).

Sanity check that the run is complete before transferring:

```bash
python - <<'PY'
import glob, json, numpy as np
for f in sorted(glob.glob("/workspace/data/rev/dump/*.npz")):
    z = np.load(f, allow_pickle=False); m = json.loads(str(z["meta"]))
    print(f.split("/")[-1], z["resid"].shape, z["variant_names"].tolist(), m["scene"])
PY
```

## Expected GPU cost

*Rendering*: 4 scenes × 6 variants × ~18 held-out views ≈ 430 renders at 259×389
(factor 4). The released 3DGS checkpoints are in the 2–6 M primitive range; at
that size a view costs ~0.05–0.2 s, so rendering is ~1–2 min for all four scenes.
The dominant cost is PLY I/O (~1–1.5 GB per scene) — expect **≈5–10 min total**.
peak VRAM for `dump_artifacts.py`: the asset (~1.5 GB fp32) plus gsplat's tile
buffers and a 2-view render chunk ≈ **6–10 GB** — an RTX 3090/A10 (24 GB) is
comfortable, 16 GB should be enough.

*Fisher pass* (`make_pup_variant.py`) keeps a gradient **and** an accumulator for
every parameter: `N × (3 means + 3 scales + 4 quats + 1 opacity + 3 sh0 + 45 shN)
× 4 B × 2` ≈ 2.8 GB at 6 M primitives, on top of the asset itself, plus one view
of rasteriser buffers. Budget **≈10 GB** and use `--n-views 4`; on a 6 M-primitive
scene it runs in well under a minute per scene.

## What comes back (measured on the synthetic fixture, real shapes)

`npz` per scene contains `gray_render (V,m,H,W) f16`, `resid (V,m,H,W) f16`,
`gray_gt (m,H,W) f16`, `views (m,)`, `c2w (m,4,4)`, `K (m,3,3)`,
`prim_means (n,3) f32` + `prim_opacity` (decimated clean point cloud for the
voxel regions), `variant_names`, `meta` (json: scene, factor, W/H, alpha,
`n_primitives` per variant, downsample, `dry_run` flag).

Measured by `dump_artifacts.py --dry-run` on 259×389 maps with 18 views
(18 views × 6 variants), `np.savez_compressed`:

| profile | variants | stored px | raw/scene | measured/scene | 4 scenes |
|---|---|---|---|---|---|
| `full` (default) | 6 | 259×389 (factor 4) | 48.0 MB | **39.3 MB** | ~157 MB |
| `core` | 4 | 259×389 | 31.4 MB | **26.7 MB** | ~107 MB |
| `compact` (`--downsample 2`) | 6 | 129×194 | 11.5 MB | **9.6 MB** | ~38 MB |

So: the 30 MB/scene target is met by `core` (26.7 MB) and `compact` (9.6 MB), not
by `full` (39.3 MB). Real residual maps are noisier than the synthetic ones and
will compress a little worse, so budget ±20 % and let `dump_summary.json`'s
`bytes`/`within_budget` fields tell you after the first scene (the script warns
when a scene exceeds `--budget-mb`). `dump_summary.json` and `pup_summary.json`
are a few hundred KB and contain the PSNR / residual / per-view tables plus the
Fisher-vs-opacity rank correlations (`pup30` PLYs stay on the node — they are ~10×
the size of the renders).

## Local recomputation (CPU, no GPU)

```bash
python experiments/region_coverage.py --npz experiments/artifacts/dump \
    --out experiments/artifacts/region_coverage.json --blocks 64 --voxel 0.25
python experiments/task_sweep.py      --npz experiments/artifacts/dump \
    --out experiments/artifacts/task_sweep.json
python experiments/second_task.py     --npz experiments/artifacts/dump \
    --out experiments/artifacts/second_task.json
```

`--npz` takes a directory, a single file, or a comma-separated list. Every script
is deterministic (`--seed 0`) and idempotent: the same inputs produce the same
numbers on every run (only the `seconds` / `generated` bookkeeping fields differ),
and each run overwrites its JSON atomically with `indent=1`.

Measured wall-clock on the CPU workstation for **one** synthetic scene
(18 views, 6 variants, 100 k pixels/view, 400 splits) — multiply by 4 for the real
run: `region_coverage.py` **20 s**, `second_task.py` **5.4 s**, `task_sweep.py`
**3 min 55 s** (the 108-cell grid × 6 variants × 100 patches dominates). Total
local recomputation for four scenes ≈ **18 min**, no GPU.

Block size: `--blocks 64` is the size the paper's existing block results use on the
factor-4 residual maps (`certificate_audit.py`'s `--block 64`), and the pooling
uses the same `H // b` floor convention (`--block-mode floor`). Every block row
also records `block_capture_px = block_stored_px × factor × downsample`, so a
reviewer can see that "64×64" here means 256×256 in the original capture.

### What each output gives the paper

* `region_coverage.json` → rows for `(scene, variant) × {pixel, block64, voxel}`,
  each with `clean_mean`, `stale_mean`, `drop_mean` (+2.5/97.5 percentiles over
  the 400 splits) and `degradation_pp = -100·drop`. This is the "pixel column +
  region column" of the main table. Voxel rows come in two flavours
  (`voxel[counted_uncovered]`, `voxel[excluded]`) depending on how regions that
  appear only in deployment are treated, and every row records its own
  `n_regions`, `n_views` and (for voxels) `voxel_size`, `observed_frac`.
* `task_sweep.json` → `per_config` (one row per cell of the 108-cell grid, with
  `hit_clean_<variant>`, `hit_<variant>`, `delta_<variant>`, `degradation_pp_<variant>`,
  and the view-level bootstrap interval `delta_lo_<variant>`/`delta_hi_<variant>`),
  `variant_summary`, `coverage_reference` (the paper's pixel coverage drop for the
  same edits) and `stability` — including
  `stability.task_vs_coverage[<variant>].frac_configs_task_gt_coverage`, i.e. the
  fraction of grid cells in which the 30 %-pruning task drop exceeds its coverage
  drop, plus `full_ranking_agreement` for the variant ordering. `meta.verify`
  records the cell-by-cell agreement with `task_success` (0 mismatches required).
* `second_task.json` → `summary[<variant>]` with `hit_rate`, bootstrap
  `[hit_lo, hit_hi]`, paired `delta = hit(edited) − hit(clean)` with its own
  interval, and per-view hit rates in `per_view_hit_rate` for auditing.

## Mapping artifacts → the cells the revision needs

| revision cell | source | field |
|---|---|---|
| main table, **pixel** coverage + drop per scene × edit | `region_coverage.json` | `rows[variant=…, granularity="pixel"]` → `clean_mean`, `stale_mean`, `drop_mean`, `degradation_pp` |
| main table, **region** columns | same file | `granularity="block64"` and `"voxel[counted_uncovered]"`; `region_vs_pixel[variant][g]` gives the ratio and how many scenes are worse at region level |
| "the task drop is not a threshold artefact" | `task_sweep.json` | `per_config[*].degradation_pp_<variant>` across the 108 cells; `variant_summary[<variant>].{degradation_pp_grid_mean, _min, _max, frac_configs_degraded_gt_2pp}` |
| "task drop vs coverage drop" claim | `task_sweep.json` | `stability.task_vs_coverage[<variant>].frac_configs_task_gt_coverage` |
| "the variant ordering is stable" | `task_sweep.json` | `stability.variant_ordering` (pairwise) and `stability.full_ranking_agreement.frac_configs_exact_rank_match` |
| second, different-family task | `second_task.json` | `summary[<variant>].{hit_rate, hit_lo, hit_hi, delta, delta_lo, delta_hi}` — view-level cluster bootstrap |
| PUP vs opacity pruning | `pup_summary.json` + `region_coverage.json` | `spearman_fisher_vs_opacity`, `topk_overlap`, `fisher_kept_frac_of_total_score`; then the `pup30` vs `prune30` rows |
| edit families beyond pruning | both json | `shdeg1`, `quant8` rows in every table |

## Protocol (must match the existing tables)

* **Images**: archive `cameras.json`, `llffhold=8` test cameras, factor 4, GT read
  through `calib.colmap_io.load_images` + `normalize_exposure` — identical to
  `scripts/many_splits.py`.
* **Residual**: per pixel, `mean over colour channels of |render − gt|`
  (`resid` in the npz). `gray_render`/`gray_gt` are channel means, matching
  `voxel_and_task.py`'s `to_gray`.
* **Splits**: 400 random calibration/deployment view splits from
  `np.random.default_rng(0)`, `n_C = max(2, m//2)` — the generator is reproduced
  bit for bit (`common.split_perms`, asserted in the tests).
* **Threshold**: split-conformal quantile `cq(scores, α=0.1)` with the
  `ceil((n+1)(1−α))` order statistic; identical values to `many_splits.cq`
  (`common.cq` uses `np.partition` for long pixel vectors, asserted equal).
* **Drop**: `drop = coverage(edited) − coverage(clean)`, paired by split, so a
  **negative** drop is a degradation; `degradation_pp = −100·drop` is the positive
  form used in the summaries. Task numbers use `delta = hit(edited) − hit(clean)`
  with the same sign, and `degradation_pp` again positive.
* **Regions**: a region's score is the **max** residual inside it, pooled again by
  **max over the views of a split** — `calib/voxel_cert.py`'s definition, so the
  voxel column is comparable with the paper's existing voxel results.
* **Bootstrap**: view-level cluster bootstrap (resample held-out views with
  replacement, 2000 reps, seed 0), as in the paper's coverage intervals.

## Caveats (read before using the numbers)

1. **GPU paths are not locally verified.** `dump_artifacts.py --dry-run` never
   imports torch, and `make_pup_variant.py --dry-run` replaces the Fisher score
   with a synthetic array. What has been verified locally is the *write path*
   (schema, dtypes, sizes, summary) and the PLY writer/reader; the torch/gsplat
   calls themselves are the same ones `scripts/many_splits.py` already runs on the
   node, but they are "unverified" in this folder.
2. **Voxel coverage is `--mode approx`.** The exact `voxel_cert.py` path
   back-projects every rendered pixel using the expected-depth buffer, which needs
   the GPU. Here the voxels are built from a decimated sample of the clean
   primitive centres (`prim_means`, stride recorded in `meta`) projected with the
   stored `c2w`/`K`, and a voxel's score is the max residual over the pixels those
   centres project onto. The world-space voxel hash, the quantile rule and the
   max-pooling are identical, so the *granularity comparison* is clean; absolute
   voxel coverage will differ from the paper's depth-based number.
3. **`--downsample > 1` changes pixel units.** Task patch sizes / tolerances and
   block sizes then refer to the coarse grid (`block_stored_px × factor ×
   downsample` recovers the capture-space size, recorded in every row).
4. **`prim_means` is a decimation**, not the full cloud (`--prim-sample`, default
   200 k points, stride in `meta`).

## Local verification (actually run, this machine, no GPU)

Synthetic fixture, real shapes (259×389, 18 views, 6 variants). Reproduce with

```powershell
pwsh -File experiments/local_verify.ps1     # ~5 min, writes experiments/artifacts/
python -m pytest experiments/tests/test_pipeline_cpu.py -q
```

Verbatim output (trimmed to the informative lines; full log in
`experiments/artifacts/_local_verify.log`):

```
=== 1/4 unit tests ===
ok   test_cq_matches_many_splits_reference
ok   test_dump_dryrun_schema
ok   test_inria_ply_roundtrip
ok   test_pixel_coverage_helper_matches_reference
ok   test_pup_dryrun_keeps_top30_and_roundtrips
ok   test_region_coverage_known_uniform_case
ok   test_second_task_recovers_known_shift
ok   test_split_perms_reproduce_reference
ok   test_task_sweep_known_hits_and_shortcut
ok   test_voxel_matrix_projection_and_pooling
10/10 passed

=== 2/4 dump_artifacts --dry-run (259x389, 18 views, 6 variants) ===
[23:50:39] dryrun_alpha: wrote experiments\artifacts\dryrun_alpha\dryrun_alpha.npz
           39.3MB (raw 48.0MB, 82% of raw) in 3.2s  shapes m=18 H=259 W=389 V=6

=== 3/4 make_pup_variant --dry-run (ranking + PLY round-trip) ===
  dry dryrun_pup: 200000 -> 60000 primitives, spearman(fisher,opacity)=+0.752,
      jaccard(topk)=0.516, wrote 6.0MB

=== 4/4 analyses on the synthetic fixture ===
[23:50:40] region_coverage: 1 npz, granularities=pixel,block,voxel blocks=64
           voxel=0.25 mode=approx splits=400
  dryrun_alpha: pixel done (100751 units/view)
  dryrun_alpha: block64 done (24 regions)
  dryrun_alpha: voxel done (voxel=0.250, 1846 voxels, 72% observed)
[23:51:00] WROTE experiments\artifacts\region_coverage_dryrun.json in 19.9s
  prune30  degradation: pixel=+44.4pp  block64=+92.7pp  voxel[counted_uncovered]=+74.5pp
  prune50  degradation: pixel=+38.7pp  block64=+92.7pp  voxel[counted_uncovered]=+69.2pp
  pup30    degradation: pixel=+32.4pp  block64=+92.7pp  voxel[counted_uncovered]=+61.5pp
  quant8   degradation: pixel=+21.1pp  block64=+92.7pp  voxel[counted_uncovered]=+49.0pp
  shdeg1   degradation: pixel=+16.3pp  block64=+92.7pp  voxel[counted_uncovered]=+40.1pp

[23:51:06] WROTE experiments\artifacts\second_task_dryrun.json in 5.4s
  clean    hit@tol=1.000 [0.999,1.000] n_views=18
  prune50  hit@tol=0.559 [0.536,0.580] n_views=18  delta=-0.441 [-0.464,-0.420]  +44.1pp
  prune30  hit@tol=0.282 [0.269,0.296] n_views=18  delta=-0.717 [-0.731,-0.704]  +71.7pp
  pup30    hit@tol=0.866 [0.854,0.877] n_views=18  delta=-0.134 [-0.146,-0.122]  +13.4pp
  shdeg1   hit@tol=0.998 [0.997,0.999] n_views=18  delta=-0.001 [-0.003,+0.000]   +0.1pp
  quant8   hit@tol=0.992 [0.990,0.994] n_views=18  delta=-0.008 [-0.010,-0.006]   +0.8pp

[23:55:02] WROTE experiments\artifacts\task_sweep_dryrun.json in 235.4s
  verify vs calib.downstream_task.task_success: 144 cells, 0 mismatches
  prune50  hit_clean=1.000 hit_edited=0.986 degradation=+1.4pp [+0.0,+12.0]  frac>0pp:0.33
  prune30  hit_clean=1.000 hit_edited=0.805 degradation=+19.5pp [+0.0,+74.1] frac>0pp:0.56
  pup30    hit_clean=1.000 hit_edited=0.999 degradation=+0.1pp [+0.0,+0.9]   frac>0pp:0.08
  shdeg1   hit_clean=1.000 hit_edited=1.000 degradation=+0.0pp                frac>0pp:0.00
  quant8   hit_clean=1.000 hit_edited=1.000 degradation=+0.0pp                frac>0pp:0.00
  stability.prune30: coverage_degradation=44.4pp, task_degradation=19.5pp,
      frac_configs_task_gt_coverage=0.25 (of 108 cells)
```

How to read this: the fixture is synthetic, so the *magnitudes* are meaningless —
what it demonstrates is that every stage runs end to end on CPU, that the schema
and sizes are as documented, that the bootstrap intervals are produced (all the
second-task intervals exclude 0 for the pruned variants), that the concentration
order is the intended one (`clean < pup30 < prune50 < prune30`), that the NCC
shortcut agrees with `task_success` on 144 (config × variant) cells with zero
mismatches, and that the block column saturates because the fixture's residuals are
uniform noise rather than a real render's structure. Real numbers come only from
the node artifacts.

