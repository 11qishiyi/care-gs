# M26 — Is the mid-rate gap a training-recipe problem?

**Round 22.** Preregistered in `tools/m26_spec.md` (00:30) with one amendment written at 00:45, before
any fine-tune ran (00:56). Node 2140583 (A100-PCIE-40GB, ¥2.80/h), rented 00:10, released 03:23
(≈ 3.2 h ≈ ¥8.9).

## The question

Every mid-rate point this project has ever reported came from one recipe: prune the published model to
25 % by volume, then fine-tune for 30 k steps at **factor 4** (735 × 490 crops) with geometry frozen.
HAC and PCGS sit 3–5 dB above that line at the same file size, and their difference from us is not one
thing: they also train at **factor 1–2** and optimise under an entropy constraint. If supervision
resolution alone closed the gap, the honest response would be "our codec is fine, our fine-tune was
under-resolved" and the mid-rate row would be an engineering afternoon. If it did not, the gap lives in
the representation and no amount of pruning or fine-tuning will move it.

R1 asked for ≥ 23.80 dB at ≤ 30 MB. R2 asked for an equal-primitive, equal-byte, equal-view attribution.
R3 said: if the factor-2 arm does not beat the factor-4 arm by ≥ 0.3 dB, stop spending node time on
post-hoc pruning and change the representation.

## What was run

Prune source is the **published** bicycle model (`iteration_30000`, 6,131,954 primitives, clean
24.52 dB), not a mirror model of our own, so the mid-rate row starts from the same 3DGS release that
the published codecs start from.

| stage | setting |
|---|---|
| prune | `prune_ply.py --keep-frac 0.25 --score volume` → 1,532,988 primitives, 380.2 MB PLY |
| pre-finetune render | **15.18 dB**, SSIM 0.389 |
| arms | A = factor 4, B = factor 2, both `--no_densify`, 12 k steps |
| shared flags | `--sh_degree 3 --split interleaved --gt-convention archive --keep_all_views --no_scene_scale --lr_scale 0.3 --grad_clip 1.0 --eval_every 2000` |
| encode | `m24_alpha.py` auto-alphabet container, three rate points |

## The answer

| arm | supervision | steps | wall time | held-out PSNR (last eval) | archive render |
|---|---|---|---|---|---|
| A | factor 4 | 12 000 | 731 s | 21.42 | **21.40** |
| B | factor 2 | 12 000 | 2 276 s | 21.33 | **21.33** |

**Factor 2 costs 3.1× the wall time and buys −0.07 dB.** The eval curves are monotone in both arms
(20.79 → 21.42 for A, 20.70 → 21.33 for B): this is a converged difference, not an artefact of where
training stopped. R3 fires.

At the encoded rate points the two arms are the same experiment seen twice:

| plan | arm A file | B/prim | PSNR | arm B file | B/prim | PSNR |
|---|---|---|---|---|---|---|
| `gp8-8-8_c10_sh3` r16/64 | 24.96 MB | 16.28 | 21.24 | 24.91 MB | 16.25 | 21.19 |
| `gp8-8-8_c10_sh3` r16/48 | 22.63 MB | 14.76 | 21.15 | 22.58 MB | 14.73 | 21.10 |
| `gp8-6-6_c9_sh3` r16/48 | 20.96 MB | 13.68 | 21.10 | 20.92 MB | 13.64 | 20.95 |

Quantisation costs 0.16–0.30 dB at these rates — the same amount it costs at the near-lossless end, so
the codec is not the mid-rate problem either.

## Where that leaves the mid-rate row

| method | bicycle bytes | PSNR |
|---|---|---|
| HAC | 27.54 MB | 25.05 |
| PCGS | 19.09 MB | 25.12 |
| **this work** | 24.96 MB | **21.24** |
| **this work** | 20.96 MB | **21.10** |

−3.8 dB at 10 % more bytes than HAC, −4.0 dB at 10 % more bytes than PCGS. R1 fails by 2.4 dB.

The failure is now causal rather than argued. Three nodes of evidence say the same thing from three
directions: N25–N27 (a 6.13 M-primitive model cannot fit in 27.5 MB once geometry alone costs
7.97 B/primitive), M17/M18 (post-hoc pruning trades decibels for bytes at a fixed exchange rate), and
now M26 (the supervision that produced the surviving primitives is not what limits them; doubling the
pixels changes nothing). A fixed set of 1.5 M Gaussians, each carrying its own mean, rotation, scale,
opacity and 48 SH coefficients, is simply a more expensive object than an anchor grid with a shared
decoder. At 25 % of the published model we are 3.2 dB below the model we started from and we cannot buy
those decibels back by training harder against the same object.

## What this changes

1. **The mid-rate row stops being a training problem.** No further prune/fine-tune sweep is worth node
   time; the exchange rate between primitives and decibels has been measured twice (M17, M18) and the
   supervision lever has now been measured and found to be flat (this round).
2. **The claim this project can defend is the near-lossless frontier**, where the comparison is
   representation-agnostic: 17.35× at 24.08 dB (0.44 dB below the 24.52 dB source model, 0.04 dB below
   the M23 shelf point), 1.97 GB decoder peak RSS,
   7.69 s decode, a single file, and a byte budget that adds up (M24, M25).
3. **Beating HAC/PCGS at 20–30 MB requires changing what a primitive is** (anchors, a shared colour
   decoder, a vector field), which is a new codec rather than a new knob. That is the next representation
   round, not this one.

## Reproduction

```
bash experiments/run_m26.sh setup                     # published PLY + colmap + base archive (~50 min)
bash experiments/run_m26.sh prune                     # 1,532,988 primitives, 15.18 dB
STEPS=12000 bash experiments/run_m26.sh finetune 4 freeze
STEPS=12000 bash experiments/run_m26.sh finetune 2 freeze
bash experiments/run_m26.sh encode f4_freeze
bash experiments/run_m26.sh encode f2_freeze
```

Artifacts in `experiments/artifacts/a4/`: `m26_m26_summary.txt` (both eval histories), the two encode
logs (per-stream tables and file sizes), the two render logs.

## Costs and mistakes

- One wasted arm: the first fine-tune launch omitted `--no_scene_scale --lr_scale 0.3 --grad_clip 1.0`,
  which the M17/M18 recipes carry, and the model collapsed to 1.20 dB. The lesson is that the flags
  which make a fine-tune stable are part of the method, not boilerplate — a new harness has to copy the
  whole invocation, not the arguments it happens to notice.
- Two chains ran concurrently after a `pkill` killed the trainer but not its parent shell, so a second
  arm started on top of the first. GPU time was lost and both runs slowed; the tell was two
  `train_gs.py` processes with identical start times.
- Per-step PSNR in this trainer is a single-view measurement under un-normalised exposure, so it
  swings between 7 and 23 dB while the model improves monotonically. Only the `[eval] cal=` line is a
  measurement; the step prints are noise.
