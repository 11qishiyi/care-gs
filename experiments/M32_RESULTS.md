# M32 — the colour block's residual: rank, bits, or neither

Pre-registered in `tools/m32_spec.md` at 10:10 on 2026-11-16, before any M32 measurement.  Node 2140760
(A100-PCIE-40GB, ¥2.80/h), rented 10:07, released 11:50.  Three scenes, five plans each, 15 containers,
15 renders.

## What was asked

M31 left the near-lossless container 0.46 / 0.63 / 0.98 dB below the clean model on bicycle / stump /
bonsai and showed that paying 17 % more bytes at the *same* rank returns only 0.11 dB — so the residual
lives in the colour block (a shared rank-16 basis, 48 bits of coefficient per primitive) rather than in
the rate.  N38 named the open question without answering it: is the residual a **rank** deficiency (16
dimensions cannot hold bonsai's colour) or a **bits** deficiency (those 16 dimensions are quantised too
coarsely)?

Four plans hold the raw colour budget at 48 bits per primitive — 6.0 B of coefficients plus 1 B of level —
and trade subspace against precision; a fifth doubles the budget at the winning rank as the rate control.

| plan | rank | colour budget | colour bytes / primitive |
|---|---|---|---|
| `r16_b48` (control) | 16 | 48 bit | 7.0 |
| `r24_b48` | 24 | 48 bit | 7.0 |
| `r32_b48` | 32 | 48 bit | 7.0 |
| `r8_b48` | 8 | 48 bit | 7.0 |
| `r16_b64` (rate control) | 16 | 64 bit | 9.0 |

## Measurements

`ratio` is the 236 B/primitive payload over the file.  `Δ` is against the same-round control, which is
the only comparison that survives the cross-node note below.

**bicycle** (6,131,954 primitives, 25 held-out views, clean 24.52 dB)

| plan | file | B/prim | ratio | PSNR | Δ vs control | bytes vs control |
|---|---|---|---|---|---|---|
| `r16_b48` | 76.56 MB | 12.49 | 18.90× | **24.06** | — | — |
| `r16_b64` | 84.22 MB | 13.73 | 17.18× | **24.22** | **+0.16** | +10.0 % |
| `r24_b48` | 78.06 MB | 12.73 | 18.54× | 23.37 | −0.69 | +2.0 % |
| `r32_b48` | 79.99 MB | 13.05 | 18.09× | 22.63 | −1.43 | +4.5 % |
| `r8_b48` | 87.22 MB | 14.22 | 16.59× | 23.65 | −0.41 | +13.9 % |

**stump** (4,961,797, 16 views, clean 26.15 dB)

| plan | file | ratio | PSNR | Δ vs control | bytes vs control |
|---|---|---|---|---|---|
| `r16_b48` | 62.59 MB | 18.71× | **25.52** | — | — |
| `r16_b64` | 68.70 MB | 17.04× | **25.68** | **+0.16** | +9.8 % |
| `r24_b48` | 64.49 MB | 18.16× | 24.51 | −1.01 | +3.0 % |
| `r32_b48` | 66.07 MB | 17.72× | 23.74 | −1.78 | +5.6 % |
| `r8_b48` | 70.10 MB | 16.70× | 25.12 | −0.40 | +12.0 % |

**bonsai** (1,244,819, 167 views, clean 28.06 dB)

| plan | file | ratio | PSNR | Δ vs control | bytes vs control |
|---|---|---|---|---|---|
| `r16_b48` | 15.30 MB | 19.20× | **26.70** | — | — |
| `r16_b64` | 17.18 MB | 17.10× | **27.02** | **+0.32** | +12.3 % |
| `r24_b48` | 15.71 MB | 18.70× | 25.84 | −0.86 | +2.7 % |
| `r32_b48` | 16.24 MB | 18.09× | 24.79 | −1.91 | +6.1 % |
| `r8_b48` | 17.09 MB | 17.19× | 26.72 | +0.02 | +11.7 % |

## Verdict: `colour_residual_is_bits`

**J1 (rank) FAIL.**  No iso-byte plan recovers 0.3 dB on bonsai.  The best of them, `r24_b48`, *loses*
0.86 dB while paying 2.7 % more bytes.  Rank 24 and 32 lose on every scene, and they lose more the
smaller the scene — a monotone, three-scene answer to the question M22 could only ask on bicycle.

**J2 (bits) PASS.**  `r16_b64` recovers +0.32 dB on bonsai at +12.3 % bytes, and +0.16 dB on both larger
scenes at ~+10 %.

So the 16-dimensional subspace was never the constraint: the coefficients that live in it are quantised
too coarsely.  Handing the same 48 bits to 24 or 32 components makes every component coarser and costs
0.7–1.9 dB; handing 16 more bits to the same 16 components is the only move that buys anything.

