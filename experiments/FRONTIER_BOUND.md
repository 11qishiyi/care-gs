# The arithmetic of the near-lossless shelf

Written 2026-11-14 as part of round 10, after the DPCM pilot (N23) failed and before any further
codec was built.  **Corrected 2026-11-15 after M15 measured the geometry packing** (round 11): the
SH term is 20.0 B not 18.9 B, the packed shelf measures 21.7 B / 10.87x not 20.2 B / 11.7x, and the
"geometry packing is free" assumption it rested on is false -- see N24 and `M15_RESULTS.md`.  The
question it answers: **can post-hoc coding reach 12x at a coverage loss of 0.3 points?**  The
answer, from measured bytes rather than a model, is no — not with any SH bit width that survives,
and not with any plausible saving on the geometry.

## 1. What the shelf costs today

Measured bytes (`zstd+morton`, level 12) and the coverage loss at the same variant, eight assets:

| variant | B/prim (bicycle) | rate | loss (pp) |
|---|---|---|---|
| `sh4_g32` (published, SH 4 bit) | 59.2 | 3.99x | -0.02 |
| `sh4_g16` | 48.0 | 4.92x | -0.46 |
| `c10_o8_sh3` | 25.4 | 9.29x | **-0.24** |
| `c8_o8_sh3` | 24.5 | 9.63x | -0.31 |
| `c8_o8_sh2` | 16.8 | 14.04x | -2.18 |
| `m16_o8_sh2` | 28.0 | 8.43x | -2.52 |

The step from 5x to 9.3x is bought almost entirely by SH: 4 bits down to 3 bits, i.e. 48
coefficients x 1 bit = 6.0 B, plus dropping the geometry from fp32 to 8-bit grids.  The step from
9.3x to 14x is bought by 3 bits down to 2 bits, and it costs two points of coverage.

## 2. What 12x requires

`rate = 236 / (bytes per primitive)`, so 12x means **at most 19.7 B per primitive**, measured with
the coder we ship.  The cheapest near-lossless variant measures 25.4 B: 20.0 B of it is SH at
3 bits and the rest is geometry.

Geometry is 11 scalars: 3 position + 3 log-scale + 4 quaternion + 1 opacity.  Three of the four
groups were assumed to pack far below 8 bits without touching coverage (M15 tested this and was
wrong on all three -- N24):

| group | today | packed | what happened when measured |
|---|---|---|---|
| quaternion | 4.0 B (32 bit grid) | **3.25 B** | free: st3 at 26 bits beats the 32-bit grid, 6 bit costs 0.00 pp |
| log-scale | 3.0 B | 1.9 B | 5 bit costs **0.14 pp** |
| opacity | 1.0 B | 0.5 B | 4 bit costs **0.31 pp** |
| position | 3.75 B at c=10 | 2.25 B at c=6 | c=6 costs **0.56 pp** |
| block header | 0.09 B | 0.09 B | unchanged |

That is 14.84 B down to 7.97 B: a **6.88 B** model saving, but **1.01 pp** of measured coverage
cost, against a shelf tolerance of 0.5 pp.  The quaternion figure is the one part that was not
taken on faith: 11 bits looked attractive and was measured to fail (12.6 degrees of mean rotation
error against 0.43 for the 32-bit grid), so the gate settled on 26 bits, which reconstructs at
2.96e-3 L2 against 3.73e-3, i.e. slightly *better* at 6 fewer bits.  It is also the only group
whose representation changed; the other three merely dropped bit width, and dropping bit width is
what costs coverage.

## 3. The bound

Two facts, both measured, pin the shelf:

1. SH at 3 bits costs 0.11-0.42 pp (`c10_o8_sh3` across the eight assets), SH at 2 bits costs
   1.46-6.16 pp (`c8_o8_sh2` against `c8_o8_sh3`).
   Nothing in between exists on our bit grid -- and M9-M12 showed that no other SH representation
   (single codebook, two-stage residual, per-primitive mode selection, product quantisation,
   prediction) lands between them either; the best of them sits at the 2-bit quality level.
2. The geometry can be squeezed to 7.97 B, but not for free: measured 0.44-3.41 pp, median 1.32 pp
   (M15, N24).  The earlier "about 6 B and no further without losing the lossless part" was a
   guess in the right direction but with the cost attached to the wrong end of the shelf: the
   lossless part does not degrade gradually, the first step below 8 bits is already visible.

So at 3-bit SH the floor is `20.0 + 7.97 = 27.97 B` model, **21.7 B measured** (zstd removes 22%,
not a quarter: the packed streams are already near entropy), i.e. a **10.87x** rate -- but at
1.32 pp of loss.  There is no point at or below 0.5 pp above 9.7x: every variant we have that is at
or below 0.5 pp sits at **9.0-9.7x**, and M15 found no packed row inside 0.5 pp above 9.00x on any
asset.  The remaining 3.7 B to 12x would have to come out of the 20 B of SH, where nothing between
3 and 2 bits survives.

**Corrected by M22 (round 18).**  The arithmetic above is right about *independent* numbers and wrong
about the block: the 45 rest coefficients live in a rank-16 subspace that the whole asset can share.
Measured on bicycle, a rank-16 basis at 48 bits per primitive renders **24.12 dB against the shelf's
24.33** -- 0.21 dB -- in **98.53 MB against 144.55 MB**, i.e. **14.69x** instead of 10.01x.  Stump
agrees: 80.72 MB / 25.57 dB against 118.88 MB / 25.81 dB, **14.51x at -0.24 dB**.  Twelve times is
therefore reachable *today* for this family and almost free: 12x means 19.67 B, of which geometry and
DC take 8.58, leaving **89 colour bits** -- between the measured 64-bit point (13.63x, -0.05 dB) and
the 96-bit point (10.58x, -0.01 dB), i.e. about **-0.03 dB**.  The identity
`20.0 B of SH` was never a property of the model; it was a property of coding 45 columns independently.
See `M22_RESULTS.md`.

**Corrected again by M23 and M24 (rounds 19-20).**  The same model, with smallest-three quaternions
(M23: 26 bits instead of 32, **0.00 dB**) and then three container repairs (M24: one scale level instead
of two, 6-bit scales/opacity, 9-bit positions), reaches **83.41 MB = 17.35x at 24.08 dB** -- 0.04 dB
under the 45-column shelf.  Measured ladder on bicycle: 93.30 MB / 15.51x (M23) -> 89.72 MB / 16.13x
(lossless container fix, bit-identical model) -> 85.71 MB / 16.88x (-0.03 dB) -> 83.41 MB / 17.35x.
The largest single step in that sequence, 3.58 MB, came from a `sh_scale` level the decoder never read
(N32).  See `M23_RESULTS.md`, `M24_RESULTS.md`.

Twelve times with a near-lossless guarantee is therefore not a coding problem that better
quantisers can solve; it is a budget identity — **and M22 broke the identity, not the quantisers**.
The honest claims are now: zero loss down to 2.83x, at most 1 pp down to 5.2x, 2.9-20.9 pp less
damage than the published formats from 5.5x upwards, and **17.35x at 0.04 dB** (1.7x further out than
the M22 point, 34 % further than the old shelf, with the same guarantee).

## 4. What this changes

- M15 (geometry packing) was done and failed: measured +1.2x in rate (9.28x -> 10.87x) at 1.32 pp
  median loss, 2.6x the tolerance, 1/8 on every R1 pair.  N24 records it.  The "+2.2x (9.5x ->
  11.7x)" expectation written here on 2026-11-14 was wrong on both the rate (10.87x, not 11.7x) and
  the cost (not free).
- Nothing further should be aimed at 12-20x near-lossless.  The 12x claim in the goal is
  unreachable with post-hoc coding, and that should be stated rather than chased.
  **Superseded by M22**: with a shared rank-16 colour basis, 12x is reachable at about -0.05 dB
  (13.62x measured) and 14.69x at -0.21 dB.  What was unreachable was 12x with 45 independent
  coefficients per primitive.
