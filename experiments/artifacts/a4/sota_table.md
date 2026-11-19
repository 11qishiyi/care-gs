> **Gap, computed (M57, round 40).** At matched bytes we are **+2.02 dB** behind HAC (bicycle, 27.54 MB) and **+2.72 dB**
> behind PCGS (19.09 MB); +1.47 / +2.17 after the 0.55 dB protocol bias. At matched PSNR we have **no row**: our curve
> including the uncompressed model never reaches the published quality on either cross-paper scene. Full table and the
> interpolation rules in `experiments/GAP_REPORT.md` (`tools/gap_report.py`).
> **Protocol note (M55, round 38).** `bicycle` and `stump` reproduce the published 3DGS numbers within the 0.55 dB bias
> measured in M16, so they carry the cross-paper rows. **`bonsai` does not** (28.06 against a published 32.12) and is
> protocol-excluded: every bonsai row below is an internal comparison and must not be read against HAC/PCGS/3DGS.
> The rule is enforced by `tools/lint_protocol_claims.py` and `experiments/protocol_assets.py`.
# Our measured rows against the published operating points

Published numbers are transcribed from the papers (`experiments/published_3dgs.json`);
ours are measured file sizes (`zstd -12` + Morton order) and PSNR on the held-out
views.  The gap column is *theirs minus ours*, so a **positive number means we are
behind** at that size and a negative one means we lead.  The 0.55 dB protocol bias that
C1 measured is not folded into the gap; it is stated once, here.

## bicycle

| published | its MB | its PSNR | our best ≤ its size | our MB | our PSNR | gap dB |
|---|---|---|---|---|---|---|
| 3DGS | 1336.45 | 25.11 | `msc12-6-a1_c8_o8` (bicycle, m17) | 278.50 | 24.49 | **+0.62** |
| HAC | 27.54 | 25.05 | `vq12_c8_o8` (bicycle_k35s30_ft, m18) | 25.67 | 22.08 | **+2.97** |
| PCGS | 19.09 | 25.12 | `vq12_c8_o8` (bicycle_k25s30_ft, m18) | 18.40 | 21.50 | **+3.62** |

Our shelf on the base model of this scene (every coded variant, priced):

| variant | MB | rate × | PSNR | drop vs clean |
|---|---|---|---|---|
| `msc12-6-a1_c8_o8` | 278.50 | 5.20 | 24.49 | -0.09 pp |
| `c10_o8_sh3` | 153.73 | 9.41 | 24.33 | -0.26 pp |
| `c8_o8_sh3` | 148.30 | 9.76 | 24.30 | -0.34 pp |
| `vq12_c8_o8` | 72.17 | 20.05 | 23.86 | -1.74 pp |
| `m16_o8_sh2` | 111.07 | 13.03 | 22.96 | -4.26 pp |

## stump

| published | its MB | its PSNR | our best ≤ its size | our MB | our PSNR | gap dB |
|---|---|---|---|---|---|---|
| 3DGS | 1070.92 | 26.66 | `msc12-6-a1_c8_o8` (stump_mirror, m16) | 228.20 | 26.11 | **+0.55** |
| HAC | 18.11 | 26.58 | `p30_vq12_c8_o8` (stump_mirror, m16) | 17.61 | 20.33 | **+6.25** |
| PCGS | 13.49 | 26.61 | `p10_vq12_c8_o8` (stump_mirror, m16) | 5.89 | 16.63 | **+9.98** |

---

# M22: one colour basis for six million Gaussians

Measured file sizes (`zstd -12` + Morton, container path) and PSNR on the held-out views.
The shelf row is the 45-independently-coded-coefficients variant the basis replaces;
`bits` is the colour block's budget per primitive, i.e. the number the round turns.

## bicycle

| plan | colour bits | file | B/primitive | PSNR | ratio | vs shelf |
|---|---|---|---|---|---|---|
| r=16 | 96 | 136.81 MB | 22.31 | 24.32 | 10.58x | -0.01 dB |
| r=16 | 64 | 106.18 MB | 17.32 | 24.28 | 13.63x | -0.05 dB |
| r=32 | 64 | 108.40 MB | 17.68 | 23.71 | 13.35x | -0.62 dB |
| r=16 | 48 | 98.53 MB | 16.07 | 24.12 | 14.69x | -0.21 dB |
| r=16 | 40 | 95.22 MB | 15.53 | 23.67 | 15.20x | -0.66 dB |
| r=16 | 32 | 92.10 MB | 15.02 | 22.98 | 15.71x | -1.35 dB |
| shelf `c10_o8_sh3` (45 x 3 bit) | 165 | 144.55 MB | 23.57 | 24.33 | 10.01x | -- |

Pre-registered L1 window (within 0.35 dB of the shelf): best point **r=16, 48 bits -> 98.53 MB, 14.69x, -0.21 dB**.

