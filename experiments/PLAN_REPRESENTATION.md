# Plan: rebuilding the representation (the only route left to the mid-rate)

**Written 2026-11-17 15:55, round 44.** Every cheap lever is measured and closed; this document is what a rebuild would
have to be, what it would cost, and where it would be killed. It exists so the decision is taken on arithmetic rather
than on hope.

## 1. What is closed, and why

| lever | rounds | verdict |
|---|---|---|
| entropy coding of the existing streams | M20, M21, M29 | streams are at their order-1 entropy; context coders move < 0.1 % |
| quantiser / geometry widths | M50, M51 | 0.30–0.90 dB per byte saved |
| pruning fraction and score | M39, M47, M48 | score fixed (+1.6…+3.2 dB); fraction at both ends loses |
| colour basis / VQ / PQ | M9–M12, M22 | rank 16 + 48 bit is the local optimum; more bits buy +0.17 dB for +50 % bytes |
| rate pressure, supervision resolution | M26, M36, M39 | constant ~5–7 % byte lever, not a quality lever |
| post-hoc finetune length | M17, M18 | 0.026 dB/1 000 steps, flattening; 90 k steps would be needed for 2.4 dB |
| allocation between geometry precision and primitive count | M52 (analysis) | loses by 4–12× in dB per byte |

The measured wall: **selling geometry bytes costs 0.30–0.90 dB/byte; buying primitives pays 0.075 dB/byte.**

## 2. What the published frontier does that we do not

HAC and PCGS both (a) prune *during* training rather than after it, and (b) code attributes through a
**reconstruction-aware** model — anchors plus vector-quantised residuals whose codebooks are fitted with the renderer in
the loop. Our container codes each primitive's attributes independently at fixed widths, and our model never sees the
quantiser. That is the whole difference, and it is why their bytes are cheaper *at equal distortion* rather than merely
fewer.

## 3. The build

**Stage A — geometry (prototype exists).** Anchor grid + offsets for positions, `experiments/m53_anchor.py`:
positions 2.69 B/primitive on synthetic data, 1.53 M primitives in 37 s on CPU. Needs no GPU to iterate.

**Stage B — attribute prediction (prototype exists, untrained).** Ridge on anchor features + the primitive's own
reconstructed position. On synthetic data with anchor-generated attributes it takes the attribute block from 5.95 to
1.01 B/primitive through joint VQ-256. **This is the number that must survive real data.**

**Stage C — train through the code (new work).** Replace the ridge with a small MLP (2 hidden layers, ~64 units,
input = anchor features + offset) trained jointly with the renderer; quantise residuals with a straight-through
estimator; add the existing log-rate term (M36) on the codebook usage. Changes are confined to `train_gs.py` plus a new
`experiments/m53_train.py`; the container stays the shipping one so every row remains comparable.

**Stage D — evaluation.** Equal bytes against the M49 control (19.47 MB / 22.63 dB) and against the saliency arm
(19.45 MB / 22.67 dB), on bicycle, 25 held-out views, same probe, same factor; then the two-scene check (bicycle + stump)
with the protocol-bias statement; bonsai stays internal-only until its 4.1 dB baseline gap is explained.

## 4. Gates and kill criteria

| gate | question | pass | kill |
|---|---|---|---|
| **G1** (done) | does the prototype run at 1.5 M primitives? | yes, 37 s CPU | — |
| **G2** | on a real PLY, does geometry reach **≤ 2.8 B/primitive at ≤ 0.4 dB** loss? | both clauses | `prediction_cannot_pay_for_the_anchor` — stop, do not rent again |
| **G3** | trained (Stage C), does the equal-bytes point beat 22.67 dB by **≥ 0.3 dB**? | yes | `training_does_not_close_it` — the representation, not the training, is the limit |
| **G4** | does it land within **1.0 dB** of PCGS at 19 MB (i.e. ≥ 24.1 dB)? | yes | publish as a near-lossless/robustness codec, mid-rate reported honestly |

G2 costs one node round (~40 min, ¥2). G3 costs 4–6 rounds (training + encodes, ~¥25). G4 is the full programme (~3
months, ¥80–120 at the observed rate).

## 5. What could still make this fail

* **The residual entropy may not be there.** Our synthetic data had attributes generated *from* the anchor; real scenes
  have per-primitive detail that no anchor predicts. If the real VQ residuals sit at 3–4 B/primitive rather than 1, the
  arithmetic loses and G2 kills the programme — which is exactly why G2 is one cheap round.
* **Training instability.** STE + VQ + renderer loss is where most implementations die; budget two rounds for debugging
  before counting any quality gain.
* **The comparison may not move even if bytes do**, because the primitive count is bounded by the same file size: at
  19.5 MB and 6.9 B/primitive we carry 2.8 M primitives, and M18's exchange rate says +1.27 M primitives is only
  +0.9 dB. The representation has to deliver the rest.

## 6. Decision

Do **G2** as soon as a 16区 A100 exists. If G2 fails, stop the compression programme at "near-lossless + robustness +
audited negative results", which is publishable if framed as such, and put the remaining effort into the certificate
paper. If G2 passes, fund G3 (≈¥25) but not G4 without a second gate.
