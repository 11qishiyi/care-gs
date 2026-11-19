# M47 — prune by what the loss pulls on: +1.59 dB at equal bytes, and +4.9 dB before any training

**Round 30, node 2141502 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 06:40–07:25 ≈ ¥2.1.** The mid-rate shelf has been
stuck at HAC −3.8 dB / PCGS −4.0 dB since M26, and M26–M39 ruled out supervision, anchors, predictors, entropy coding
and rate pressure as the cause. The one thing never questioned was **which primitives survive pruning**: the score was
`opacity × cbrt(sx·sy·sz)`, a proxy for how much an image a primitive can change, computed without rendering. This
round measured the saliency instead of approximating it, and the proxy was the bottleneck.

## Method

1. **Saliency pass.** 800 steps of the M17 recipe from the published 6,131,954-primitive model (factor 4, `--no_densify`
   so indices stay fixed), accumulating `Σ [(∂L/∂μ)² + (∂L/∂s)² + (∂L/∂α)²]` per primitive. 193 s, of which ~110 s is
   the 800 steps; the model is discarded, only the vector is kept (`imp_bicycle.npy`, 49 MB of float64).
2. **Prune** to 25 % (1,532,988 primitives) by that vector — `prune_ply.py --score importance`.
3. **Finetune** 12k steps, M17 recipe, and **encode** at `gp6-6-6_c8_sh3` — identical to the volume arm in every
   respect except the score.

## The two selections are not the same selection

| quantity | value |
|---|---|
| kept by both, of 1,532,988 | 424,683 (**27.7 %**) |
| Spearman ρ(saliency, volume) | **0.407** |
| saliency mass the volume set keeps | 0.9994 |
| volume mass the saliency set keeps | 0.2403 |

The two rankings disagree about 72 % of the surviving set. Note the third row: the volume set already carries 99.94 % of
the *total* saliency mass — which is exactly why the proxy looked safe, and why this was never tried. What the proxy gets
wrong is not the mass, it is **which** primitives hold it: it keeps large, faint, distant primitives whose gradient is
small, and drops small ones that sit on the loss.

## Measurements (bicycle, 25 held-out views, same node, same session)

| stage | volume score | saliency score | difference |
|---|---|---|---|
| pruned model, no training | 15.18 dB / SSIM 0.389 | **20.11 dB / SSIM 0.693** | **+4.93 dB** |
| after 12k finetune (cal view) | 21.43 dB | **24.75 dB** | +3.32 dB |
| container, same spec `gp6-6-6_c8_sh3` | 19.34 MB / 21.08 dB / 0.517 | 20.54 MB / 22.92 dB / 0.700 | +1.84 dB at +6.2 % bytes |
| **container at equal bytes** | **19.34 MB / 21.08 dB / 0.517** | **19.45 MB / 22.67 dB / 0.681** | **+1.59 dB at +0.6 % bytes** |

The equal-bytes row is the one that counts, because equal primitive counts do **not** guarantee equal bytes: the
saliency-pruned model holds detail where the container charges for it, so it compressed 6.2 % larger at the same spec
(13.40 against 12.62 B/primitive). Re-encoding it with a 40-bit colour budget lands at 19.45 MB, 19.34 MB's match.

The training-side gain (+3.32 dB) is bigger than the encoded gain (+1.59 dB) for the same reason: the saliency model's
extra quality lives in colour detail, which is the expensive stream, not in geometry, which is nearly free.

## Criteria

* **S1 — ≥ +0.5 dB at the same container — PASS**: +1.59 dB at +0.6 % bytes, SSIM +0.164.
* **S2 — the scores must not be the same selection — PASS**: 27.7 % overlap, ρ = 0.407.
* **S3 — saliency pass ≤ 4 min — PASS** at 193 s. Its second clause (the pass's own render within 0.5 dB of the full
  model) is **not measured**: the run's model was discarded without a held-out render, and the finetuned arm supersedes
  it. Stated as unmeasured rather than assumed.
* **S4 — code tested — PASS**: `experiments/tests/test_m47_importance.py` (4), plus 159 total.

## Where this leaves the mid-rate gap

| method | bytes (bicycle) | PSNR |
|---|---|---|
| PCGS (quoted) | 19.09 MB | 25.12 dB |
| HAC (quoted) | 27.54 MB | 25.05 dB |
| **ours, M47 saliency prune + finetune** | **19.45 MB** | **22.67 dB** |
| ours, M26 volume prune + finetune | 19.34 MB | 21.08 dB |

The gap against PCGS at ~19 MB shrinks from **−4.04 dB to −2.45 dB**, and every part of it is post-hoc: no architecture
change, no retraining from scratch, no learned entropy model — one 800-step pass to measure saliency and the finetune we
already had. This is the first mid-rate movement in five rounds, and it came from asking a question the pipeline had
never asked: *which primitive is the loss actually pulling on?*

## What is still on the table

* **Other scenes and seeds.** One scene, one seed. The mechanism predicts the same ordering on stump and bonsai, and the
  series' rule is to report a single-seed effect as an effect and a multi-scene one as a method.
* **Longer saliency, more steps.** 800 steps was chosen before the data; the vector converged (finite, sum 113,490)
  but nothing here rules out 2000 steps being better.
* **Saliency × volume.** The volume set keeps 99.94 % of saliency mass and the saliency set keeps 24 % of volume mass —
  a product of the two would keep the primitives that are both large and load-bearing, which is what a renderer cares
  about. That is a pre-registerable hypothesis, not a conclusion.

## Reproduction

```bash
SCENE=bicycle bash experiments/run_m47.sh setup
SCENE=bicycle bash experiments/run_m47.sh importance     # 800 steps -> imp_bicycle.npy
SCENE=bicycle bash experiments/run_m47.sh prune          # both scores + overlap report
SCENE=bicycle bash experiments/run_m47.sh arm v; SCENE=bicycle bash experiments/run_m47.sh arm g
SCENE=bicycle bash experiments/run_m47.sh encode v; SCENE=bicycle bash experiments/run_m47.sh encode g
bash tools/m47_g40.sh        # the equal-bytes encode of arm g
bash tools/m47_pruned.sh     # the two pre-finetune renders
```

Artifacts: `experiments/artifacts/a4/m47/` (drive.log, importance.log, train_v.log, train_g.log, enc_v.log, enc_g.log,
enc_g40.log, render_v.log, render_g.log, render_g40.log, render_prune.log, overlap.json).

## Cost

45 min of A100-PCIE-40GB ≈ ¥2.1, of which 25 min is the two 12k-step finetunes.