## stump

| plan | colour bits | file | B/primitive | PSNR | ratio | vs shelf |
|---|---|---|---|---|---|---|
| r=16 | 64 | 86.84 MB | 17.50 | 25.73 | 13.49x | -0.08 dB |
| r=16 | 48 | 80.72 MB | 16.27 | 25.57 | 14.51x | -0.24 dB |
| shelf `c10_o8_sh3` (45 x 3 bit) | 165 | 118.88 MB | 24.42 | 25.81 | 9.85x | -- |

Pre-registered L1 window (within 0.35 dB of the shelf): best point **r=16, 48 bits -> 80.72 MB, 14.51x, -0.24 dB**.

---

# M23-M24: the same colour, cheaper geometry and a container without waste

Measured file sizes (zstd -12 + Morton, container path) and PSNR on 25 held-out views
(1236x822).  Every row is the same rank-16 colour basis at 48 bits per primitive; the rounds
change geometry coding and the container, never the code words.  Clean = 1447 MB / 24.52 dB.

## bicycle

| plan | what changed | file | B/prim | PSNR | ratio |
|---|---|---|---|---|---|
| `c10_o8_sh3` r16/48 | M22 shelf (32-bit quats, 8-bit attrs, 10-bit positions) | 98.53 MB | 16.07 | 24.12 | 14.69x |
| `gp8-8-8_c10_sh3` r16/48 | smallest-three quaternions (26 bits) | 93.30 MB | 15.22 | 24.12 | 15.51x |
| `gp8-8-8_c10_sh3` r16/48 | + one SH scale level (a byte nothing read, N32) | 89.72 MB | 14.63 | 24.12 | 16.13x |
| `gp8-6-6_c10_sh3` r16/48 | + 6-bit scales and opacity | 85.71 MB | 13.98 | 24.09 | 16.88x |
| **`gp8-6-6_c9_sh3` r16/48** | **+ 9-bit positions (ships)** | **83.41 MB** | **13.60** | **24.08** | **17.35x** |

Decode 11.80 s, encode 51 s, peak decode RSS 7.4 GB on the shipping row before M25.

---

# M25: decoder footprint

| | bicycle, `gp8-6-6_c9_sh3` r16/48 |
|---|---|
| file | 83.41 MB (17.35x) |
| primitives | 6,131,954 |
| encode | 51 s |
| decode | **7.69 s** (was 11.80) |
| peak decode RSS | **1.97 GB** (was 7.41) |
| decoded tensors | 1447 MB (float32) |
| PSNR | 24.08 dB (clean 24.52) |

The bitstream did not change; only the decoder's dtypes and chunking did.

## Mid-rate (bicycle, published model pruned to 25 %)

| method | file | PSNR | note |
|---|---|---|---|
| HAC | 27.54 MB | 25.05 | published |
| PCGS | 19.09 MB | 25.12 | published |
| this work (M26, factor 4) | 24.96 MB | 21.24 | 1,532,988 prims, r16/64 bit colour |
| this work (M26, factor 4) | 20.96 MB | 21.10 | r16/48 bit, gp8-6-6_c9_sh3 |
| this work (M26, factor 2) | 24.91 MB | 21.19 | supervision doubled: -0.05 dB vs factor 4 |

The two arms differ only in supervision resolution; factor 2 costs 3.1x the wall time and buys nothing
(M26, N33).  The mid-rate row is representation-bound, not training-bound.

## Mid-rate, second attempt: anchor representation (M27, full 6.13 M model, no fine-tuning)

| method | file | B/prim | PSNR | note |
|---|---|---|---|---|
| HAC | 27.54 MB | — | 25.05 | published |
| PCGS | 19.09 MB | — | 25.12 | published |
| this work (M26, prune 25 % + finetune) | 24.96 MB | — | 21.24 | 1,532,988 prims |
| this work (M27, anchors ppa 16, 3-bit offsets) | 15.42 MB | 2.52 | 13.86 | constant sharing |
| this work (M27, anchors ppa 8, 3-bit offsets) | 21.75 MB | 3.55 | 16.05 | constant sharing |
| this work (M27, anchors ppa 8, 4-bit offsets) | 24.07 MB | 3.93 | 16.97 | constant sharing |
| this work (M27, anchors ppa 8, 5-bit offsets) | 34.23 MB | 5.58 | 17.77 | constant sharing |
| this work (M27, scale/rotation/opacity per primitive, 5-bit offsets) | 69.19 MB | 11.28 | 21.58 | only colour shared |
| this work (M28, anchors + offset-conditioned predictor, DC 4) | 27.13 MB | 4.42 | 17.04 | +0.08 dB over constant |
| this work (M28, anchors + offset-conditioned predictor, DC 6) | 33.57 MB | 5.47 | 17.05 | +0.08 dB over constant |