- The one lever this arithmetic still leaves open is entropy coding of the SH block (the 20 B that
  dominate the shelf), which no round has tried yet.  **Tried in M20 and it did not work** (N29:
  every context bound was worse than zstd).  The lever that worked was structural (M22), not
  statistical.

## 5. Where the series stops: 48x is a different representation (M17, 2026-11-15)

The bound above is about the near-lossless end.  M16-M17 measured the other end against HAC and
PCGS on bicycle, which is the only place where an external number exists at 48x:

- our cheapest coder (q12_c8_o8) costs **11.90 B** per stored primitive after zstd-12 + Morton;
  27.54 MB -- HAC's bicycle file, 48x on the same 1336 MB base model -- therefore buys **2.31 M
  primitives**, and the base model has 6.13 M, which would need 4.49 B/prim;
- at the primitive count the budget allows, our best model (35 % keep + 8000 finetune steps) reads
  **21.81 dB clean / 21.51 dB coded**; 30 000 steps (M18) move that to **22.54 dB clean / 22.08 dB
  coded**, i.e. +0.57 dB for 3.75x the training, against HAC's 25.05 dB;
- 50 % keep (3.07 M) is 22.67 dB clean but needs 36.5 MB, 33 % over the budget.

So the series has no operating point at 48x at all, and the shortfall is two-term: bytes (4.49 B
needed, 11.90 B available) and fidelity (1.98 dB lost to pruning at the affordable primitive count,
even after 30 000 finetune steps).  Closing the fidelity term by training would need a pruned subset
0.5 dB *better* than the 6.13 M model it came from, which no schedule we measured approaches.  Both come from paying for a per-Gaussian SH.  HAC/PCGS reach 48x because their colour is an
MLP over sparse anchors, so 4.5 B/primitive is coherent for them.  Any future round that aims at
the mid-rate regime has to change the representation, not the quantiser.

**Closed by M26 (round 22, 2026-11-16).**  The last untested explanation for the mid-rate gap was that
our recipe trains at factor 4 while the published codecs train at factor 1-2.  Measured as a paired
experiment on the same 1.53 M-primitive prune: factor 4 gives 21.40 dB in 731 s, factor 2 gives 21.33 dB
in 2 276 s -- **3.1x the wall time for -0.07 dB**, with monotone eval curves in both arms.  Encoded at
20.9-25.0 MB the two arms stay within 0.15 dB of each other and within 0.3 dB of the raw model.  HAC sits
at 27.54 MB / 25.05 dB, PCGS at 19.09 MB / 25.12 dB, so the shortfall is -3.8 dB at comparable bytes and
it is not training, not coding and not supervision.  N33 records it.  The sentence above stands with no
qualification left: **any future round that aims at the mid-rate regime has to change the representation**.

## 6. Where the mid-rate row stops: an anchor that stores a constant (M27, 2026-11-16)

Written after M27 measured the anchor representation.  The question: **is the 20-30 MB row winnable by
paying for attributes once per voxel instead of once per primitive?**

The bookkeeping side of the answer is yes, emphatically.  The full published bicycle model (6,131,954
primitives) fits in **15.42 MB = 2.52 B per primitive** at 16 primitives per voxel, and 21.75 MB =
3.55 B at 8 — against the shelf's 13.60 B on the same model.  The identity in N25-N27 that a
per-primitive attribute record costs ~16 B and therefore cannot fit in 27.5 MB is correct and is
beaten by construction.

The rendering side of the answer is no.  The same container renders 13.86 dB (15.42 MB), 16.05 dB
(21.75 MB) and 17.92 dB (33.25 MB), against 24.52 dB for the source and 21.24 dB for our pruned and
fine-tuned model at 24.96 MB.  At 24.07 MB the anchor file renders 16.97 dB: **4.3 dB below pruning
at equal bytes, with 3.8x fewer bytes per primitive**.

The attribution is measured rather than argued, one attribute at a time:

| term | cost |
|---|---|
| position quantum, 3-bit offsets inside a 10.67 cm voxel (1.33 cm) | **1.72 dB** recovered by 5-bit offsets |
| constant scale inside a voxel | **2.46 dB** recovered by keeping scale per primitive |
| constant opacity | 0.29 dB |
| constant rotation | 0.09 dB |
| shared rest colour | ≈ 2 dB at equal bytes |

So the bound this document has been tracking all along was never "bytes per primitive".  A rate is
`(bytes, the reconstruction the representation is allowed to make)`.  Constant sharing halves the bytes
and quarters the fidelity, and the image prefers exact attributes: pruning keeps every attribute and
drops primitives, anchors keep every primitive and blur the attributes that matter.

The distinguishing feature of the methods that do win this row (HAC, PCGS) is not that they group by
voxel — this round did that and lost 4 dB — but that the voxel's contents are **predicted** from the
anchor feature and the offset by a small network.  Their per-primitive scale and rotation are not
stored and not constant; they are decoded.  Every measurement here is consistent with that design
being the right one, and none of it can be reached by tuning quantisers: the next round is a training
round, with one candidate.

**Status of the frontier table.** Near-lossless row unchanged by M27 (17.35x at 24.08 dB, M24).  The
mid-rate row keeps its measured envelope: ≤30 MB reaches 21.24 dB (M26) and 23.80 dB is not reachable
by pruning, by supervision or by constant-sharing anchors — the three explanations that have now been
priced.

---

## 7. The predictor was built, and it was asked to invent bits it never received (M28)

§6 ended with a hypothesis: the winners of the mid-rate row do not store constants, they *predict* the
primitive from its anchor and its offset, and the next round should be a training round with one
candidate.  That round is done and the candidate lost — but it lost in a way that converts the
hypothesis into arithmetic, which is worth more than another 0.1 dB.

`experiments/m28_pred.py` adds a 10 → 64 → 64 → 7 MLP (10.6 kB of float16 weights, inside the
container) that maps the anchor's seven attribute numbers plus the primitive's offset inside the voxel
to Δlog-scale (3), a rotation vector composed with the anchor's rotation, and Δlogit opacity.  Per
primitive the file pays only a 4-bit offset and the DC code.  Measured on bicycle's 6,131,954
primitives at 8 primitives per voxel:

| container | file | B/prim | PSNR |
|---|---|---|---|
| M27, constant attributes, DC 6 | 29.62 MB | 4.83 | 16.26 |
| M27, constant attributes, 4-bit offsets, DC 6 | 24.07 MB | 3.93 | 16.97 |
| **M28, predicted attributes, 4-bit offsets, DC 4** | **27.13 MB** | **4.42** | **17.04** |

**+0.08 dB.**  The network is not broken: on a synthetic world where scale and opacity really are
functions of the offset, the identical architecture reaches a loss of 1e-5 in 500 steps
(`tools/m28_control.py`).  On the real model the loss falls from 9.665 to 9.016 in the first thousand
steps and never moves again, and the entire gain is an opacity bias.

The reason is not capacity — it is information.  A voxel's mean explains, at this grid, 62.8 % of the
scale variance, 37.8 % of the opacity variance and 59.5 % of the rotation variance:

| primitives per voxel | 4 | 8 | 16 | 64 | 256 |
|---|---|---|---|---|---|
| R² scale | 0.742 | 0.628 | 0.538 | 0.412 | 0.338 |
| R² opacity | 0.531 | 0.378 | 0.274 | 0.161 | 0.107 |
| R² rotation | 0.733 | 0.595 | 0.473 | 0.287 | 0.171 |

An anchor record is 58 bits; its eight members carry 8 × 58 = 464.  The anchor holds exactly the 58
that are redundant, and 37–62 % of every attribute's variance is in the part it does not hold.  No
decoder can recover what the file never contained.  Coarsening the grid makes this worse, not better
(R² falls monotonically with primitives per voxel), so "bigger anchors, bigger network" is not the fix
either.

