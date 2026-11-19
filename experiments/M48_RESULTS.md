# M48 — the saliency prune is a method: +3.17 / +1.64 dB on the other scenes, +1.51 dB on a second seed

**Round 31, node 2141508 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 08:30–10:05 ≈ ¥4.3.** M47 replaced the pruning score
with measured saliency and gained +1.59 dB at equal bytes on bicycle — one scene, one seed. This round was the
replication: the same protocol on **stump** and **bonsai**, plus **bicycle with a second finetune seed**, with every
number produced on one node in one session and the criteria written before the first measurement.

## Result

Equal-bytes pairs (within 2 % of each other in file size; the saliency container is re-encoded with a smaller colour
budget when it comes out larger):

| scene | volume arm | saliency arm (equal bytes) | Δ | Δ SSIM | ratio vs fp32 |
|---|---|---|---|---|---|
| bicycle seed 1 (M47) | 19.34 MB / **21.08** / 0.517 | 19.45 MB / **22.67** / 0.681 | **+1.59** | +0.164 | 74.4× → 74.0× |
| bicycle seed 2 | 19.34 MB / **21.07** / 0.516 | 19.43 MB / **22.58** / 0.680 | **+1.51** | +0.164 | 74.4× → 74.1× |
| stump | 15.49 MB / **20.35** / 0.391 | 15.12 MB / **23.52** / 0.675 | **+3.17** | +0.284 | 75.6× → 77.4× |
| bonsai | 3.94 MB / **24.10** / 0.768 | 3.99 MB / **25.74** / 0.858 | **+1.64** | +0.090 | 74.6× → 73.6× |

Ratios use the series' payload convention (236 B/primitive: bicycle 1447.1 MB, stump 1170.98 MB, bonsai 293.78 MB).
At 25 % keep with colour budgets of 48 / 40 / 32 bits, the mid-rate regime sits at 73–77×, i.e. 4× the near-lossless
shelf's 18.90×.

**Verdict `saliency_prune_is_a_method`** — T1 PASS (stump +3.17, bonsai +1.64, both ≥ 0.5 dB at equal bytes),
T2 PASS (+1.51 ≥ 0.75 dB on a second seed), T4 PASS (gates below). **T3 FAIL on stump** (see below), and that failure
is the most informative number in the round.

## Where the gain comes from — and where the criterion was wrong

Each pruned set is rendered three times: before finetuning, on the calibration views after 12k steps, and after encoding.

| scene | volume: pre → cal → container | saliency: pre → cal → container | Δ pre | Δ container |
|---|---|---|---|---|
| bicycle | 15.18 → 21.43 → 21.08 | 20.11 → 24.75 → 22.67 | +4.93 | +1.59 |
| stump | 20.59 → 20.57 → 20.35 | 20.89 → 25.89 → 23.52 | **+0.30** | **+3.17** |
| bonsai | 24.67 → 24.98 → 24.10 | 27.00 → 29.67 → 25.74 | +2.33 | +1.64 |

T3 asked for ≥ 2.0 dB pre-finetune on both new scenes and stump delivers 0.30 — so the pre-registered mechanism test
fails while the outcome test passes by a wide margin. Both rows are true and they say different things:

* On stump the volume set renders at the *same PSNR* as the saliency set while being structurally much worse
  (SSIM 0.408 vs 0.726). It keeps large, faint splats that cover pixels with roughly the right mean colour and the
  wrong structure — PSNR barely sees the difference, and neither could the pre-finetune criterion.
* What the score buys is **what finetuning can recover**, not what the initial render looks like: stump's volume set
  does not improve at all across 12k steps (20.59 → 20.57 cal, 20.35 in the container), while the saliency set gains
  +5.00 dB (20.89 → 25.89) and keeps +3.17 after encoding. The same ordering holds on bonsai (+0.31 vs +2.67 cal).

So the assumption behind T3 — that a better selection shows up as a better starting point — was wrong. The pre-finetune
render is a diagnostic, not a criterion. Recorded rather than reinterpreted: **T3 FAIL stands.**