The anchor bookkeeping is 3.8x cheaper per primitive than our own shelf (2.52 vs 13.60 B/prim) and
renders 4.3 dB below pruning at equal bytes: constant sharing is not the mechanism that wins this row.
The measured attribution is position quantum 1.72 dB, constant scale 2.46 dB, constant opacity 0.29 dB,
constant rotation 0.09 dB, shared rest colour ~2 dB at equal bytes (M27, N34).  The predictor M27
pointed at was built in M28 and bought **+0.08 dB** at the same grid: the anchor mean explains only
R² = 0.63 / 0.38 / 0.60 of scale / opacity / rotation variance at 8 primitives per voxel, so the rest
is not in any input the decoder has (M28, N35).  Three post-hoc explanations of the mid-rate gap are
now priced and excluded -- supervision (N33), anchor representation (N34), predictor (N35) -- and what
remains is a jointly trained decoder with learned latents, which this pipeline does not have.

---

# M24 / M25 / M29: the near-lossless point, and what moved it

Same scene (bicycle, 6,131,954 primitives), same 25 held-out views, same container path.  `ratio` is
1447 MB (the fp32 model as the renderer loads it) over the file.  The uncompressed model renders
**24.52 dB**; that number is the ceiling of this table, not a baseline to beat.

| point | spec | file | B/prim | ratio | PSNR | decoder |
|---|---|---|---|---|---|---|
| M22 basis (r16/48) | `c10_o8_sh3` | 98.53 MB | 16.07 | 14.69x | 24.12 | 7.7 s / 2.0 GB |
| M24 shipping | `gp8-8-8_c10_sh3` + o6 + c9 | 83.41 MB | 13.60 | 17.35x | 24.08 | 7.69 s / 1.97 GB |
| **M29 shipping** | **`gp6-6-6_c8_sh3`** | **76.56 MB** | **12.49** | **18.90x** | **24.06** | **7.51 s / 1.96 GB** |

The M29 sweep (registered as an amendment after the entropy probe, before any number existed):

| spec | file | B/prim | ratio | PSNR | SSIM |
|---|---|---|---|---|---|
| `gp8-8-8_c9` | 87.43 MB | 14.26 | 16.55x | 24.11 | 0.7439 |
| `gp7-7-7_c9` | 85.64 MB | 13.97 | 16.90x | 24.10 | 0.7433 |
| `gp6-6-7_c8` | 77.43 MB | 12.63 | 18.69x | 24.06 | 0.7395 |
| `gp6-6-6_c8` | 76.56 MB | 12.49 | 18.90x | 24.06 | 0.7393 |

Why the curve is shallow where it is: the attribute streams are already at their entropy
(`experiments/m29_entropy.py`), so a nominal bit removed is not a bit saved — zstd spends 6.67 bits on
8-bit scale codes, so dropping to 7 bits recovers ~0.6.  The one number that was pure choice is the
10-bit position offset, which codes at exactly 10.00 bits; 10 -> 8 bits is 1.5 B/primitive on its own.

### the position block, and why its width is not a free parameter (M30)

| allocation | file | ratio | PSNR |
|---|---|---|---|
| fixed 8-bit grid over the local cluster box (shipping) | 76.56 MB | 18.90x | 24.06 |
| constant absolute step, one bit coarser | 75.56 MB | 19.14x | 23.89 |
| constant absolute step, 1.8 bits coarser | 73.37 MB | 19.72x | 23.48 |
| budget-neutral tilt toward the dense clusters | 76.76 MB | 18.85x | 23.98 |
| budget-neutral tilt toward the sparse clusters | 76.71 MB | 18.86x | 24.03 |

With a fixed width the absolute error is proportional to the cluster extent at every density (ratio
0.00134 in all four size quartiles).  That is a rate allocation in units of local primitive spacing, and
every alternative measured at the same or smaller byte count was worse.

### the same configuration on three scenes (M31)

One container, nothing re-tuned.  `ratio` is the 236 B/primitive payload over the file; the as-shipped
fp32 PLY carries 12 B of normals per primitive, so the file-based ratio is 0.5-1.0x higher.

| scene | primitives | file | B/prim | ratio | clean dB | ours dB | delta | SSIM | dec s / RSS GB |
|---|---|---|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 76.56 MB | 12.49 | 18.90x | 24.52 | 24.06 | -0.46 | 0.7393 | 7.49 / 1.96 |
| stump | 4,961,797 | 62.59 MB | 12.61 | 18.71x | 26.15 | 25.52 | -0.63 | 0.7432 | 6.00 / 1.60 |
| bonsai | 1,244,819 | 15.30 MB | 12.29 | 19.20x | 28.06 | 27.08 | -0.98 | 0.8868 | 1.39 / 0.47 |

