# M53 — the anchor prototype is cheaper than the container and currently renders nothing usable

**Round 45, node 2141852 (RTX 4090, ¥2.20/h), 2026-11-17 14:35–16:05 ≈ ¥3.3.** The first node round in eleven
attempts (16区 A100 was sold out all day; the 4090 pool in 亚太2区 was the only usable card). The byte side of the
anchor prototype works and lands **below the 2.8 B/primitive bar**; the reconstruction it writes renders at
**10.9–12.4 dB against a 24.52 dB control**, and the defect survived every check this round could afford.

## What was measured

Control: the untouched published bicycle model (6,131,954 primitives) through the round's own probe → **24.52 dB**
(exactly the M16 clean number, so the render path is sound).

| arm | geometry B/prim | positions | attributes | PSNR | Δ vs control |
|---|---|---|---|---|---|
| anchor k=3, 4-bit offsets, scalar attrs | 7.51 | 1.43 | 6.08 | 12.08 | −12.44 |
| anchor k=3, 4-bit offsets, VQ-64 | **2.15** | 1.43 | **0.72** | 10.88 | −13.64 |
| anchor k=3, 4-bit offsets, VQ-256 | 2.39 | 1.43 | 0.96 | 11.53 | −12.99 |
| anchor k=1, 8-bit offsets, scalar attrs | 9.05 | 3.12 | 5.92 | 11.85 | −12.67 |
| anchor k=1, 8-bit offsets, VQ-64 | 3.84 | 3.12 | 0.72 | 12.40 | −12.12 |
| k=1, 8-bit, 12-bit attributes (near-lossless attr) | 15.52 | 3.12 | 12.40 | 11.85 | −12.67 |

Three readings:

1. **The byte side is real and below the bar.** Geometry at **2.15 B/primitive** with joint VQ-64 — against the
   shipping container's 9.16 — with positions at 1.43 B/primitive once primitives are sorted by anchor (the first
   run, in model order, spent 7.7 B/primitive on the anchor-index stream alone; sorting fixed it).
2. **The distortion side is broken, and it is not the attribute budget.** Making the attributes near-lossless
   (12-bit scalar, 12.4 B/primitive) changes the render by **0.00 dB**. Whatever costs 12 dB is not quantiser width.
3. **It is not the writer, the colour permutation, or the positions.** An identity round trip through
   `load_inria_ply → save_inria_ply` renders **24.52**; the SH permutation bug (the prototype sorted primitives but
   wrote colour in the original order) was found and fixed and changed nothing (−12.7 → −12.1 dB); position RMSE is
   **0.033** against an offset step of 0.063, i.e. inside the quantisation bound; per-field reconstruction error is
   small (quaternion 0.0065, log-scale 0.085, logit-opacity 0.083) and the marginal distributions of means, scales and
   opacities match the original to the second decimal at p1/p50/p99.

## Verdict — `prototype_not_valid` (R1 undecided, **not** a kill)

The pre-registered R1 (≤ 2.8 B/primitive at ≤ 0.4 dB) is **not met**, and the reason is a defect in the prototype,
not evidence about anchors. `PLAN_REPRESENTATION.md` says a failed G2 stops the programme; that rule should **not** be
applied here, because the round did not produce a valid reconstruction to judge. The honest status is: byte side
passes, distortion side unmeasured.

## What the next attempt must do first

Localise the defect with a *rendered-pixel* unit test rather than aggregate statistics: take a 200-primitive scene,
encode/decode it through the prototype, and compare the two images pixel by pixel while zeroing one field at a time
(positives, scales, quaternions, opacity, colour). The 12 dB is far larger than any single field's measured RMSE, so
one of the fields must be mis-wired in a way that means and percentiles do not show — the sign/order of a quaternion
component and the opacity logit/sigmoid round trip are the two candidates this round did not isolate.

## Process failures, recorded