## Why stump gains three times as much as the others

The three scenes disagree about which primitives matter by very different amounts:

| quantity | bicycle | stump | bonsai |
|---|---|---|---|
| kept by both, of 1,532,988 / 1,240,449 / 311,205 | 27.7 % | **11.4 %** | 31.1 % |
| Spearman ρ(saliency, volume) | 0.407 | **0.179** | 0.447 |
| saliency mass the volume set keeps | 0.9994 | **0.1116** | 0.9834 |
| volume mass the saliency set keeps | 0.2403 | 0.1036 | 0.2793 |

On stump the volume score keeps an eighth of the primitives that carry the loss — a far more extreme disagreement than
bicycle's — and stump is the scene with the largest gain. The ranking by disagreement (0.179 < 0.407 < 0.447) is not the
ranking by gain (+3.17, +1.59, +1.64), so disagreement alone does not predict the prize, but the extreme case is where
the proxy costs the most.

## The price is in the colour block, not the geometry

| scene | volume B/prim | saliency B/prim (48-bit) | equal-bytes budget |
|---|---|---|---|
| bicycle | 12.62 | 13.40 | 40-bit (12.67) |
| stump | 12.49 | 13.69 | 32-bit (12.19) |
| bonsai | 12.65 | 13.35 | 40-bit (12.83) |

Same primitive count, same spec — yet the saliency set spends 6–10 % more bytes, because the primitives worth keeping
are the ones with detail in their colour, and the volume set wastes budget on faint background splats. This is why the
same-spec comparison flatters the saliency arm, and why the equal-bytes re-encode is the honest one. It also means part
of the gain is bought back: at 32-bit colour stump's saliency arm is 23.52 dB rather than 24.27.

## Gates

`pytest experiments/tests` **159 passed**; `m1_check_bytes.py` **881 cases, 0 mismatches**; `check_py311.py`
**164/164 files parse as 3.11**; `m19_codec --selftest` ALL PASS. This round added no new tests: it is a replication
of an existing protocol, and the arm-independence was already covered by `test_m47_importance.py`.

## What this changes

* **Mid-rate on bicycle is unchanged at −2.45 dB vs PCGS** (~19 MB): this round did not move the bicycle point, it
  showed the method is not a single-scene accident. The mid-rate deficit is now a *representation* deficit on the
  best scene and a *selection* deficit on the others.
* **The near-lossless shelf is untouched** (76.56 MB / 18.90× / 24.06 dB on bicycle): 25 % pruning is a mid-rate regime.
* **The pruning score is measured saliency in every mid-rate pipeline** (`prune_ply.py --score importance`); the volume
  score survives only as the published-model baseline and as the control arm.
* **The three-scene spread is the paper's claim:** the same post-hoc pipeline, nothing tuned per scene, lands at
  73.6–77.4× with +1.5…+3.2 dB over the volume score — but the *variance of the gain* (0.3× to 3.2× depending on scene)
  is a property of the proxy being replaced, not of the method.

## Reproduction

```bash
# on the node, one session, PYTHONPATH=research/code:root:experiments
bash tools/m48_drive.sh            # per scene: saliency pass, two prunes, both renders, both 12k arms, encodes
bash tools/m48_one.sh stump        # single scene
bash tools/m48_stump32.sh          # the equal-bytes re-encode for stump (32-bit colour)
python3 tools/m47_overlap.py --scene stump --importance ... --volume ...
```

Files: `experiments/M48_RESULTS.md`, `experiments/run_m48.sh`, `tools/m48_{spec,drive,one,stump32,gaps,gap2}.sh`,
`tools/m47_overlap.py`, `experiments/tests/test_m47_importance.py`.

## Cost

Node 2141508: A100-PCIE-40GB at ¥2.80/h, 08:30–10:05 ≈ **1.6 h ≈ ¥4.3**, of which ~80 min is training (8 arms × 12k
steps) and ~20 min rendering/encoding. All three published models came from the persistent `/mnt/m35cache`, so no
download cost this round.