The rate transfers (12.3-12.6 B/primitive on all three) because the per-stream shares do: `sh_coef`
24.3-24.5 %, `cluster_off` 23.7-24.3 %, rotation 17.8-18.1 %, scales 15.8-16.3 % across a 5x range of
primitive counts.  The distortion does not, and it is not a rate effect -- re-encoding bonsai at the
generous end of the M29 scan costs 17 % more bytes for +0.11 dB (27.08 -> 27.19).  Quote the delta per
scene; a single "<=0.5 dB at 19x" sentence is a bicycle measurement generalised one scene too far.

### the colour block: subspace or quantiser? (M32)

Same container, same geometry, raw colour budget held at 48 bits per primitive; `r16_b64` is the rate
control.  Deltas are against the same-round `r16_b48` control.

| plan | bicycle | stump | bonsai |
|---|---|---|---|
| `r16_b48` (shipping) | 76.56 MB / 18.90x / 24.06 | 62.59 MB / 18.71x / 25.52 | 15.30 MB / 19.20x / 26.70 |
| `r24_b48` | 23.37 (-0.69) | 24.51 (-1.01) | 25.84 (-0.86) |
| `r32_b48` | 22.63 (-1.43) | 23.74 (-1.78) | 24.79 (-1.91) |
| `r8_b48` | 23.65 (-0.41) | 25.12 (-0.40) | 26.72 (+0.02) |
| `r16_b64` | 24.22 (+0.16) | 25.68 (+0.16) | 27.02 (+0.32) |

More subspace at the same bytes is worse on all three scenes; more bits inside the same subspace is the
only move that pays.  Note that "same raw bits" is not "same file": the four 48-bit plans compress to
18.58/20.08/22.01/29.25 MB on bicycle because 6-bit codes are a near-uniform 64-symbol alphabet where
3-bit codes are a skewed 8-symbol one.

The choice can be made offline, but only with a metric that charges truncation:

| plan | coef error vs original 45 cols (bicycle / stump / bonsai) | in-subspace error |
|---|---|---|
| `r16_b64` | 28.73 / 35.82 / 35.50 % | 22.70 / 23.30 / 23.31 % |
| `r16_b48` | 50.65 / 55.49 / 55.37 % | 48.10 / 49.92 / 49.97 % |
| `r8_b48` | 54.82 / 59.81 / 51.88 % | 6.55 / 6.85 / 7.44 % |
| `r24_b48` | 86.87 / 105.03 / 93.64 % | 86.69 / 105.18 / 93.41 % |
| `r32_b48` | 119.49 / 136.63 / 131.72 % | 119.58 / 136.96 / 132.08 % |

Full-column error vs render PSNR: Spearman **-1.000** on all three scenes.  In-subspace error vs PSNR:
-0.70 / -0.70 / -0.90 -- it ranks the rank-8 plan first, the plan that discards 21-28 % of the energy.

## Robustness: what a damaged file renders at (M33)

Same shipping container (`gp6-6-6_c8_sh3`, rank-16 basis, 48-bit coefficients), 25 held-out views,
11 conditions per scene, decoded with `read_container(tolerant=True)` and rendered through the same path
as every other row.

| scene | file | control | 0.10 % burst | 1.0 % burst | 5.0 % burst | prefix 50 % | prefix 90 % |
|---|---|---|---|---|---|---|---|
| bicycle | 76.56 MB | 24.06 | 23.37 (-0.69) | 23.37 | 22.26 (-1.80) | 9.25 | 22.71 |
| stump | 62.59 MB | 25.52 | 24.67 (-0.85) | 24.67 | 24.25 (-1.27) | 11.27 | 23.31 |
| bonsai | 15.30 MB | 27.08 | 23.44 (-3.64) | 23.44 | 23.44 | 8.87 | 25.53 |

* **Geometry survives every corruption**: `means`, `scales`, `opacities`, `quats` are byte-identical to
  the control in all 33 mechanical reports (0.00 % changed).
* **Frame size, not damage fraction, sets the granularity**: with 4 MB frames, 0.1-1 % destroys one frame,
  2 % two, 5 % three.  bonsai's colour block is a single frame, so no corruption below 5 % can cost it
  less than -3.64 dB.
* **Cost of a damaged decode**: 11.28 s / 2.08 GB against 11.28 s / 2.01 GB intact (time 1.00x, peak
  1.03x); a truncated file is cheaper (7.4 s) because there is less to decode.
* **Truncation is a cliff, then a ladder**: below ~75 % the render is empty (a zero scale covers no
  pixels), above it 17.22 / 16.05 / 10.29 dB at 75 % rising to 22.71 / 23.31 / 25.53 dB at 90 %.
  Reordering the streams colour-first does not move the cliff (measured, `tools/m33_reorder.py`).