**What survives as the honest reading of the mid-rate row.** Three post-hoc explanations are now
priced and excluded: supervision resolution (N33, −0.07 dB for 3.1× compute), anchor representation
(N34, −4.3 dB at equal bytes), and a per-primitive predictor on top of it (N35, +0.08 dB).  The
remaining difference between 21.24 dB @ 25 MB and HAC's 25.05 dB @ 27.5 MB is therefore attributable
to the one thing none of these rounds built: **learned per-anchor latents trained jointly with the
decoder under a rate–distortion objective, with entropy-coded residuals and a rendering loss** — i.e.
a different training programme, not a different quantiser.

That is a scope decision, and this document takes it explicitly: the near-lossless row (17.35× at
24.08 dB, 10.01× container with a 1.97 GB / 7.69 s decoder) is this project's contribution, and the
mid-rate row is reported as measured, with the three negative results that bound it.

**Frontier table status.**  Near-lossless: unchanged, 17.35× at 24.08 dB (M24).  Mid-rate: 21.24 dB at
24.96 MB (M26) remains the best this pipeline reaches without a jointly trained decoder; the
anchor family is the cheapest container at any fidelity (2.52 B/primitive, 15.42 MB, decode 3.4 s) and
is kept for low-LoD and progressive use, not as a mid-rate competitor.

---

## 8. The codes were already at their entropy; the widths were not (M29)

§7 ended by excluding three post-hoc explanations of the mid-rate gap and by asserting that the
near-lossless row was finished at 17.35×.  M29 tested the one coder-side lever that assertion assumed:
if the attribute codes carried structure zstd could not see, a context-aware coder would take it.

They do not.  Measured on the shipped container, per stream (zstd bits per code against the order-0 and
order-1 entropies of the same codes):

| stream | width | B/prim | zstd b/code | H0 | H1 |
|---|---|---|---|---|---|
| position offsets | 10 | 3.750 | 10.00 | 9.99 | 9.90 |
| scales | 8 | 2.501 | 6.67 | 6.82 | 6.78 |
| rotation (which) | 2 | 0.103 | 0.82 | 0.95 | 0.77 |
| rotation (abc) | 8 | 2.953 | 7.88 | 7.76 | 7.75 |
| opacity | 8 | 0.896 | 7.17 | 7.18 | 6.96 |

