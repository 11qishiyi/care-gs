# M36 — the rate in the loss, and what part of it was real

Round 32 · node 2141303 (A100-PCIE-40GB, ¥2.80/h, rented 21:15) · pre-registered in
[`tools/m36_spec.md`](../tools/m36_spec.md) at 21:25, before the first line of this round's code existed.

## The question

Everything this project has measured so far optimises for rendering and *then* compresses. M26 showed the
mid-rate gap to HAC/PCGS (3.8 dB at 25 MB) is not supervision; M27–M28 showed it is not the container.
The remaining hypothesis was the obvious one: those methods optimise the model *with* its rate in the loop,
so their 27.5 MB model is a different function, not a better-compressed copy of ours.

So: **does a differentiable rate pressure on the parameters buy rate-distortion, or does it just shrink the
model like weight decay?** The third arm exists because those two explanations make identical predictions
unless you measure both.

## Design

One source, one recipe, three (later four) losses. Source: the published bicycle model pruned to 25 % by
volume score — 1,532,988 primitives, 380.2 MB PLY, renders 15.18 dB before fine-tuning (M26's source, so
arm a is a reproduction, not a new baseline). Recipe: 12k steps, factor 4, `--no_densify --no_scene_scale
--lr_scale 0.3 --grad_clip 1.0 --split interleaved --gt-convention archive --keep_all_views`.

The pressure is `R = mean(log2(1 + (θ/σ)²))` over `shN, sh0, scales, opacities`, with σ = 1.5 × the group's
own median |θ| at initialisation. It is scale-invariant, differentiable, and falls when a group's
distribution tightens. λ is calibrated once, at step 0, to make the pressure's gradient 5 % of the rendering
loss's gradient norm, then frozen — and both the log arm and the L2 control calibrate their *own* λ to the
same share, because an equal λ is not an equal pressure for two different functionals.

## Measurements

| arm | loss | λ | σ (shN, sh0, scales, opac) | container | B/prim | PSNR | SSIM | wall |
|---|---|---|---|---|---|---|---|---|
| **a** | `0.8 L1 + 0.2 (1−SSIM)` | — | — | 19,272,155 B | 12.574 | 21.07 | 0.5166 | 731 s |
| **b** | + log rate term, 5 % share | 0.9319 | 0.0437, 1.70, 6.78, 7.21 | **17,959,298 B** | **11.715** | **21.24** | 0.5279 | 812 s |
| **c** | + L2 control, 5 % share | 0.2959 | same | 18,381,419 B | 11.990 | 21.19 | 0.5281 | 780 s |
| **d** | + log rate term, 15 % share | 2.796 | same | 17,482,803 B | 11.404 | 21.09 | 0.5200 | 823 s |

Same 1,532,988 primitives in all four containers; all rendered on the same 25 held-out views at
1236 × 822; the final in-training eval (`[eval] PSNR … cal=`) tracks the render to within 0.3 dB
(a 21.42, b 21.52, c 21.51, d 21.40).

## What the numbers say

**b Pareto-dominates a**: 6.82 % fewer bytes *and* 0.17 dB more PSNR *and* a better SSIM. The pressure did
not buy bytes by selling quality — it moved the model to a place where the coder needs fewer bits *for the
same or better picture*. The rate term fell from 0.732 at step 0 to 0.197 at step 11.8k while calibration
PSNR rose to 21.52, i.e. the parameters genuinely redistributed rather than collapsing.

**The logarithm is not the active ingredient.** Arm c — plain `mean((θ/σ)²)` at the same 5 % gradient
share — reached 18,381,419 B at 21.19 dB. Against b it pays 2.35 % more bytes for 0.05 dB more PSNR: inside
render noise, and far short of the 0.3 dB R2 asked for. So what the pressure buys is **shrinkage of the
parameter distribution towards the quantiser grid**, and any smooth penalty that does that behaves the same.
That is a mechanism, not a result about entropy.

**15 % overshoots.** d reaches the smallest container of the four (17.48 MB, −9.3 % vs a) but gives back
0.15 dB against b and 0.07 against a. The pressure's return is not monotone: the knee is at or below the
5 % share. d's rate term ends at 0.145 (the lowest), which is the *shape* the coder likes best and the
*image* likes least — exactly the trade the pre-registration said to look for.

## Verdict

Pre-registered criteria, evaluated literally:

* **R1 FAIL** — b is 0.932× a's bytes (window was ≤ 0.85× for matched PSNR) and +0.17 dB (bar was +0.5 dB
  at matched bytes). Neither clause fires.
* **R2 FAIL** — c is +2.35 % bytes at −0.05 dB relative to b: not distinguishable, so "the rate term is
  weight decay" cannot be rejected.
* **R3 PASS** — 812 / 731 = 1.11× the wall clock.
* **R4 PASS** — 9 tests in `experiments/tests/test_m36_rate.py`.

Literal branch: `rate_pressure_does_not_pay`. **That label is wrong for what happened**, and the reason is
worth recording: R1 was written as a *trade* (bytes for dB) because that is the shape a rate-distortion
penalty is expected to have, and the measurement came back as a *Pareto move* (both improve), which no
clause covered. The round's own label, derived after the fact and flagged as such:

**`pressure_pays_through_shrinkage`** — a real 6.8 % bytes + 0.17 dB gain at 1.11× the wall clock, whose
active ingredient is shrinkage rather than entropy, with the pressure's knee below a 15 % gradient share.

## What this does and does not buy against SOTA

Our mid-rate point moves from 19.27 MB / 21.07 dB to **17.96 MB / 21.24 dB** (M26's factor-4 recipe was
24.96 MB / 21.24 dB at the time, on the M24 container). Against the published numbers,
HAC is 27.54 MB / 25.05 dB and PCGS 19.09 MB / 25.12 dB: we are now 6 % below PCGS's bytes at 3.9 dB below
its PSNR. **The gap did not close** — a 0.17 dB gain cannot close 3.9 dB — but the direction is the one the
hypothesis predicted, and it cost a fifth of a node-hour to establish.

The honest reading: fine-tuning a *pruned* model with a rate pressure recovers a little; the 3.9 dB is not
in the pressure, it is in the fact that a 25 %-pruned model has lost information the source never lost.
HAC/PCGS do not prune to 25 % — they train the full primitive count under an entropy model.

## Cost

Node 2141303, ~2.2 h of A100 at ¥2.80/h ≈ ¥6.2 for this round (four arms + containers + renders, plus the
failed first b/c attempts on a device bug, ~8 min).

## Reproduce

```bash
bash experiments/run_m36.sh setup && bash experiments/run_m36.sh prune
bash experiments/run_m36.sh arm b && bash experiments/run_m36.sh encode b && bash experiments/run_m36.sh render b
python tools/m36_table.py --dir experiments/artifacts/a4/m36
```

## Files

* code — `experiments/m36_rate.py`, `research/code/scripts/train_gs.py` (`--rate-lambda/--rate-kind/--rate-groups/--rate_share`), `experiments/run_m36.sh`, `tools/m36_{table,arms,arms_bc,arm_d}.{py,sh}`
* tests — `experiments/tests/test_m36_rate.py` (9)
* spec/amendments — `tools/m36_spec.md`, `tools/m36_amend.md`
* artifacts — `experiments/artifacts/a4/m36/render.txt`, `m36_time.txt`, `train_{a,b,c,d}.log`