## Robustness with the frame boundary moved (M34, bonsai)

Same container and configuration, `MIN_FRAME` swept; all three arms decode to the identical model
(sha1 over every array), so the only difference is where the frame boundaries fall.  16 held-out views.

| `MIN_FRAME` | file | vs shipping | `sh_coef` frames | decode | peak RSS | control | 0.10 % burst | 1.0 % burst | 5.0 % burst |
|---|---|---|---|---|---|---|---|---|---|
| 4 MB (shipping) | 15,302,362 B | — | 2 | 1.63 s | 0.66 GB | 27.06 | 23.97 (-3.09) | -3.09 | -3.09 |
| 1 MB | 15,352,658 B | +0.36 % | 8 | 1.63 s | 0.66 GB | 27.06 | 25.78 (-1.28) | -1.28 | 24.79 (-2.27) |
| 256 KB | 15,297,691 B | **-0.03 %** | 29 | 1.66 s | 0.66 GB | 27.06 | **26.92 (-0.14)** | 25.62 (-1.44) | 25.43 (-1.63) |

* **The smallest detectable corruption falls 22x for 0.03 % fewer bytes**: 3.09 dB -> 0.14 dB, decode
  time 1.02x, peak RSS 1.00x.  The 4 MB frame was a format default, not a property of the format.
* **Cost tracks the fraction of the colour block a frame covers, not the byte count**: bonsai's 4.19 MB
  `sh_coef` is ~96 % of a 4 MB frame (-3.09 dB), ~24 % of a 1 MB frame (-1.28), ~6 % of a 256 KB frame
  (-0.14).  This is why M33's floor was scene-specific: 4 MB is 5 % of bicycle's colour budget and all of
  bonsai's.
* **bicycle and stump at 1 % with 256 KB frames: not measured** (their models exceeded this round's
  download budget; the row is marked not measured rather than extrapolated).


## The rate-distortion curve (M35, round 31) — two scenes, six configurations, one run

Everything above is a point. This is the curve those points sit on. Same node, same code, same day; the
configuration is varied only through the pre-registered ladder in `tools/m35_spec.md`; no retraining, no
per-scene tuning.

**bicycle** — 6,131,954 primitives, 25 held-out views, clean model 24.52 dB, payload 1447.1 MB (236 B/prim)

| file | B/prim | ratio | PSNR | Δ vs clean | on the frontier |
|---|---|---|---|---|---|
| 76.56 MB | 12.49 | 18.90× | 24.06 | −0.46 | yes |
| 69.34 MB | 11.31 | 20.87× | 23.80 | −0.72 | yes |
| 66.24 MB | 10.80 | 21.85× | 23.60 | −0.92 | yes |
| 57.23 MB | 9.33 | 25.28× | 22.53 | −1.99 | yes |
| 55.18 MB | 9.00 | 26.22× | 21.82 | −2.70 | yes |
| 69.30 MB | 11.30 | 20.88× | 22.82 | −1.70 | **no — dominated** |

**stump** — 4,961,797 primitives, 16 views, clean 26.15 dB, payload 1171.0 MB

| file | B/prim | ratio | PSNR | Δ vs clean | on the frontier |
|---|---|---|---|---|---|
| 62.59 MB | 12.61 | 18.71× | 25.52 | −0.63 | yes |
| 56.72 MB | 11.43 | 20.65× | 25.30 | −0.85 | yes |
| 54.41 MB | 10.96 | 21.52× | 25.04 | −1.11 | yes |
| 47.46 MB | 9.57 | 24.67× | 24.42 | −1.73 | yes |
| 45.75 MB | 9.22 | 25.60× | 22.32 | −3.83 | yes |
| 56.77 MB | 11.44 | 20.63× | 22.70 | −3.45 | **no — dominated** |

Fits over the four `sh3` points: bicycle **+3.74 dB per doubling** (R² 0.942; 23.0 dB at 61.1 MB, 24.0 dB at
73.5 MB); stump **+2.83 dB per doubling** (R² 0.971; 23.0 dB at 33.2 MB, 24.0 dB at 42.3 MB).

Two sentences for the text:

* **The floor of this format is 45–55 MB at fixed primitive count**, and the cheapest point is already
  9.00 B/primitive of which 7.97 B is geometry. HAC (27.54 MB) and PCGS (19.09 MB) are budgets that require
  a model with fewer Gaussians, not a finer quantiser — which is what M26's prune-and-fine-tune pipeline
  does, and where the remaining 3.8–4.0 dB gap lives.
* **SH degree is dominated at equal bytes**, in both scenes: a degree-2 container is within 0.06–0.09 % of a
  degree-3 container's size and 1.02–2.60 dB below it. Cutting quaternion/scale/opacity widths instead buys
  the same bytes for 0.22–0.26 dB.

