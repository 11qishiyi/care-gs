# M37 — the rate pressure on the full model: it recovers what fine-tuning destroyed, and not more

Round 33 · node 2141303 (A100-PCIE-40GB, ¥2.80/h, rented 21:15, released 00:12) · pre-registered in
[`tools/m37_spec.md`](../tools/m37_spec.md) at 23:05, before the first measurement of this round.

## The question

M36 showed a differentiable rate pressure on a *pruned* model is a Pareto gain (6.8 % bytes, +0.17 dB) — but
that model started at 15.18 dB and had ample headroom to recover. The headline number lives on the **full**
6,131,954-primitive model, 76.56 MB at 24.06 dB. Does the same pressure buy bytes when there is no headroom?

## Design

Same recipe as M36, applied to the published bicycle model instead of the pruned one: 12k steps, factor 4,
`--no_densify --no_scene_scale --lr_scale 0.3 --grad_clip 1.0 --split interleaved --gt-convention archive
--keep_all_views`, shipping container `gp6-6-6_c8_sh3` with the rank-16/48-bit colour basis, 25 held-out
views.

* **A** — plain loss (0.8 L1 + 0.2 (1−SSIM)): what 12k steps of factor-4 fine-tuning do to a converged model.
* **B** — same + the log rate term on `shN, sh0, scales, opacities`, λ calibrated at step 0 to a 5 %
  gradient share, frozen (λ = 0.2358 here, against 0.9319 on the pruned model: a converged model's
  parameters are already near the scale the penalty wants).

## Measurements

| arm | container | B/prim | PSNR | SSIM | wall | eval cal |
|---|---|---|---|---|---|---|
| **a** | 76,931,227 B | 12.546 | 23.69 | 0.7244 | 1265 s | 25.27 |
| **b** | **73,124,530 B** | **11.925** | **23.81** | **0.7331** | 1577 s | 25.26 |
| reference: untouched published model | 76,556,000 B | 12.480 | **24.06** | 0.7393 | — | — |

b against a: **bytes ×0.951, PSNR +0.12 dB, SSIM +0.0087, wall ×1.25**.

## Verdict

Pre-registered criteria:

* **K1 PASS by its second clause** — b is +0.12 dB at 0.951× the bytes (the first clause, ≤ 0.95× bytes with
  ≥ −0.10 dB, misses by 0.06 percentage points of byte ratio: 0.9506 vs 0.9500). Recording the near miss
  rather than rounding it.
* **K2 PASS** — bytes fell and SSIM rose by 0.0087.
* **K3 PASS** — 1.25× the wall clock.

Branch: **`pressure_helps_near_lossless`**.

## What that verdict does not mean

Both arms are *worse than not fine-tuning at all*. Twelve thousand steps at factor 4 on a converged model
costs **0.37 dB and 0.4 MB** (a: 76.93 MB / 23.69 dB against the untouched 76.56 MB / 24.06 dB). The pressure
recovers 0.12 dB of that 0.37 and 4.9 % of the bytes; it does not put the model back where it started, and
against the existing rate-distortion curve — 76.56 MB / 24.06 dB and 69.34 MB / 23.80 dB measured in M35 —
b's 73.12 MB / 23.81 dB is *dominated* by the interpolation (the curve gives ≈ 23.94 dB at 73.12 MB, 0.13 dB
more than b).

So the honest summary of M36 + M37 together:

| where the pressure was applied | start | result | frontier? |
|---|---|---|---|
| 25 %-pruned model (M36) | 15.18 dB, ample headroom | 17.96 MB / 21.24 dB vs 19.27 / 21.07 | **new point** for that model |
| full model (M37) | 24.06 dB, converged | 73.12 MB / 23.81 dB vs 76.93 / 23.69 | **dominated** by the untouched shelf |

**The pressure buys back quality that a fine-tuning schedule destroyed; it does not create quality that the
model does not have.** On the pruned model the destroyed quality was recoverable (0.17 dB above the control,
i.e. beyond recovery to parity); on the converged model there was nothing to recover beyond parity with the
starting point, and neither arm reaches it.

That is a negative result about a lever everyone assumes is free, and it is why M37 was worth its ¥2.80.

## Consequence for the near-lossless headline

The shipping point stays **76.56 MB / 18.90× / 24.06 dB** — untouched model, no fine-tuning. The M35 sweep
had already established that moving along that curve by re-encoding (69.34 MB / 23.80 dB, 66.24 MB /
23.60 dB) is cheaper than moving by training: 0.26 dB for 9.4 % bytes, against 0.37 dB for 0.4 % bytes here.

## Cost

Node 2141303: ~2.95 h of A100 ≈ ¥8.3 for M36 + M37 together (both rounds shared the node).

## Reproduce

```bash
bash experiments/run_m37.sh all
python tools/m37_table.py --dir experiments/artifacts/a4/m37
```

## Files

* code — `experiments/run_m37.sh` (arm|encode|render|all), `tools/m37_table.py`, `tools/fetch_m37.py`
* spec — `tools/m37_spec.md`
* artifacts — `experiments/artifacts/a4/m37/{render.txt,m37_time.txt,train_a.log,train_b.log,encode_a.log,encode_b.log,m37_table.json}`