**J5 (cost) PASS.**  Encode 519 s / 420 s / 96 s for five plans on bicycle / stump / bonsai (≈104 s per
bicycle plan, matching M31's 121 s single-plan number); decode path unchanged.

## J4: the plan can be chosen offline — but only with the right metric

The pre-registered J4 asked whether the plan that minimises coefficient reconstruction error is the plan
that maximises render PSNR.  With the obvious definition of "coefficient error" — RMS of the quantised
coefficients against the unquantised ones *inside the retained subspace* — the answer is **no**:

| scene | Spearman(error in subspace, PSNR) |
|---|---|
| bicycle | −0.700 |
| stump | −0.700 |
| bonsai | −0.900 |

The naive metric puts `r8_b48` first (6.6 % / 6.9 % / 7.4 % error, by far the lowest) because it never
looks at the 37 of 45 coefficients that rank 8 throws away — it measures the quantiser on a subspace
that has already discarded 21–28 % of the energy.

Charging the truncation — RMS against the **original 45 columns**, `‖(coef_q·V + μ) − C‖ / ‖C‖` — makes
the ordering exact on all three scenes:

| plan | bicycle | stump | bonsai | Spearman vs PSNR |
|---|---|---|---|---|
| `r16_b64` | 28.73 % | 35.82 % | 35.50 % | |
| `r16_b48` | 50.65 % | 55.49 % | 55.37 % | |
| `r8_b48` | 54.82 % | 59.81 % | 51.88 % | **−1.000** on all three |
| `r24_b48` | 86.87 % | 105.03 % | 93.64 % | |
| `r32_b48` | 119.49 % | 136.63 % | 131.72 % | |

So a scene-adaptive colour budget *can* be chosen without rendering anything, which is what J4 was for.
The metric has to be the one the loss is actually about.  (This is the same failure mode that made
N31's mid-rate probe misleading, in mirror image: there a proxy that included truncation was trusted
too much; here a proxy that excluded it is worthless.)

## A side finding: iso-raw is not iso-file

All four 48-bit plans write exactly 36.79 MB of coefficient codes on bicycle (6.0 B/primitive), and they
compress to 18.58 / 20.08 / 22.01 / 29.25 MB for rank 16 / 24 / 32 / 8 — a 58 % spread in the bytes the
file pays for the same raw budget.  The reason is the symbol alphabet: rank 8 with 48 bits gives 6-bit
codes (64 symbols, near-uniform) where rank 16 gives 3-bit codes (8 symbols, strongly skewed).  This is
M20/M24's alphabet result arriving from the other side — the alphabet is a function of the allocation, so
"same number of bits" is not "same number of bytes" once zstd is in the loop.  Consequence for this
round: `r8_b48` costs +14 % bytes rather than 0 %, and the iso-byte window (±5 %) admits only `r24` and
`r32`.  Both lose.

## A measurement note that the paper has to carry

The bonsai control renders 26.70 dB here and 27.08 dB in M31 — 0.38 dB apart, for a container of the
same nominal size.  Bicycle, in the same pair of rounds, reproduced to the digit (24.06 dB,
SSIM 0.7393), and re-encoding bonsai on this node reproduces the container byte for byte
(`md5 a3d3488a537b2f30d3231ce849cde201`), so:

* the encoder is deterministic **on a fixed build**;
* the renderer is consistent for a fixed archive (bicycle agreeing across two nodes shows the pipeline
  is not drifting);
* the bonsai container built on two different nodes differs in *content* while matching in size, and the
  difference is not attributable from the evidence available.  The standing suspects are the torch build
  behind `torch.svd_lowrank`'s random start (the seed fixes the stream only within a build) and the
  gsplat version (this node shipped without gsplat/scikit-image/lpips and needed a hand install, so the
  two nodes provably did not have the same rasteriser).

Every M32 claim is therefore a within-round delta against the same-round control, measured by one
process on one machine.  Cross-round absolute PSNR on bonsai carries ±0.4 dB of build uncertainty; on
the two larger scenes it has reproduced exactly every time it has been re-measured.

## What this changes

* `experiments/FRONTIER_BOUND.md` §11 records the sweep, the verdict and the offline selector.
* The near-lossless row keeps one configuration for all scenes (M31's conclusion that the rate model
  transfers is untouched); what changes is that the *fidelity* knob is now named and priced:
  +16 bits of colour per primitive buys +0.16 / +0.16 / +0.32 dB for ~+10 / +10 / +12 % bytes.
* Appendix **N39** records the failed half: more subspace at fixed bytes is worse on all three scenes,
  and the coefficient-error proxy that ranks it best is measuring the wrong thing.
* `experiments/artifacts/a4/sota_table.md` gains the colour-block table and the offline-selector table.

## Reproduce

```
# node: image Pytorch 2.6.0_cuda_12.4 + `pip install plyfile zstandard packaging gsplat scikit-image lpips`
for s in bicycle stump bonsai; do bash experiments/run_m32.sh setup $s; done
bash tools/m32_drive.sh bicycle stump bonsai        # encode | coef | render per scene, then collect
python3 tools/m32_coef_error.py --ply <ply> --plans 16:48,24:48,32:48,8:48,16:64 --json coef2_<scene>.json
python tools/m32_analyse.py --root experiments/artifacts/a4/m32
```

## Cost and artefacts

Node 2140760, 10:07 → 11:50 ≈ 1.72 h ≈ ¥4.8.  `experiments/artifacts/a4/m32/`: `m32_sizes.json`,
`coef_{bicycle,stump,bonsai}.json` (naive metric), `coef2_*.json` (full metric), `render_*.log`,
`coef_*.log`, `enc_*.txt`.  Gates after the round: `pytest experiments/tests` **93 passed**;
`m1_check_bytes.py` 881 cases 0 mismatches; `check_py311.py` 144/144.