## The mid-rate point, with the rate in the loss (M36, round 32)

Prune the published bicycle model to 25 % (1,532,988 primitives), fine-tune 12k steps at factor 4, encode at
the shipping configuration. The only difference between the rows is the loss:

| arm | loss | container | B/prim | PSNR | SSIM |
|---|---|---|---|---|---|
| a | `0.8 L1 + 0.2 (1−SSIM)` | 19,272,155 B | 12.574 | 21.07 | 0.5166 |
| **b** | + log rate term at a 5 % gradient share | **17,959,298 B** | **11.715** | **21.24** | 0.5279 |
| c | + L2 control at the same share | 18,381,419 B | 11.990 | 21.19 | 0.5281 |
| d | + log rate term at a 15 % share | 17,482,803 B | 11.404 | 21.09 | 0.5200 |

Published comparisons at these budgets: **HAC 27.54 MB / 25.05 dB**, **PCGS 19.09 MB / 25.12 dB**. We are
6 % below PCGS's bytes and 3.9 dB below its PSNR — the gap is unchanged by this round, and it is a gap in
the *model* (a 25 %-pruned one), not in the container or the loss.

* **The pressure is a Pareto gain**: b is 6.8 % smaller than a and 0.17 dB better, at 1.11× the wall clock.
* **The logarithm is not what pays**: the L2 control at the same gradient share is within 0.05 dB and 2.4 %
   of the log arm, so what the pressure buys is shrinkage of the parameter distribution towards the
   quantiser grid, not entropy shaping.
* **The knee is below a 15 % gradient share**: d saves another 2.7 % of bytes and gives back 0.15 dB.

## The codebook, at equal bytes (M38, round 34)

| k | container | PSNR | SSIM |
|---|---|---|---|
| 4096 | 54.61 MB | 19.58 | 0.5149 |
| 16384 | 56.34 MB | 19.61 | 0.5270 |
| 65536 | 58.60 MB | 20.36 | 0.5587 |
| scalar `gp6-6-6_c8_sh3` (baseline) | 76.56 MB | 24.06 | 0.7393 |
| scalar, same 58.6 MB (M35 curve) | 58.6 MB | ≈ 22.6 | — |

* **The joint codebook is 2.2 dB below the scalar frontier at its own size.** Sizes fall by 18–22 MB; quality
  falls by 3.7 dB against the baseline, and against the curve at equal bytes the codebook loses.
* **Sixteen times the centroids buys 0.78 dB for 4 MB** — the curve is flat in the direction that matters.
* **The residual is scale error**: RMSE 0.28 in log units at k = 65536 (a 32 % scale error), which is a
  consequence of 93 points per 8-D cell rather than of the coder.
* With M29 this closes the family "reduce the number of symbols per primitive"; the bytes are in the count of
  primitives, not in their description.

### The extreme-rate corner (M39, round 22)

Same format, same code path, bicycle, 25 held-out views; pruning prefix 25/15/10 % with the rate pressure in
the loss. Ratios use the 1447.1 MB payload of the published model.

| keep | container | B/prim | ratio | PSNR | Δ vs clean (24.52) |
|---|---|---|---|---|---|
| 25 % (M36) | 17.96 MB | 11.72 | 80.6× | 21.24 | −3.28 |
| 15 % | 10.82 MB | 11.77 | 133.71× | 20.12 | −4.40 |
| 10 % | 7.24 MB | 11.81 | 199.80× | 19.02 | −5.50 |

The pressure's saving is constant (5.5–6.8 % of bytes) and its dB gain shrinks with depth (+0.17 → +0.02),
so the lever is a rate knob, not a quality one.

### Deployment (M40, round 23): one configuration, three scenes

| scene | container | B/prim | ratio | PSNR (clean) | encode | decode | peak RSS | 0.1 % burst (256 KB) |
|---|---|---|---|---|---|---|---|---|
| bicycle | 76.60 MB | 12.49 | 18.90× | 24.06 (24.52) | 142 s | 7.84 s | 1.96 GB | 24.00 |
| stump | 62.65 MB | 12.63 | 18.71× | 25.52 (26.15) | 98 s | 6.38 s | 1.60 GB | 25.33 |
| bonsai | 15.30 MB | 12.29 | 19.20× | 27.08 (28.06) | 27 s | 1.49 s | 0.47 GB | 26.73 |

Shipping default since M40: 256 KB frames, which cost +0.05 / +0.09 / −0.03 % of the file and bound a lost
frame's damage at 0.35 dB instead of 3.64 dB.

### Encode cost (M41, round 24)

| scene | build (streams) | write serial | write 4 workers | encode end to end (4 workers) |
|---|---|---|---|---|
| bicycle | 58.9 s | 11.31 s | 3.21 s | 142 s |
| stump | 137.7 s | 8.71 s | 2.55 s | 98 s |
| bonsai | 21.2 s | 2.61 s | 0.70 s | 27 s |