zstd is *at or below* the order-1 bound on the two streams that dominate, and every context a decoder
could compute (coarse spatial band, the primitive's own scale) lands within 0.1 % of plain zstd.  The
container is not failing to compress its codes; the codes are entropy.

What that leaves is the widths — and there the probe found the one number that is pure choice: the
10-bit position offset codes at exactly 10.00 bits, so it is uniform by construction and costs
3.75 B/primitive.  A four-point sweep on the same colour block:

| spec | file | B/prim | ratio | PSNR |
|---|---|---|---|---|
| `gp8-8-8_c9` | 87.43 MB | 14.26 | 16.55× | 24.11 |
| `gp7-7-7_c9` | 85.64 MB | 13.97 | 16.90× | 24.10 |
| `gp6-6-7_c8` | 77.43 MB | 12.63 | 18.69× | 24.06 |
| **`gp6-6-6_c8`** | **76.56 MB** | **12.49** | **18.90×** | **24.06** |

**The near-lossless row is now 18.90× at 24.06 dB** (was 17.35× at 24.08 dB), decoded in 7.51 s and
1.96 GB — +9.0 % ratio for 0.02 dB, with the decoder untouched.

The sweep also explains why the curve is shallow where it is: coarsening a stream by one nominal bit
saves *less than a bit* wherever zstd was already below the width.  Removing three bits per primitive
(P0 → P1) bought 1.8 MB where the arithmetic predicts 4.9 MB.  That is the same fact as the entropy
table, seen from the other side.

**Status of the frontier.**  Near-lossless: **18.90× at 24.06 dB**, 12.49 B/primitive, 1.96 GB decoder.
Mid-rate: unchanged at 21.24 dB / 24.96 MB (M26); the anchor family (M27–M28) is the cheapest container
at any fidelity and does not compete on the row.  Every coder-side and quantiser-side lever is now
measured; what remains on both rows is a representation or a training programme, not a code change.

## 9. And the widths were already an allocation (M30, 2026-11-16)

M29 ended with one lever on the table: the near-lossless container codes each position offset at 8 bits
on a grid over its own 256-primitive cluster box, so a per-cluster width looked like free money.  It was
not.  Eight allocations were built and rendered, and every one of them lost:

| allocation | file | ratio | PSNR |
|---|---|---|---|
| fixed 8 bit | 76.56 MB | 18.90x | **24.06** |
| constant step, one bit coarser | 75.56 MB | 19.14x | 23.89 |
| constant step, 1.8 bits coarser | 73.37 MB | 19.72x | 23.48 |
| constant step, 2.4 bits coarser | 72.29 MB | 20.02x | 22.90 |
| budget-neutral tilt toward dense | 76.76 MB | 18.85x | 23.98 |
| budget-neutral tilt toward sparse | 76.71 MB | 18.86x | 24.03 |

The measurement that explains it: with a fixed width, the absolute position error is proportional to the
cluster extent, and the ratio is constant — 0.00134 in every size quartile.  The grid therefore delivers
0.13 % relative precision at every density, which is precisely what the renderer rewards; equalising the
absolute step instead takes the densest quartile's mean error from 0.25 mm to 2.39 mm and costs 0.58 dB
for 4 % of the file.

So the near-lossless row is **18.90x at 24.06 dB, 12.49 B/primitive**, and every block of it now has a
measured reason: the colour block is a shared rank-16 basis (M22), the DC and geometry widths are at their
entropy (M29), the position grid is a rate allocation in local units (M30), and the container is a single
self-describing file that decodes in 7.5 s under 2 GB (M19, M25).  12x was reached in M22 and is now
reached at 0.04 dB of the source; going below 12.5 B/primitive means giving up the per-primitive
representation itself, which is where the mid-rate experiments (M27, M28) already looked and lost.

## 10. The row is one scene wide, and now it is three (M31, 2026-11-16)

Every number in section 9 is a bicycle number.  M31 built the same container, unchanged, on the three
scenes the pretrained release publishes (bicycle, stump, bonsai -- every other name 404s), and the row
splits in half:

| scene | primitives | file | B/prim | ratio | clean dB | ours dB | delta |
|---|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 76.56 MB | 12.49 | 18.90x | 24.52 | 24.06 | -0.46 |
| stump | 4,961,797 | 62.59 MB | 12.61 | 18.71x | 26.15 | 25.52 | -0.63 |
| bonsai | 1,244,819 | 15.30 MB | 12.29 | 19.20x | 28.06 | 27.08 | -0.98 |

The **rate** is scene-invariant: 12.3-12.6 B/primitive and 18.7-19.2x on all three, with two of the three
better than the scene the configuration was tuned on, because the per-stream shares vary by less than a
percentage point across a 5x range of primitive counts.  The **distortion** is not: 0.46, 0.63, 0.98 dB.

The gap is not rate.  Re-encoding bonsai at the generous end of the M29 scan buys 0.11 dB for 17 % more
bytes (27.08 -> 27.19 dB), so the container sits on the saturation shoulder there and the residual
0.87 dB belongs to the colour block -- a rank-16 basis with 48 bits of coefficient, which runs out of
colour on an indoor scene whose detail is high-frequency at the scale of 1.2 M primitives.

So the correct form of the near-lossless claim is a table, not a sentence: **18.7-19.2x at 0.46-0.98 dB
below the source, per scene**, with the byte budget and the decode cost (7.5 s / 2.0 GB on the largest
scene, 1.4 s / 0.5 GB on the smallest) holding everywhere.  Any single-scene "<=0.5 dB at 19x" statement
undercounts by a factor of two on the scene that matters least favourably.

Where that leaves the frontier: the near-lossless row is settled at 12.5 B/primitive with every block
allocated for a measured reason; what is not settled is how much of those bytes a *scene-adaptive* colour
block could buy back.  Bonsai's 0.87 dB is the size of that prize, and it is a representational question,
not a rate one -- the same conclusion M27 and M28 reached from the mid-rate side.

## 11. The colour residual is a quantiser, not a subspace (M32, 2026-11-16)

Section 10 ended with one named residual -- bonsai's 0.87 dB -- and one guess: that the rank-16 colour
subspace runs out of colour there.  M32 measured that guess on three scenes by holding the raw colour
budget at 48 bits per primitive and trading subspace for precision.

| plan | bicycle | stump | bonsai |
|---|---|---|---|
| r16_b48 (shipping) | 76.56 MB / 18.90x / 24.06 | 62.59 MB / 18.71x / 25.52 | 15.30 MB / 19.20x / 26.70 |
| r24_b48 (+2-3 % bytes) | 23.37 (-0.69) | 24.51 (-1.01) | 25.84 (-0.86) |
| r32_b48 (+4-6 %) | 22.63 (-1.43) | 23.74 (-1.78) | 24.79 (-1.91) |
| r8_b48 (+12-14 %) | 23.65 (-0.41) | 25.12 (-0.40) | 26.72 (+0.02) |
| r16_b64 (+10-12 %) | 24.22 (+0.16) | 25.68 (+0.16) | 27.02 (+0.32) |

The guess was wrong in an informative direction.  Widening the subspace at fixed bytes loses everywhere,
and loses *most* on the scene whose residual is largest -- the opposite of what "the subspace is too
small" predicts.  The residual is quantiser-side, and the price of buying it back is +16 bits of colour
per primitive for +0.16 / +0.16 / +0.32 dB at +10 / +10 / +12 % bytes.

Two consequences for the frontier:

* **The fidelity knob is now explicit and priced.**  The near-lossless row keeps one configuration for
  all scenes, because the rate model transfers (section 10); what a deployment can additionally choose is
  a per-scene colour budget, and that choice can be made **without rendering**: the plan that minimises
  coefficient error measured against the original 45 columns reproduces the render ranking exactly
  (Spearman -1.000 on all three scenes), while the cheaper metric that scores only the retained subspace
  gets it backwards (it ranks the rank-8 plan first).
* **The row's remaining headroom is small and expensive.**  Bonsai's 0.87 dB costs 12 % of the file; on
  bicycle and stump the same 16 bits buy 0.16 dB.  There is no cheap remaining decibel in this
  representation -- which is the same conclusion M27 and M28 reached from the mid-rate side, now measured
  at the top of the range as well.

A measurement caveat that the paper must carry: the bonsai control renders 26.70 dB here and 27.08 dB in
M31 for a same-size container, while bicycle reproduced to four decimals across the same two nodes.  The
container is byte-reproducible on a fixed build, so the difference is a rasteriser/build difference on a
1.2 M-primitive scene.  Every claim above is a within-round delta; absolute PSNR on the small scene is
quoted with that uncertainty.

## §12. Robustness: what a broken file renders at (M33, round 29)

The dimension this document had only ever measured mechanically — a burst kills one frame, positions do
not move (M19) — now has rendered numbers, and they are the first ones that depend on the *decoder* being
right about broken input rather than about its own output.

**The shipping container degrades, it does not fail.**  bicycle / stump / bonsai, control 24.06 / 25.52 /
27.08 dB:

| condition | bicycle | stump | bonsai |
|---|---|---|---|
| 0.10 % burst (one 4 MB frame) | 23.37 (-0.69) | 24.67 (-0.85) | 23.44 (-3.64) |
| 1.0 % burst (still one frame) | 23.37 | 24.67 | 23.44 |
| 5.0 % burst | 22.26 (-1.80) | 24.25 (-1.27) | 23.44 |
| prefix 50 % | 9.25 | 11.27 | 8.87 |
| prefix 90 % | 22.71 | 23.31 | 25.53 |

Geometry is byte-identical to the control under every corruption (means, scales, opacities, quats:
0.00 % changed in all 33 mechanical reports) because the damage lands in the colour block and the
geometry streams come first.  A damaged decode costs the same time and 3 % more memory than an intact one
(11.28 s / 2.08 GB vs 11.28 s / 2.01 GB on bicycle).

**This number was 3.4 dB worse one round ago and the difference was two bugs**, not the format: a tolerant
reader that did not keep a lost frame's length (so a hole shifted every later byte), and a basis alphabet
with no neutral symbol (so a lost frame decoded to its most negative coefficient).  Both are fixed; the
progression for one condition is 19.80 -> 16.51 -> 23.37 dB.

**The prefix ladder starts at 75 %, and no reordering moves it.**  Geometry is 70 % of the payload and a
zero scale covers no pixels, so a 50 % prefix is an *empty* render (9.25 dB), not a coarse one.  Writing
the same streams colour-first changes nothing (measured: 50 % still 9.25 dB).  A prefix decoder would need
a coarse predictor for geometry in the first half of the file — a different format, not a different order.

**The parameter that sets robustness is the frame, not the damage fraction.**  With 4 MB frames, 0.1 %-1 %
all destroy exactly one frame; 2 % two; 5 % three.  bonsai's entire colour block is one frame, so its
smallest possible corruption is its whole colour refinement — which is why it is the one scene that misses
the 2.0 dB criterion.  Intra-block ordering trades damage granularity for bytes: component-major puts one
component of 68 % of the primitives behind a single frame and compresses 17 % better than primitive-major
(M20), so the current layout is a deliberate choice with both sides now measured.

**What this adds to the comparison.**  Most 3DGS codecs publish a file size and a PSNR and nothing about
loss.  This one can now state, per scene, what the smallest detectable corruption costs (0.69 / 0.85 /
3.64 dB), what 5 % costs (at most 1.8 dB on the two large scenes), that geometry survives everything, and
that a truncated download is unreadable below 75 % — a limit of the dependency set, not of the container.

## §13. And the frame boundary is the knob (M34, round 30)

§12 ended with a defect it could name but not fix: bonsai's whole colour block is smaller than one 4 MB
frame, so its smallest detectable corruption cost 3.64 dB — the worst number on the robustness row, on the
one scene where the scene is smaller than the frame.

M34 moved the constant. On bonsai, with the shipping configuration unchanged, all three arms decoding to
the identical model:

| `MIN_FRAME` | file | `sh_coef` frames | one lost frame | 1 % burst | 5 % burst |
|---|---|---|---|---|---|
| 4 MB | 15,302,362 B | 2 | **−3.09 dB** | −3.09 | −3.09 |
| 1 MB | 15,352,658 B (+0.36 %) | 8 | −1.28 | −1.28 | −2.27 |
| 256 KB | 15,297,691 B (−0.03 %) | 29 | **−0.14** | −1.44 | −1.63 |

The smallest detectable damage falls **22×** and the file is 0.03 % *smaller*; decode time and memory are
unchanged (1.02×, 1.00×). The cost of a lost frame tracks the fraction of the colour block it covers, not
the bytes: 96 % → −3.09, 24 % → −1.28, 6 % → −0.14.

**What this changes in the comparison.** §12's robustness row was a statement about one format constant
wearing the costume of a property: bicycle and stump looked robust because 4 MB is 5 % of their colour
budget, bonsai looked fragile because 4 MB is all of it. With a 256 KB frame the row becomes a property —
the smallest detectable corruption costs ≤ 1.5 dB on every scene measured, and the frame count is the
knob that sets it. bicycle and stump are still owed the 1 % check (their models did not download inside
this round's budget; the P3 row is marked not measured, not extrapolated).

## §14. The curve, not the point (M35, round 31)

Every number this project has quoted is one point on a curve nobody had drawn. M35 drew it: six
configurations per scene, same code, same node, same run.

**bicycle** (6,131,954 primitives, clean 24.52 dB, 1447.1 MB payload):

| file | ratio | PSNR | Δ | frontier |
|---|---|---|---|---|
| 76.56 MB | 18.90× | 24.06 | −0.46 | yes |
| 69.34 MB | 20.87× | 23.80 | −0.72 | yes |
| 66.24 MB | 21.85× | 23.60 | −0.92 | yes |
| 57.23 MB | 25.28× | 22.53 | −1.99 | yes |
| 55.18 MB | 26.22× | 21.82 | −2.70 | yes |
| 69.30 MB | 20.88× | 22.82 | −1.70 | **no (dominated)** |

**stump** (4,961,797 primitives, clean 26.15 dB, 1171.0 MB): 62.59 MB/25.52 · 56.72/25.30 · 54.41/25.04 ·
47.46/24.42 · 45.75/22.32; dominated: 56.77 MB/22.70.

Three things this fixes in the paper:

1. **The floor is ~45–55 MB at fixed primitive count**, and the last point is already 9.00 B/primitive with
   7.97 B of it geometry. HAC's 27.54 MB and PCGS's 19.09 MB are not budgets this format can be *asked*
   for; reaching them needs fewer Gaussians (M26's pipeline), not a smaller quantiser. Stated this way the
   mid-rate gap stops being a compression failure and becomes a representation fact.
2. **SH degree is the wrong axis.** A degree-2 container lands within 0.06–0.09 % of a degree-3 container's
   bytes and 1.02–2.60 dB below it — dominated at every budget. Any future "save bytes by cutting SH" idea
   is now pre-refuted, in both scenes.
3. **The trade-off is not smooth.** 18.9→21.9× costs 0.46 dB; the next 3.6 % of bytes costs 0.71 dB. Claims
   should be made in the comfortable band and the cliff should be drawn, not averaged away.

Also closed here: M34's frame-size claim on a second scene. bicycle at 1 % burst with 256 KB frames renders
**23.73 dB** against 23.45 dB for 4 MB frames, and the 256 KB container is 0.05 % larger, not smaller. The
4 MB container reads 23.45 dB at *every* burst fraction up to ~5 % because one frame is 4.19 MB and cannot
get smaller — which is why the knob is the frame, not the corruption rate.

## §15. The rate in the loss: a Pareto gain, and what it was made of (M36, round 32)

The last untried lever on the mid-rate gap was the one every entropy-constrained method uses: put the rate
in the training loss. M36 did it on the 25 %-pruned bicycle model (1,532,988 primitives, 12k steps, factor 4)
with a differentiable proxy `R = mean(log2(1 + (θ/σ)²))` over `shN, sh0, scales, opacities`, λ calibrated at
step 0 to a 5 % gradient share and then frozen.

| arm | container | B/prim | PSNR | SSIM | wall |
|---|---|---|---|---|---|
| plain fine-tune (control) | 19,272,155 B | 12.574 | 21.07 | 0.5166 | 731 s |
| **+ log rate term, 5 % share** | **17,959,298 B** | **11.715** | **21.24** | 0.5279 | 812 s |
| + L2 control, same share | 18,381,419 B | 11.990 | 21.19 | 0.5281 | 780 s |
| + log rate term, 15 % share | 17,482,803 B | 11.404 | 21.09 | 0.5200 | 823 s |

Three findings, in decreasing order of usefulness:

1. **The pressure is a Pareto gain, not a trade.** 6.8 % fewer bytes *and* 0.17 dB more PSNR at 1.11× the
   wall clock. A rate penalty that moves the model to a place where the coder needs fewer bits for a
   slightly better picture is not buying bytes with quality; it is removing bits the model was wasting.
2. **The logarithm is not the active ingredient.** The L2 control at the same gradient share lands within
   0.05 dB and 2.4 % of the log arm. What pays is shrinkage of the parameter distribution towards the
   quantiser grid — any smooth penalty with a per-group scale does the same. The entropy-shaped functional
   is not measurably better here, and this is only knowable because the control was pre-registered.
3. **There is a knee below a 15 % gradient share.** d is 2.7 % smaller than b and 0.15 dB worse; its rate
   term ends lowest of the four (0.145), i.e. the coder's favourite shape and the picture's least favourite.

**What it does not do.** The mid-rate point moves 19.27 MB → 17.96 MB at 21.24 dB. HAC is 27.54 MB /
25.05 dB and PCGS 19.09 MB / 25.12 dB: we are 6 % below PCGS's bytes and 3.9 dB below its PSNR. A 0.17 dB
gain cannot close a 3.9 dB gap, and the round says so in its own table. The gap lives in the pruning, not
in the loss: a 25 %-pruned model has discarded information that no penalty can restore, which is why M37
asks the same question on the full model where the headline number lives.

## §16. The rate in the loss is a repair tool, not a compressor (M37, round 33)

The same differentiable pressure that gave a Pareto gain on the 25 %-pruned model was applied to the full
6,131,954-primitive model, where the headline number lives (76.56 MB, 18.90×, 24.06 dB):

| arm | container | PSNR | SSIM | wall |
|---|---|---|---|---|
| plain 12k-step, factor-4 fine-tune | 76,931,227 B | 23.69 | 0.7244 | 1265 s |
| + 5 %-share log rate term | 73,124,530 B | 23.81 | 0.7331 | 1577 s |
| untouched published model | 76,556,000 B | **24.06** | 0.7393 | — |

The pressure works — 4.9 % fewer bytes and +0.12 dB against its own control — and both arms are **worse than
not fine-tuning at all**. Twelve thousand steps at factor 4 on a converged model costs 0.37 dB; the penalty
recovers a third of it and none of the rest. Against M35's measured curve b (73.12 MB / 23.81 dB) is
dominated by interpolation (≈ 23.94 dB at that size).

**Bracketed, the lever is now understood.** Where a schedule destroyed quality there is headroom and the
pressure wins beyond parity (M36: +0.17 dB at 6.8 % fewer bytes). Where the model is converged there is no
headroom, and the pressure only pays back part of the damage the schedule itself did. **It is a repair tool,
not a compressor** — and the cheap knob on this frontier remains re-encoding (0.26 dB for 9.4 % of the bytes
in the M35 sweep) rather than retraining (0.37 dB for 0.4 % here).

The shipping near-lossless point is therefore unchanged: **76.56 MB / 18.90× / 24.06 dB**, untouched model,
no fine-tuning.

## §17. The codebook answer: fewer symbols per primitive is a dead end (M38, round 34)

After M29 showed the geometric codes sit at their first-order entropy, the remaining lever was to spend fewer
symbols: one index into a joint 8-D codebook `(log σxyz, qwxyz, logit α)` instead of four independently coded
groups (44 bits/primitive today).

| k | container | PSNR | SSIM |
|---|---|---|---|
| 4096 (12-bit index) | 54.61 MB | 19.58 | 0.5149 |
| 16384 (14-bit) | 56.34 MB | 19.61 | 0.5270 |
| 65536 (16-bit) | 58.60 MB | 20.36 | 0.5587 |
| scalar baseline `gp6-6-6_c8_sh3` | 76.56 MB | **24.06** | 0.7393 |
| scalar at the same 58.6 MB (M35 curve) | 58.6 MB | **≈ 22.6** | — |

The codebook saves 18–22 MB and costs 3.7 dB against the baseline, and **2.2 dB against the curve at equal
bytes** — it is not below the baseline, it is below the frontier the baseline traces. Sixteen times more
centroids bought 0.78 dB for 4 MB.

**The family is closed.** Scalar codes are at their entropy (M29); joint codes are worse at any affordable
size (M38). The bytes are not in how a primitive is described but in **how many primitives there are** —
which is what the M26 prune-and-fine-tune pipeline exploits, and what HAC/PCGS achieve with anchors and
context models over fewer, better-placed Gaussians. Every remaining idea that keeps 6.13 M primitives and
tries to describe each one more cheaply is now measured to be a dead end.

## §18. The curve now reaches 199.8×, and the lever that got it there is flat (M39, round 22)

The rate-distortion curve of this format, one configuration, one code path, bicycle, 25 held-out views:

| keep | container | ratio | PSNR | Δ vs clean |
|---|---|---|---|---|
| 100 % | 76.56 MB | 18.90× | 24.06 | −0.46 |
| 100 % | 69.34 MB | 20.87× | 23.80 | −0.72 |
| 100 % | 66.24 MB | 21.85× | 23.60 | −0.92 |
| 100 % | 57.23 MB | 25.28× | 22.53 | −1.99 |
| 100 % | 55.18 MB | 26.22× | 21.82 | −2.70 |
| 25 % (M36) | 17.96 MB | 80.6× | 21.24 | −3.28 |
| 15 % (M39) | 10.82 MB | 133.71× | 20.12 | −4.40 |
| 10 % (M39) | 7.24 MB | 199.80× | 19.02 | −5.50 |

The M36/M39 points are the 25 / 15 / 10 % pruning prefixes with the rate pressure in the loss. "The pressure
pays" is true on every row (5.5–6.8 % fewer bytes than the same schedule without it), and yet the pressure is
not what puts these rows on the curve: their position is set by the primitive count, at ~12 B/primitive for
every prefix. The lever that moves a point *along* the curve is the one that changes what a primitive costs.

Read against the published methods: HAC's 27.54 MB and PCGS's 19.09 MB sit at 25.05 and 25.12 dB in our
measurement protocol, i.e. on the quality axis our format reaches only at 76 MB. The gap is not a coding gap
— §14 measured the codes at their first-order entropy, §17 measured a joint codebook doing worse at the same
bytes, §15/§16 measured the rate pressure — it is a representation gap: 44 bits per primitive for geometry
alone versus their ~1 bit per anchor plus a shared decoder.

## §19. The frame boundary is a shipping choice, and it is now a measured one (M40, round 23)

For three scenes, one configuration (`gp6-6-6_c8_sh3`), unchanged between arms except `MIN_FRAME`:

| scene | primitives | 4 MB | 256 KB | Δ bytes | decode | peak RSS | burst 0.1 %: 4 MB → 256 KB | burst 1.0 %: 256 KB |
|---|---|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 76,557,737 B | 76,598,203 B | +0.053 % | 7.84 s | 1.96 GB | 23.45 → **24.00** (control 24.06) | 23.73 |
| stump | 4,961,797 | 62,591,315 B | 62,649,653 B | +0.093 % | 6.38 s | 1.60 GB | 24.67 → **25.33** (control 25.52) | 25.28 |
| bonsai | 1,244,819 | 15,302,360 B | 15,297,685 B | −0.031 % | 1.49 s | 0.47 GB | 23.44 → **26.73** (control 27.08) | 25.68 |

The bound is scene-independent: **256 KB frames cost ≤ 0.35 dB for a 0.1 % burst on every scene**, whereas
4 MB frames cost 0.61–3.64 dB with the loss set by how much of the colour block one frame covers. The default
in `experiments/m19_codec.py` is now 256 KB, with the byte prices in the comment and the boundary recorded in
every file's header. Earlier reported byte counts and ratios are unaffected at the 0.1 % level.

## §20. The encoder: free parallelism, and where the time actually goes (M41, round 24)

| scene | primitives | build | write serial | write jobs=4 | file | end to end |
|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 58.9 s | 11.31 s | 3.21 s | 76,598,203 B (md5 identical) | 153 → 142 s (1.13×) |
| stump | 4,961,797 | 137.7 s | 8.71 s | 2.55 s | 62,649,653 B | 100 → 98 s (1.04×) |
| bonsai | 1,244,819 | 21.2 s | 2.61 s | 0.70 s | 15,297,685 B | 29 → 27 s (1.34×) |

The writer's frames are independent, so the pool is free and byte-neutral (3.4–3.7× on the write). It is also
16 % of the job: stream construction dominates, at 84–94 % of encode time, with peak RSS of 18.8 GB on bicycle —
2.4× the decoder's footprint and 12× the file. The encoder, not the format, is what a deployment has to budget
for; the next round's target is the build, not the compression.

## §21. The encoder is cheaper and still too big — and where its bytes actually are (M42, round 25)

| scene | build (old → new) | peak RSS (old → new) | container |
|---|---|---|---|
| bicycle | 190.1 → 150.1 s | 18.38 → 11.63 GB | 76,598,203 B, md5 identical |
| stump | 127.2 → 103.9 s | 14.94 → 9.51 GB | 62,649,653 B, md5 identical |
| bonsai | 21.4 → 19.9 s | 4.07 → 2.78 GB | 15,297,685 B, md5 identical |

The 18.8 GB was a transient inside `_encode` (four float64 temporaries in the SH quantiser, an `int64` plane array
in the bit-packer); slicing both is arithmetic-neutral and byte-identical. What remains is live data rather than
waste — float64 attribute arrays (4.5 GB, SH rest 2.21 GB), an int64 code array (2.21 GB), three layout
candidates at once — plus a 4.3 GB spike in `load_model`. Cross-host spread on the same code path is 2.5×, so
encode-time claims are only valid as same-node A/B.

## §22. The encoder's peak was a copy of data already in memory (M43 + M44, rounds 26–27)

| scene | legacy | M42 | M43 | M44 | build (legacy → M44) | container |
|---|---|---|---|---|---|---|
| bicycle | 18.38 GB | 11.66 GB | 11.65 GB | **9.60 GB** | 189.6 → 108.9 s (1.74×) | 76,598,203 B, md5 identical |
| stump | 14.94 GB | 9.52 GB | 9.49 GB | **7.83 GB** | 139.7 → 82.6 s | 62,649,653 B, md5 identical |
| bonsai | 4.07 GB | 2.92 GB | 2.70 GB | **2.27 GB** | 21.5 → 19.0 s | 15,297,685 B, md5 identical |

Five rewrites of the encoder's memory behaviour, one file. M43 narrowed the code arrays to `uint8`/`uint16` and freed
the rejected layout candidates: **peak unchanged**, build faster. The stage probe showed why — the peak is a window
inside `_encode`, and the largest thing in that window was `take(block) = block[perm]`, a second full-size float64 copy
of the SH rest block (2.21 GB) made only so the quantiser could read rows in Morton order. M44 gathers the permutation
per slice instead: −2.05 GB, byte-identical.

The remaining 9.60 GB peak sits on a live footprint of 7.2 GB, and 2.21 GB of that is the SH rest block held in float64
because `m22_basis.fit` runs `svd_lowrank` on it — that dtype decides the file. The 6 GB encoder target is therefore not
reachable by memory work: it needs a streaming float64 fit or an explicit decision that byte-identity is worth 3.6 GB.

## §23. The build re-encoded the geometry three times to choose a colour alphabet (M45, round 28)

| scene | old phase (3 full encodes) | new (geometry once + colour ×3) | ratio | build | peak | container |
|---|---|---|---|---|---|---|
| bicycle | 35.1 s | 26.3 s | 0.750 | 78.3 s | 9.18 GB | md5 identical |
| stump | 28.0 s | 21.2 s | 0.755 | 62.8 s | 7.48 GB | md5 identical |
| bonsai | 5.9 s | 4.6 s | 0.782 | 14.3 s | 2.18 GB | md5 identical |

Geometry is 64 % of the container and was being built once per SH layout, though the layout only moves colour bytes.
Building it once is byte-neutral and worth 25 % of the search phase — not the 34 % the byte shares predicted, because
the two halves of `_encode` share a fifth of their time (warm cache on the same permuted arrays). The pre-registered
0.70× target was missed at 0.750×. After the split the three colour passes are independent, so the next lever is a
thread pool over layouts rather than more refactoring.

Encoder history, all with identical containers: 189.6 s / 18.38 GB (pre-M42) → 135.8 s / 11.66 GB (M42) → 126.9 s /
11.65 GB (M43) → 108.9 s / 9.60 GB (M44) → 78.3 s / 9.18 GB (M45, this host).

## §24. Two independent colour passes, one thread pool, and the trade that does not clear (M46, round 29)

| scene | sequential | 2 workers | ratio | 4 workers | peak cost |
|---|---|---|---|---|---|
| bicycle | 26.3 s | 19.2 s | 0.734× | 0.730× | +3.89 GB |
| stump | 21.1 s | 15.6 s | 0.739× | 0.720× | +3.50 GB |
| bonsai | 4.7 s | 3.4 s | 0.723× | 0.702× | +0.86 GB |

Identical streams and md5s, so the pool is correct and byte-neutral. It is GIL-bound (1.67× on two threads; no change
from two to four) and it costs 3.9 GB of peak — more than the extra stream set by an order of magnitude, because both
passes hold their float64 slice temporaries. Shipping stays sequential; the pool is kept for a `fork`-based round that
would have to beat 0.73× at equal peak. Encoder ledger: 189.6 s / 18.38 GB before M42 → 78.3 s / 9.18 GB after M45, with
a bit-identical container at every step.

## §25. The pruning score was the mid-rate bottleneck, and it was a proxy nobody had checked (M47, round 30)

Mid-rate, bicycle, one node, one session, 25 held-out views, identical finetune and container:

| selection | pruned, no training | after 12k finetune | container (equal bytes) |
|---|---|---|---|
| volume `opacity × cbrt(sx·sy·sz)` | 15.18 dB / 0.389 | 21.43 dB | 19.34 MB / **21.08 dB** / 0.517 |
| **saliency from 800 steps of gradients** | **20.11 dB / 0.693** | **24.75 dB** | 19.45 MB / **22.67 dB** / 0.681 |

**+4.93 dB before any training, +1.59 dB at equal bytes.** The two selections share only 27.7 % of the kept set
(Spearman 0.407). The reason the proxy survived five rounds is that it keeps 99.94 % of the *saliency mass* — it is not
the mass it gets wrong, it is which primitives hold it: large faint distant primitives score high and carry no gradient,
small ones on the loss score low and carry most of it.

Gap against PCGS at ~19 MB: **−4.04 dB → −2.45 dB**, entirely post-hoc (one 800-step pass, no architecture change, no
learned entropy model, the same container). Single scene, single seed; the method claim needs the other two scenes.

## §26. The saliency score is a method, and what it buys is trainability (M48, round 31)

The §25 claim was one scene and one seed. Replication on the other two published scenes plus a second bicycle seed,
same protocol, nothing tuned per scene, all numbers from one session on one node:

| scene | volume arm (equal bytes) | saliency arm (equal bytes) | Δ | Δ SSIM |
|---|---|---|---|---|
| bicycle seed 1 | 19.34 MB / 21.08 / 0.517 | 19.45 MB / 22.67 / 0.681 | +1.59 | +0.164 |
| bicycle seed 2 | 19.34 MB / 21.07 / 0.516 | 19.43 MB / 22.58 / 0.680 | +1.51 | +0.164 |
| stump | 15.49 MB / 20.35 / 0.391 | 15.12 MB / 23.52 / 0.675 | **+3.17** | +0.284 |
| bonsai | 3.94 MB / 24.10 / 0.768 | 3.99 MB / 25.74 / 0.858 | +1.64 | +0.090 |

Verdict `saliency_prune_is_a_method`; the second seed lands within 0.08 dB of the first, so M47's number was not a seed
artefact. Mid-rate ratios are 73.6–77.4×, four times the near-lossless shelf.

**The mechanism is not the one that was pre-registered.** T3 asked for ≥ 2.0 dB better *before* finetuning on both new
scenes; bonsai gives +2.33 and stump gives **+0.30**, so the mechanism test fails while the outcome test passes by
3.17 dB. On stump both pruned sets render at the same PSNR (20.59 vs 20.89) but at very different SSIM (0.408 vs 0.726)
— the volume set keeps large faint splats that get the mean colour right and the structure wrong — and across 12k steps
the volume set improves by −0.02 dB while the saliency set improves by +5.00. What the score selects is a set that is
still **trainable**; the pre-finetune render cannot see that, so it is a diagnostic and never again a criterion.

Why stump gains most: the two rankings share only 11.4 % of kept primitives there (ρ 0.179), versus 27.7 % on bicycle
and 31.1 % on bonsai, and the volume set retains 11.2 % of the saliency mass against bicycle's 99.94 %. The ranking by
disagreement is not the ranking by gain, so disagreement predicts volatility rather than payoff.
## §27. What the container actually costs at mid-rate: 0.39 dB, not 1.83 (M49, round 32)

M48's table implied the container ate 1.83 dB on the saliency-pruned model and 0.35 dB on the volume-pruned one, and
that asymmetry was one round away from becoming a method claim. It was a measurement: the "clean" row was a factor-4
training-view eval and the container row was a factor-1 held-out render. M49 rendered the missing control — the
unquantised finetuned model through the container's own probe at factor 1:

| row | file | PSNR | SSIM | Δ vs raw |
|---|---|---|---|---|
| raw finetuned model, factor 1 | 236 B/prim | **23.26** | 0.7334 | — |
| container 96-bit colour | 30.78 MB | 23.04 | 0.7165 | −0.22 |
| container 64-bit | 22.91 MB | 23.01 | 0.7130 | −0.25 |
| **container 48-bit** | **20.56 MB** | **22.87** | 0.6999 | **−0.39** |
| container 40-bit | 19.47 MB | 22.63 | 0.6808 | −0.63 |
| container 32-bit | 18.35 MB | 21.94 | 0.6415 | −1.32 |
| raw finetuned model, factor 4 (the old "cal" protocol) | — | 18.71 | 0.5726 | −4.55 |

Three readings, all of them load-bearing for the paper:

1. **The codec is not the mid-rate bottleneck.** 0.39 dB on the saliency model, 0.35 dB on the volume model — the same
   cost twice. Whatever separates us from PCGS at 19 MB is not quantisation.
2. **Two thirds of a mid-rate container is geometry.** The measured stream attribution is positions 3.38,
   quaternions 2.95, scales 2.04, opacity 0.70, headers 0.09 = 9.16 B/primitive of geometry against 4.34 B of
   colour (corrected 2026-11-17 13:20; the earlier "85 % / 11.4 B" was a bad extrapolation). The colour curve
   confirms the split from the other side: 48 → 96 bits buys +0.17 dB for +10.22 MB.
3. **The mid-rate point is a model point.** Raw 23.26 dB at 1.53 M primitives against PCGS's 25.12 at 19.09 MB: the
   deficit exists before compression. Either the same bytes must carry more primitives, or 1.53 M primitives must be
   made better. M50 prices the geometry block to see which of those is reachable.

## §28. The geometry block is at its rate — except opacity, which is free (M50, round 33)

M49 left one number to explain: geometry is about two thirds of a mid-rate container. M50 priced every field of it on the same
finetuned model (bicycle, 1.53 M primitives, 48-bit colour, 25 held-out views, encode-only so only the geometry code
moves):

| change | Δ bytes | Δ dB | dB per 1 % saved |
|---|---|---|---|
| opacity 6 → 4 bits | −2.37 % | **+0.01** | **0.00** |
| positions 8 → 7 bits | −2.78 % | −0.11 | 0.040 |
| positions 8 → 6 bits | −5.60 % | −0.44 | 0.079 |
| quaternions 6 → 4 bits | −6.48 % | −0.29 | 0.045 |
| scales 6 → 4 bits | −7.54 % | −0.91 | 0.121 |
| quat+scales+opacity 4 | −16.40 % | −1.22 | 0.074 |
| + 6-bit positions | −22.00 % | −1.51 | 0.069 |

The exchange rate against M17/M18's primitive trade (25 % → 35 % keep: +32.7 % bytes for +0.43 dB = 0.013 dB per 1 %)
is decisive: **every geometry knob costs more per byte than a primitive does**, so neither coarsening geometry to buy
primitives nor spending geometry bytes on precision pays. The mid-rate deficit against PCGS needs a cheaper geometry
*representation* (anchors/offsets, VQ), not a quantiser setting — which is exactly where M27/M28 stopped.

The exception is worth shipping: **opacity at 4 bits is free** — 2.37 % of the file for +0.01 dB and −0.004 SSIM. On
the near-lossless shelf that would take 76.56 MB to ≈74.7 MB, 18.90× to ≈19.37×, if it replicates on the unpruned
model at 165-bit colour — which is M51's whole job, on three scenes, with the file measured rather than extrapolated.

## §29. The free byte was a property of the pruned model (M51, round 34)

M50's most quotable row — opacity at 4 bits instead of 6, −2.37 % of the file for +0.01 dB — does not survive the move
to the untouched published models. Three scenes, shipping spec `gp6-6-{6,4}_c8_sh3`, 48-bit colour, same probe:

| scene | control | 4-bit opacity | Δ bytes | Δ dB | Δ SSIM |
|---|---|---|---|---|---|
| bicycle | 76,598,203 B / 24.06 | 74,802,867 B / 23.95 | −2.35 % | −0.11 | −0.0063 |
| stump | 62,649,653 B / 25.52 | 61,191,922 B / 25.41 | −2.33 % | −0.11 | −0.0064 |
| bonsai | 15,297,685 B / 27.08 | 14,927,795 B / 26.97 | −2.42 % | −0.11 | −0.0044 |

The identical 0.11 dB on 6.1 M, 5.0 M and 1.2 M primitives is the tell: on the pruned model pruning had already
collapsed the opacity distribution, so the 6-bit quantiser was spending bits on a near-constant field. The unpruned
models keep the distribution and the top bits matter.

The byte is still the cheapest one available at the near-lossless end — 0.047 dB per 1 % against 0.134 for 48 → 40-bit
colour and 0.175 for 48 → 32-bit (M22's rows) — so the right way to write it is a rate knob, not a free win:
18.90× at −0.46 dB, or 19.35× at −0.57 dB. The shipping row stays at 6 bits. The lesson is the one M49 taught in a
different guise: **a container result measured on a pruned model does not transfer to the published one**, and each
transfer costs one round to verify.

Two environment defects were also caught here and are worth recording because they fail *silently*: the MatPool
PyTorch image ships **no gsplat** (the renderer needs `gsplat.rasterization`, 1.5+; without it the probe prints its
header and dies, and every row reads "NA"), and it has **no `/usr/bin/time`** (decode timing must use
`resource.getrusage`). Both are now pinned in the round's scripts.

## §30. The mid-rate wall is a price, not a limit (M52, round 35)

The allocation question ("at 19 MB, should we keep more primitives at coarser geometry?") is answerable from two
measured exchange rates, and the answer is no in every direction:

| direction | rate |
|---|---|
| buying a primitive (M18: 1.53 M → 2.15 M, +40 %, +0.57 dB) | **0.075 dB per byte** |
| selling a geometry byte (M50/M51: positions 0.30, quaternions 0.33, opacity 0.38, scales 0.90) | **0.30–0.90 dB per byte** |

Chain them through the coarsest knob we have (`gp6-6-6_c8 → gp4-4-4_c6`, −2.95 B/primitive, −1.51 dB): the freed bytes
buy +28.2 % primitives = +0.40 dB, so the trade nets **−1.11 dB**. Reaching the 2.8 M primitives that 19.5 MB would
need at PCGS-like density requires geometry at 4.0 B/primitive, which at the measured price costs 1.5–4.6 dB against
the +0.9 dB it buys.

The conclusion is not "SOTA is a physical limit" — PCGS's 19.09 MB / 25.12 dB is an existence proof in the same
operating region. It is that **our geometry code is cheap to decode and expensive per byte**, and only a representation
whose reconstruction is trained through (anchor + VQ) can make the same bytes cheaper. Post-hoc pruning cannot, which is
why eight rounds of pruning/thinning/quantiser work moved the mid-rate by 1.6 dB and no more.

The falsifiable target for that round, written before it exists: **geometry at 4.0 B/primitive with ≤ 0.6 dB loss**
(0.15 dB/B), netting +0.3 dB at equal bytes. Below that rate the arithmetic wins; above it, no allocation does.

## §31. The target was too generous: the attributes alone exceed it (M52 correction, round 35–36)

§30 set "geometry 4.0 B/primitive" as the bar for an anchor round. Adding the measured per-field costs up shows the bar
was wrong: at `gp6-6-6_c8` the **attributes alone** cost 5.88 B/primitive (quaternions 2.95 + scales 2.04 + opacity
0.70 + headers 0.19) and positions another 3.38. Field-wise coarsening to the edge of usability gives 3.71 B for the
attributes, and anchored positions would add ~1.0 B — a floor of **4.71 B/primitive**, still above the 4.0 bar.

At that floor the trade is: −4.45 B/primitive at fixed bytes = ×1.50 primitives = +0.70 dB, against ≥1.31 dB of
coarsening plus an unmeasured anchor error. **Net −0.6 to −1.1 dB.** So the mid-rate cannot be bought back by any
combination of coarsening and position anchors; the attributes have to be *predicted* from the anchors, which is a
training problem, not a codec one — and it is precisely the piece M28 identified and never trained.

**The revised, falsifiable bar:** geometry ≤ **2.8 B/primitive** with ≤ **0.4 dB** loss at equal bytes (which means
anchored positions ~1.0 B and anchor-conditioned prediction of quaternion/scale/opacity residuals to ~1.8 B combined).
A prototype that cannot get the attributes below 3 B/primitive is arithmetic that loses, and the anchor programme should
not be run. This is the number M53 is written against.

## §32. Two scenes, not three: the bonsai exclusion is now enforced (M55, round 38)

`bicycle` 24.52 vs published 25.11 and `stump` 26.15 vs 26.66 both sit inside the 0.55 dB protocol bias M16 measured.
`bonsai` renders at 28.06 against a published 32.12 — 4.1 dB — and M16 excluded it from cross-paper claims. That
exclusion was prose, and prose drifts: a summary table in round 36 compared our bonsai row (25.74 dB at 4.0 MB) with
PCGS (33.20 dB at 7.4 MB) as though the two shared a protocol.

The registry (`experiments/protocol_assets.py`) and the linter (`tools/lint_protocol_claims.py`, wired into the suite)
now make it mechanical. The consequence for the paper is a count, not a caveat: **the cross-paper evidence is two
scenes.** Bonsai remains in every within-pipeline comparison — saliency vs volume (+1.64 dB), opacity width, damage
locality, decode memory — but never against HAC/PCGS/3DGS until the 4.1 dB is explained.

The unexplained gap is itself a defect worth recording: same primitive count, same renderer that reproduces the other two
scenes to 0.6 dB, so the suspicion is the GT/COLMAP pairing rather than the checkpoint. One control training plus a
standard-split render would settle it.

## §33. The gap, computed the way a compression paper computes it (M57, round 40)

Three numbers have been quoted for "how far behind": 2.5 dB, "4x", "70x". `tools/gap_report.py` replaces all three with
one table computed from measured points only (whole curve in `experiments/GAP_REPORT.md`):

| scene | method | their MB | their PSNR | our PSNR @their MB | gap | bias-corrected |
|---|---|---|---|---|---|---|
| bicycle | HAC | 27.54 | 25.05 | 23.03 | **+2.02** | +1.47 |
| bicycle | PCGS | 19.09 | 25.12 | 22.40 | **+2.72** | +2.17 |
| stump | HAC | 18.11 | 26.58 | 24.30 | **+2.28** | +1.73 |
| stump | PCGS | 13.49 | 26.61 | no row | — | — |
| bicycle | 3DGS | 1336.45 | 25.11 | no row | — | — |

Two rules make it honest. Interpolation happens only **between** measured rows, so a published size outside our range
reads `no row` instead of being extrapolated. And the rate at matched quality is **`unreachable`** on both scenes,
because our curve — including the uncompressed published model (bicycle 1447.1 MB / 24.52 dB; stump 1170.98 MB /
26.15 dB) — never reaches the published PSNR. Correcting the 0.55 dB protocol bias does not create a row; it only moves
the statement to "our uncompressed model is the published quality at 76x the bytes".

**What the paper must print.** At matched bytes: **+2.0 to +2.7 dB raw, +1.5 to +2.2 dB bias-corrected**, on two scenes
(bonsai excluded, §32). At matched quality: no row. The second sentence is the one that decides the framing — a
compression paper that cannot reach the published PSNR at any size is not a competitor on the rate-distortion axis, and
saying so is cheaper than having a referee say it.