* The node was released **before** the artifact bundle was downloaded, so `experiments/artifacts/a4/m53g3/` is empty
  and every number above comes from in-session reads of the logs. The rule for the following rounds: fetch the bundle,
  *then* release.
* `tail` is unusable through this harness on the MatPool images (`tail -4` → "option used in invalid context"), and a
  script that pipes `python | grep` silently swallows the failure. Both cost node time this round; `sed -n 1p`,
  `awk 'END{print}'` and direct redirection to a file are the fixed replacements and are now in the round's scripts.
* 1.5 h of a 4090 at ¥2.20/h is the cheapest node hour this project has used; the data staging that dominated previous
  rounds took 8 minutes here (28 MB/s from hf-mirror, versus 180 kB/s in 1区). **If A100 stays unavailable, 4090 in
  亚太2区 is the right fallback** — its 24 GB is enough for 1.5 M-primitive training at factor 4.

## Addendum (round 46): the 12 dB defect is a coding-geometry bug, not a quantiser bug

CPU experiments on a bicycle-like generator localised it. (1) Offsets were coded around the cell **mean**, so
primitives near cell corners were clipped by up to 0.87·cell: 1 % of primitives displaced by up to 1.42 world units,
which is invisible in mean/percentile error statistics and fatal in a render. Anchoring at the cell **centre** drops the
max error to 0.18 and the outlier tail to 0.00 %. (2) The spacing estimator measured inter-cluster distance on a random
subsample (1.05 against a true 0.06), making the cell 20× too large; it is now a density estimate, which is better but
still biased on clustered data. The real conclusion is that a spatial grid is the wrong grouping for 3DGS data — the
container clusters by **count** (256 primitives in Morton order), and the prototype should do the same before it is run
again. The next node round should therefore start from count-based anchors, not from another parameter sweep.

## Addendum 3 (round 49): G2 measured on real data — the prediction cannot pay for the anchor

No usable GPU again (only A30/A4000/P100, whose pools reject the CUDA 12.4 image), but the decisive part of G2 does not
need one: the question is whether the attribute block can be coded at ~1 B/primitive, and that is a distortion question
in attribute space. Bonsai's published checkpoint (1,244,819 primitives, 309 MB) was downloaded locally and run through
the prototype's attribute path with the container's own count-based clustering (256 per cluster, Morton order).

| quantity | value |
|---|---|
| prediction residual RMS (ridge on anchor features + position) | quat 0.225, log-scale 1.36, logit-opacity 3.80 |
| scalar 6-bit quantisation of the same residuals | quat 0.0092, scale 0.094, opacity 0.096 |
| **joint VQ-64, 1.01 B/primitive** | **RMS 0.55** |
| joint VQ-256, 1.03 B/primitive | RMS 0.43 |
| joint VQ-1024, 2.11 B/primitive | RMS 0.35 |

**The residual is not low-dimensional on real data.** At one byte per primitive the joint codebook reproduces the
residual about **six times worse** than the container's scalar path at 4.3 B/primitive (0.55 against ~0.07 combined).
The container loses **0.39 dB** at that 4.3 B budget (M49); an attribute error six to eight times larger cannot plausibly
stay under the 0.4 dB R1 bar, and VQ-1024 only halves the gap while doubling the bytes.

The earlier "0.72 B/primitive" on synthetic data was an artefact of the generator: those attributes were *produced from*
the anchor, so the residual was near-zero by construction. This is the risk `PLAN_REPRESENTATION.md` §5 named first, and
it is now measured rather than suspected.

**Verdict: G2 FAILS → `prediction_cannot_pay_for_the_anchor`.** Under the pre-registered kill rule the anchor-plus-
prediction route stops here. The one branch that would survive is a *trained* predictor (G3 in the plan): a ridge
regression cannot see the structure that a learned model might, and the residual RMS of 0.225/1.36/3.80 shows how much
structure is left unexplained. That is a 2–3 month programme with the arithmetic still against it (M52: even free
geometry only buys +0.9 dB from the extra primitives), so the recommendation is **not** to fund it without an external
reason.