The writer's pool is byte-neutral (md5 identical at 1/2/4/8 workers) and 3.4–3.7× on the write, which is 16 %
of the job; stream construction dominates (84–94 %) and peaks at 18.8 GB RSS on bicycle.

### Encoder memory and build cost (M42, round 25)

| scene | build, before | build, after | peak RSS, before | peak RSS, after | container |
|---|---|---|---|---|---|
| bicycle | 190.1 s | 150.1 s | 18.38 GB | 11.63 GB | md5 identical, 76,598,203 B |
| stump | 127.2 s | 103.9 s | 14.94 GB | 9.51 GB | md5 identical, 62,649,653 B |
| bonsai | 21.4 s | 19.9 s | 4.07 GB | 2.78 GB | md5 identical, 15,297,685 B |

Same node, same model, same `--jobs 4`; the change is byte-neutral (sliced SH quantiser and bit-packer). Remaining
memory is live data: float64 attribute arrays 4.5 GB (SH rest 2.21 GB), int64 code array 2.21 GB, three layout
candidates 0.5 GB. Absolute encode times vary 2.5× across hosts, so only same-node A/B is evidence.

## Encoder cost (M43 + M44)

| scene | legacy | M42 | M43 | M44 | peak (M44) | container |
|---|---|---|---|---|---|---|
| bicycle | 189.6 s / 18.38 GB | 135.8 / 11.66 | 126.9 / 11.65 | **108.9 / 9.60** | 9.60 GB | 76,598,203 B |
| stump | 139.7 / 14.94 | 156.3 / 9.52 | 89.9 / 9.49 | **82.6 / 7.83** | 7.83 GB | 62,649,653 B |
| bonsai | 21.5 / 4.07 | 19.9 / 2.92 | 18.8 / 2.70 | **19.0 / 2.27** | 2.27 GB | 15,297,685 B |

Same node, same session, one process per encode; `--jobs 4` throughout. The file is identical for all four variants, so
the only thing these rounds changed is what the encoder costs to run. Encoding is now 1.74× faster than pre-M42 on
bicycle with 48 % less peak memory, and the decode side is untouched (M25: 7.49 s, 1.96 GB).

## Mid-rate with the pruning score fixed (M47)

| scene | method | bytes | PSNR | SSIM | note |
|---|---|---|---|---|---|
| bicycle | PCGS (quoted) | 19.09 MB | 25.12 | — | trained from scratch with rate-aware pruning |
| bicycle | HAC (quoted) | 27.54 MB | 25.05 | — | learned proxy + entropy model, retrained |
| bicycle | ours, M26 volume prune | 19.34 MB | 21.08 | 0.517 | post-hoc, 12k finetune |
| bicycle | **ours, M47 saliency prune** | **19.45 MB** | **22.67** | **0.681** | post-hoc, 800-step saliency pass + 12k finetune |

The saliency pass is 800 steps (~110 s on an A100) and produces one float per primitive; pruning then keeps the top 25 %
of it. No retraining from scratch and no learned entropy model, so the comparison is not like-for-like in cost — it is
like-for-like in bytes, which is the axis this table is about.

## Mid-rate, three scenes, two seeds: the saliency score is a method (M48)

Equal-bytes pairs only (the saliency container is re-encoded with a smaller colour budget when it comes out larger).
Ratios use the series' 236 B/primitive payload convention.

| scene | arm | bytes | B/prim | ratio | PSNR | SSIM | colour budget |
|---|---|---|---|---|---|---|---|
| bicycle seed 1 | volume | 19.34 MB | 12.62 | 74.4× | 21.08 | 0.517 | 48 bit |
| bicycle seed 1 | **saliency** | 19.45 MB | 12.67 | 74.0× | **22.67** | 0.681 | 40 bit |
| bicycle seed 2 | volume | 19.34 MB | 12.62 | 74.4× | 21.07 | 0.516 | 48 bit |
| bicycle seed 2 | **saliency** | 19.43 MB | 12.67 | 74.1× | **22.58** | 0.680 | 40 bit |
| stump | volume | 15.49 MB | 12.49 | 75.6× | 20.35 | 0.391 | 48 bit |
| stump | **saliency** | 15.12 MB | 12.19 | 77.4× | **23.52** | 0.675 | 32 bit |
| bonsai | volume | 3.94 MB | 12.65 | 74.6× | 24.10 | 0.768 | 48 bit |
| bonsai | **saliency** | 3.99 MB | 12.83 | 73.6× | **25.74** | 0.858 | 40 bit |

