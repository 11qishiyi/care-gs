# M49 — the container's mid-rate loss was a measurement, not a codec defect

**Round 32, node 2141648 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 10:35–11:25 ≈ ¥2.4.** M47/M48 reported that the
container eats **−1.83 dB** on the saliency-pruned model but only **−0.35 dB** on the volume-pruned one, and that
asymmetry was about to become the next method claim. It does not survive a controlled render: the two numbers were
measured on different protocols. This round renders the missing control and finds the container costs **0.39 dB** on
both arms.

## What was measured

One node, one session, bicycle, seed 1, the M47/M48 recipe unchanged: 800 saliency steps → prune 25 % (1,532,988
primitives) → 12k finetune steps at factor 4. Then the *unquantised* finetuned model is registered in the archive and
rendered through the container's own probe path, and the same model is encoded at five colour budgets.

| row | file | PSNR | SSIM | Δ vs raw |
|---|---|---|---|---|
| **raw finetuned model, factor 1** | 380 MB PLY (236 B/prim) | **23.26** | 0.7334 | — |
| container, 96-bit colour | 30.78 MB | 23.04 | 0.7165 | −0.22 |
| container, 64-bit | 22.91 MB | 23.01 | 0.7130 | −0.25 |
| container, 48-bit | 20.56 MB | 22.87 | 0.6999 | **−0.39** |
| container, 40-bit | 19.47 MB | 22.63 | 0.6808 | −0.63 |
| container, 32-bit | 18.35 MB | 21.94 | 0.6415 | −1.32 |
| raw finetuned model, **factor 4** | — | **18.71** | 0.5726 | −4.55 |

All PSNRs are on the same 25 held-out views at the archive's resolution (factor 1) unless the row says otherwise.

## Verdict — `calibration_artifact`, `geometry_block_dominant`, the mid-rate point stands

* **C1 — decomposition.** `Q = R1 − C48 = 23.26 − 22.87 =` **0.39 dB**, below the 0.6 dB floor →
  **`calibration_artifact`**. The container is not what costs the mid-rate decibels. What produced M48's −1.83 dB was
  comparing a *factor-4 training-view* number against a *factor-1 held-out container* number: the factor-4 render of
  the very same model is 4.55 dB below its factor-1 render (18.71 against 23.26), so the protocol gap is three times
  the effect that was attributed to quantisation.
* **C2 — which block.** Encoding 48 → 96 colour bits buys **+0.17 dB for +10.22 MB**. The loss is not colour-budget
  limited → **`geometry_block_dominant`**. Per-primitive accounting puts the geometry block (positions, 6-bit scales,
  6-bit opacity, quaternions) at **9.16 of the 13.60 B/primitive** the container spends — **67 %** — with the colour
  block, at 4.34 B, taking the other third (corrected 13:20 on 11-17; the first write-up said 11.4 B / 85 %, see the
  correction note at the end of this file).
* **C3 — the mid-rate point does not move.** Best row at ≤19.5 MB is 40-bit: **22.63 dB @ 19.47 MB** against M48's
  22.67 @ 19.45 MB — a **−0.04 dB** replication, well inside the ±0.3 dB the criterion demanded. The point stands, and
  it is now known to be a model-side point rather than a codec-side one.
* **C4 — gates green**: 42/42 files parse as 3.11, `m1_check_bytes` 0 mismatches over 881 cases, `m19_codec
  --selftest` ALL PASS, run on the round's node.

## What this changes

1. **The codec is not the mid-rate bottleneck.** At 48 bits it costs 0.39 dB on the saliency model and 0.35 dB on the
   volume model — the same number twice. The claim "quantisation-aware finetuning is the next lever" is withdrawn
   before it was written.
2. **The mid-rate gap is a primitive-count-per-byte gap.** The finetuned model at 1.53 M primitives renders 23.26 dB
   *before* any compression, against PCGS's 25.12 dB at 19.09 MB. No coding decision can move a model that is already
   1.86 dB behind in its uncompressed form; either the same bytes must carry more primitives (cheaper geometry) or
   1.53 M primitives must be made better (selection, finetuning, representation).
3. **Colour is nearly free at mid-rate; geometry is the bill.** The colour curve is flat above 20.5 MB (+0.17 dB for
   50 % more bytes) and steep below 19 MB (−0.69 dB going 40 → 32 bits). Any byte saved from geometry can be spent on
   primitives at roughly 13 B each; any byte saved from colour buys almost nothing above 48 bits.
4. **A measurement defect, recorded.** Four rounds of documents compared a factor-4 training-view PSNR with a
   factor-1 held-out render. The rule this round adds: *a "clean" row is only comparable to a container row if both
   come through the same probe at the same factor on the same views*. Appendix **N54**.

## Where the numbers go

* mid-rate table (`sota_table.md`): the 40-bit row is the equal-bytes row, with the container loss stated as 0.39 dB
  rather than 1.83 dB;
* `FRONTIER_BOUND.md` §27: the decomposition and the geometry/colour accounting;
* `METHOD_PLAN.md`: M49 result + M50 spec (geometry precision at mid-rate, pre-registered before its data).

## Reproduction

```bash
# on the node, one session, PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
bash tools/m49_go.sh          # import check + detached driver
bash tools/m49_drive.sh       # the five stages, idempotent per stage
```

Files: `tools/m49_spec.md` (pre-registration, written 10:40 before the run), `tools/m49_drive.sh`, `tools/m49_go.sh`,
`tools/push_m49.ps1`, `experiments/artifacts/a4/m49/` (stage log, byte table, five encode logs, seven render logs,
importance and finetune logs), `experiments/artifacts/a4/m49_bundle.tgz`.

## Cost

Node 2141648: A100-PCIE-40GB at ¥2.80/h, 10:35–11:25 ≈ **0.85 h ≈ ¥2.4**, of which ~13 min is the 12k-step finetune,
~3.5 min the saliency pass, ~10 min the five encodes and ~2 min the seven renders; the rest is the COLMAP fetch that
a fresh node always pays (the model came from `/mnt/m35cache`).

**Correction (2026-11-17 13:20, before any M52 data).** §"C2" said geometry was "≈11.4 of 13.41 B/primitive (85 %)". That was
an extrapolation from two colour points and it double-counted the colour block. The measured stream attribution
(`experiments/artifacts/a4/m24_encode_streams.txt`, gp8-6-6_c9 at 13.60 B/primitive) is: positions 3.38, quaternions
2.95, scales 2.04, opacity 0.70, headers 0.09 = **9.16 B/primitive of geometry (67 %)**, and colour 3.03+0.60+0.71 =
**4.34 B (32 %)**. The shipping `gp6-6-6_c8` row has the same split within a point. Nothing in the round's verdict
changes — the container still costs 0.39 dB — but the geometry share is two thirds, not 85 %, and the colour block is
4.3 B/primitive, not "inside 2 B". The corrected number is what M52 trades against.
