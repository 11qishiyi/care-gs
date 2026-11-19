# M28 — predicted anchors: the decoder M27 proved was missing, and the bits it cannot invent

Round 24. Node 2140655 (A100-PCIE-40GB, ¥2.80/h), rented 04:52, released 06:50 (≈2.0 h ≈ ¥5.6). Preregistered in
`tools/m28_spec.md` (copied into `METHOD_PLAN.md`) **before** any training ran.

## Verdict: `prediction_does_not_pay` — B1 and B2 fail, B3 passes

M27 measured that an anchor storing *one constant* attribute record is 3.8× cheaper than the shelf and
4–8 dB worse, and attributed the loss to the missing per-primitive prediction. M28 built that predictor:
a 10 → 64 → 64 → 7 MLP whose 10.6 kB of float16 weights live in the container, fed by the anchor's
seven attribute numbers and the primitive's offset inside the voxel.

| criterion | bar | measured | |
|---|---|---|---|
| **B1** ≤ 30 MB and ≥ 23.0 dB | 23.0 dB | 27.13 MB / **17.04 dB** | FAIL (−5.96) |
| **B2** ≤ 25 MB and ≥ 22.0 dB | 22.0 dB | 27.13 MB (smallest) / 17.04 dB | FAIL |
| **B3** one file, decode ≤ 60 s, RSS ≤ 8 GB | 60 s / 8 GB | **5.36 s / 4.03 GB**, weights inside | PASS |
| **B4** attribution (constant / predicted / oracle) | reported | constant 16.97 → predicted 17.04 (+0.08) | reported |

## Measurements

bicycle, the published model, 6,131,954 primitives, SH degree 3, 25 held-out views at 1236×822,
clean model 24.52 dB / 1447 MB, shelf 83.41 MB / 24.08 dB. All containers at 8 primitives per voxel
(voxel 10.7 cm, 766,512 anchors), rank-16 colour basis, 48-bit coefficients.

| container | file | B/prim | PSNR | Δ vs M27 constant |
|---|---|---|---|---|
| M27 constant, 4-bit offsets, DC 6 | 29.62 MB | 4.83 | 16.26 | — |
| **M28 predicted, 4-bit offsets, DC 4** | **27.13 MB** | **4.42** | **17.04** | **+0.08** (M27 a8_o4 16.97) |
| M28 predicted, 4-bit offsets, DC 6 | 33.57 MB | 5.47 | 17.05 | +0.08 |

Against the other mid-rate rows: pruning + fine-tune 24.96 MB / 21.24 dB, HAC 27.54 MB / 25.05 dB,
PCGS 19.09 MB / 25.12 dB. The predicted-anchor container is 4.2 dB below our own pruning at the same
file size, so nothing about this representation competes on the mid-rate row.

## Why it does not pay — three measurements, no hand-waving

**(1) The loss never moves.** Per-step training loss (batch 2²⁰, 12,000 steps, Adam 1e-3):

| step | total | scale | quaternion | opacity |
|---|---|---|---|---|
| 0 | 9.665 | 2.118 | 0.0780 | 14.469 |
| 1,000 | 9.052 | 2.115 | 0.0782 | 13.248 |
| 6,000 | 9.02 | 2.11 | 0.078 | 13.2 |
| 11,999 | 9.016 | 2.116 | 0.0782 | 13.175 |

Every decibel of improvement is the opacity *bias*; the scale term moves 0.3 % and the rotation term
not at all (mean |dot| 0.92 = the constant's number, i.e. the network outputs ≈ zero correction).

**(2) The optimiser is fine.** `tools/m28_control.py` trains the identical network on a synthetic world
where scale and opacity really are functions of the offset: loss 1.13 → **1e-5 in 500 steps**. So the
quaternion composition, the loss and the optimiser are all working; the flat curve on bicycle is a
statement about the data.

**(3) The ceiling is arithmetic.** `tools/m28_var.py` measures, for every voxel, the fraction of an
attribute's variance its mean explains:

| primitives per voxel | voxel edge | anchors | R² scale | R² opacity | R² rotation |
|---|---|---|---|---|---|
| 4 | 5.1 cm | 1,533,083 | 0.742 | 0.531 | 0.733 |
| 8 | 10.7 cm | 766,512 | 0.628 | 0.378 | 0.595 |
| 16 | 19.0 cm | 383,174 | 0.538 | 0.274 | 0.473 |
| 64 | 46.7 cm | 95,872 | 0.412 | 0.161 | 0.287 |
| 256 | 97.7 cm | 23,975 | 0.338 | 0.107 | 0.171 |

At the grid used, **37 % of the scale variance, 62 % of the opacity variance and 40 % of the rotation
variance live inside the voxel**. An anchor record is 58 bits; its eight members' attributes are
8 × 58 = 464 bits. The anchor holds the 58 bits that are redundant and none of the 406 that are not, so
no decoder can reconstruct them — the predictor was asked to invent information it never received.

## What this changes for the paper

* The mid-rate gap is **not** closed by an anchor representation in the post-hoc setting: at equal
  bytes, pruning + fine-tune (21.24 dB) beats anchor + predictor (17.04 dB) by 4.2 dB, and both are
  behind HAC/PCGS by another 3.8 dB.
* N33 (supervision), N34 (constant anchors) and N35 (predicted anchors) now exclude the three
  post-hoc explanations of that gap: it is not the supervision resolution, not the lack of an anchor
  representation, and not the lack of a predictor. What remains is the thing that all three failed to
  provide — **learned per-anchor latents trained jointly with the decoder under a rate–distortion
  objective, with entropy-coded residuals**. That is a training programme, and the next round should
  either do it or declare the row out of reach for this project's scope.
* What the anchor representation *is* good for stays true and measured: 2.52 B/primitive at 16
  primitives per voxel (15.42 MB), decode 3.4 s, RSS 3.1 GB — the cheapest container this project has
  built, and the natural backbone for a progressive or low-LoD stream.

## Cost and artefacts

* Node 2140655: rented 04:52, released 06:50 (≈2.0 h ≈ ¥5.6; setup 20 min incl. the 1.5 GB download, two encodes with 12k training steps each, two renders, one timing run) 
* Code: `experiments/m28_pred.py`, `experiments/run_m28.sh`, `experiments/tests/test_m28_pred.py`
  (4 cases), `tools/m28_control.py`, `tools/m28_var.py`, `tools/m28_spec.md`.
* Gates: `pytest experiments/tests` **85 passed**; `m1_check_bytes.py` 881 cases 0 mismatches;
  `check_py311.py` 138/138.
* Negative result: `APPENDIX_negative_results.md` **N35**.

## Reproduction

```bash
bash experiments/run_m28.sh setup       # deps + data + base archive (20 min)
bash experiments/run_m28.sh train       # two containers, 12k steps each
bash experiments/run_m28.sh render      # decode to PLY, archive, 25 views
python tools/m28_var.py <point_cloud.ply>   # the ceiling table
python tools/m28_control.py                 # the optimiser control
```