Gains **+1.51 / +1.59 / +1.64 / +3.17 dB** at equal bytes; the two bicycle seeds agree to 0.08 dB, so the original
M47 number was not a seed artefact. Nothing is tuned per scene: the same 800-step saliency pass, the same 25 % keep,
the same 12k finetune, the same container spec.

The gain does not come from the starting point. On stump both pruned sets render at 20.6–20.9 dB before finetuning,
but at SSIM 0.408 (volume) vs 0.726 (saliency), and across 12k steps the volume set moves −0.02 dB while the saliency
set moves +5.00 dB. What the score selects is a set that is still **trainable**; the pre-finetune render cannot see it
(M48, T3 failed on stump while the outcome test passed by 3.17 dB).
## Mid-rate container loss, measured properly (M49, round 32)

The container costs **0.39 dB** on the saliency-pruned model at 48-bit colour (23.26 dB raw → 22.87 dB in 20.56 MB,
bicycle, 25 held-out views, same probe and factor). The 1.83 dB figure that circulated in M47/M48 was a factor-4
training-view eval against a factor-1 held-out render; the same model's factor-4 render is 18.71 dB, i.e. the protocol
gap is 4.55 dB. Equal-bytes row: **19.47 MB / 22.63 dB / SSIM 0.681** (40-bit colour), which reproduces M48's
19.45 MB / 22.67 dB within 0.04 dB.

| colour bits | file | PSNR | SSIM |
|---|---|---|---|
| raw (no container) | 236 B/prim | 23.26 | 0.7334 |
| 96 | 30.78 MB | 23.04 | 0.7165 |
| 64 | 22.91 MB | 23.01 | 0.7130 |
| 48 (shipping) | 20.56 MB | 22.87 | 0.6999 |
| 40 | 19.47 MB | 22.63 | 0.6808 |
| 32 | 18.35 MB | 21.94 | 0.6415 |

Measured attribution: geometry 9.16 of 13.60 B/primitive (67 %), colour 4.34 B (32 %) — corrected 2026-11-17 13:20. Against PCGS (19.09 MB /
25.12 dB) the deficit is therefore a model/primitive-count deficit, not a coding one.

## Geometry precision at mid-rate, priced field by field (M50, round 33)

Same model and protocol as the M49 table above (bicycle, 1,532,988 primitives, 48-bit colour, 25 held-out views,
factor 1). Only the geometry code changes between rows.

| spec | file | MB | PSNR | SSIM | Δ bytes |
|---|---|---|---|---|---|
| `gp6-6-6_c8` (shipping) | 20,561,912 | 20.56 | 22.87 | 0.6999 | — |
| `gp6-6-4_c8` (opacity 4) | 20,073,993 | 20.07 | **22.88** | 0.6955 | **−2.37 %** |
| `gp6-6-6_c7` | 19,990,939 | 19.99 | 22.76 | 0.6884 | −2.78 % |
| `gp6-6-6_c6` | 19,410,087 | 19.41 | 22.43 | 0.6563 | −5.60 % |
| `gp4-6-6_c8` (quat 4) | 19,228,871 | 19.23 | 22.58 | 0.6839 | −6.48 % |
| `gp6-4-6_c8` (scales 4) | 19,011,806 | 19.01 | 21.96 | 0.6675 | −7.54 % |
| `gp4-4-4_c8` | 17,190,847 | 17.19 | 21.65 | 0.6440 | −16.40 % |
| `gp4-4-4_c6` | 16,039,022 | 16.04 | 21.36 | 0.6079 | −22.00 % |

Verdict `shipping_spec_is_at_its_rate`; the one shippable change is **4-bit opacity**, worth −2.37 % bytes at +0.01 dB
(M51 tests it on the unpruned near-lossless row, three scenes).

## Opacity bit-width at the near-lossless end (M51, round 34)

Three untouched published models, spec `gp6-6-{6,4}_c8_sh3`, 48-bit colour, same probe and views:

| scene | 6-bit opacity | 4-bit opacity | Δ bytes | Δ dB | Δ SSIM |
|---|---|---|---|---|---|
| bicycle | 76,598,203 B / 24.06 dB / 18.90× | 74,802,867 B / 23.95 / 19.35× | −2.35 % | −0.11 | −0.0063 |
| stump | 62,649,653 B / 25.52 / 18.71× | 61,191,922 B / 25.41 / 19.14× | −2.33 % | −0.11 | −0.0064 |
| bonsai | 15,297,685 B / 27.08 / 19.20× | 14,927,795 B / 26.97 / 19.68× | −2.42 % | −0.11 | −0.0044 |

Verdict `not_free_but_cheapest`: the byte costs 0.11 dB everywhere (M50's "+0.01 dB" was a property of the pruned
model), but at 0.047 dB per 1 % it is still three times cheaper than cutting the colour block. The shipping row stays
at 6-bit opacity; 4-bit is documented as the rate knob.
