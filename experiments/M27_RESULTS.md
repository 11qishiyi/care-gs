# M27 — the anchor representation: 3.8× cheaper per primitive, 5 dB worse per megabyte

Preregistration: `tools/m27_spec.md` (written 03:20, before any anchor number existed). Machine:
node 2140647, A100-PCIE-40GB, ¥2.80/h, rented 03:31, released 05:05 (≈1.55 h ≈ ¥4.3). Asset: the
published bicycle model, 6,131,954 primitives, 25 evaluation views at 1236×822, clean 24.52 dB,
fp32 1447 MB.

## Verdict: `sharing_costs_too_much` — and more precisely, *constant* sharing does

Appendix entry: **N34** (`APPENDIX_negative_results.md`).

| criterion | measurement | verdict |
|---|---|---|
| **A1** ≤ 30 MB and ≥ 23.0 dB | best ≤ 30 MB is **16.97 dB** (24.07 MB); best anywhere is 21.58 dB at 69.19 MB | **FAIL** |
| **A2** within 1 dB of HAC (25.05 dB) at 27.54 MB | at 27.5 MB the anchor file is ≈16.5 dB, i.e. **−8.5 dB** | **FAIL** |
| **A3** one file, our container, decode ≤ 60 s, RSS ≤ 8 GB | **3.40 s**, **3.10 GB**, single `.gs1` | PASS |
| **A4** attribution over ppa × offset depth | table below | reported |

The representation is cheap — astonishingly so. The full published model fits in 15.4 MB at 2.52 B
per primitive, **3.8× cheaper than the shelf's 13.60 B** on the same model. It just does not look
like the model.

## Everything measured (bicycle, 6,131,954 primitives, no fine-tuning of any kind)

| variant | ppa | offset bits | kept per primitive | file | B/prim | PSNR | SSIM |
|---|---|---|---|---|---|---|---|
| a16_o3 | 16 | 3 | — | 15.42 MB | 2.52 | 13.86 | 0.166 |
| a8_o3 | 8 | 3 | — | 21.75 MB | 3.55 | 16.05 | 0.250 |
| a8_o4 | 8 | 4 | — | 24.07 MB | 3.93 | 16.97 | 0.332 |
| a4_o3 | 4 | 3 | — | 33.25 MB | 5.42 | 17.92 | 0.375 |
| v_all | 8 | 3 | — | 29.62 MB | 4.83 | 16.26 | 0.268 |
| v_opac | 8 | 3 | opacity | 34.45 MB | 5.62 | 16.55 | 0.273 |
| v_quat | 8 | 3 | rotation | 46.13 MB | 7.52 | 16.35 | 0.274 |
| v_opacquat | 8 | 3 | opacity, rotation | 50.96 MB | 8.31 | 16.65 | 0.279 |
| v_opacquat_scale | 8 | 3 | opacity, rotation, scale | 64.58 MB | 10.53 | 19.11 | 0.359 |
| all_o5 | 8 | 5 | — | 34.23 MB | 5.58 | 17.77 | 0.428 |
| all_o6 | 8 | 6 | — | 36.53 MB | 5.96 | 17.97 | 0.456 |
| ppq_o5 | 8 | 5 | opacity, rotation, scale | 69.19 MB | 11.28 | **21.58** | 0.605 |

Reference rows on the *same asset*: our shelf file at 13.60 B/prim is 83.41 MB / **24.08 dB** (M24);
our prune-plus-finetune mid-rate point is 24.96 MB / **21.24 dB** (M26 arm A); HAC is 27.54 MB /
25.05 dB; PCGS is 19.09 MB / 25.12 dB.

## What the numbers say, term by term

**Position quantum is the first-order term, and it is a choice, not a property.** At ppa 8 the voxel
edge is 10.67 cm, so a 3-bit offset grid quantises positions to 1.33 cm — an order of magnitude
coarser than the shelf's 0.19 mm. Going 3 → 4 bits is +0.92 dB (16.05 → 16.97) for 2.3 MB; 3 → 5 bits
is +1.72 dB (16.26 → 17.77 in the 6-bit-DC arm). Half of the early loss was simply a grid that was too
coarse, which is the sort of thing the preregistration's A4 was written to expose.

**Sharing a constant costs the attributes that carry the image.** Holding the position grid fixed
(3-bit offsets, 6-bit DC, 29.62 MB = 16.26 dB):

* opacity per primitive: **+0.29 dB** for 4.8 MB;
* rotation per primitive: **+0.09 dB** for 16.5 MB;
* scale per primitive: **+2.46 dB** for 13.6 MB (16.65 → 19.11).

Scale is the one that cannot be shared, and the reason is visible in the per-attribute audit
(`tools/m27_diff.py`): inside one 10.7 cm voxel the member scales span a factor of ~two and the
opacities span 0.02 to 0.79. A single number cannot describe both a wisp of fog and an opaque leaf
that happen to live in the same voxel. Rotations disagree by ~23° on average (mean |dot| 0.92 **even
after** the double-cover fix, which is the sharing cost, not a bug); opacity error is 0.25 absolute.

**Sharing the rest colour costs ≈2 dB at equal bytes.** The ppq_o5 arm shares nothing but the rest
colour: 69.19 MB / 21.58 dB, while the shelf at 69 MB would sit near 23.7 dB by interpolation. View
dependent colour is smooth enough to share at 10 cm — the measured cost is real but an order of
magnitude smaller than the geometry attributes.

**The decisive comparison is against pruning, not against the shelf.** At 24.96 MB our pruned and
fine-tuned model renders 21.24 dB (M26). The anchor path at 24.07 MB renders 16.97 dB. The anchor
representation is *5× cheaper per primitive* and *4.3 dB worse at equal bytes*. Pruning keeps every
attribute exact and throws away primitives; anchors keep every primitive and blur its attributes.
On this evidence the image prefers exact attributes.

## Why this had to be measured rather than argued

The budget identity from N25–N27 said the 20–30 MB row was unwinnable because a per-primitive
attribute record costs ~16 B and 27.5 MB cannot hold 6.13 M of them. That identity is correct — this
round built the representation it implies and reached **2.52 B per primitive**. The identity was not
the only binding constraint: *sharing an attribute is not free in distortion*, and the exchange rate
turned out to be terrible for exactly the attributes the earlier rounds never had to touch, because
the shelf always stored them at full precision.

Stated as a law for the record: **bytes per primitive is not a rate; it is one factor of a rate that
also contains the reconstruction the representation is allowed to make.** An anchor that stores a
constant has a reconstruction of one constant per voxel; an anchor that *predicts* has a decoder.

## What this changes for the next round

The only missing ingredient between 21.58 dB at 69 MB and HAC's 25.05 dB at 27.5 MB is the decoder:
HAC stores a per-anchor feature and runs an MLP over (feature, offset) to produce per-primitive
attributes. Every measurement above is consistent with that design being the right one — the anchor
side is cheap and works, the constant side is what fails — and none of it can be obtained by tuning
quantisers. M28 therefore has one candidate, and it is a training round, not a coding round.

## Reproduction

```bash
bash experiments/run_m27.sh setup                     # published bicycle + colmap + base archive
bash experiments/m27_ablate.sh                        # the sharing ablation at ppa 8
bash experiments/m27_offsets.sh                       # offset depth 5/6 bits
bash experiments/m27_render_v.sh                      # render every container the two scripts wrote
python3 tools/m27_diff.py <point_cloud.ply> <file.gs1>   # per-attribute error audit
python3 tools/m27_stats.py <point_cloud.ply> <file.gs1>  # source vs decoded distributions
```

## Cost

Node 2140647: 03:31 rent → 05:05 release, 1.55 h at ¥2.80/h ≈ **¥4.3**, including the 18-minute setup
(published model, COLMAP, base archive) and twelve encodes plus fifteen renders.

## Defects found and fixed while building it

* `voxel_size_for` trusted a density estimate and returned a voxel ten times too coarse: a `ppa = 8`
  sweep silently became `ppa = 85`, every container 2.5× too small, no error anywhere. Fixed by
  *verifying* the bracket by expansion before bisecting; the ppa is now printed in every log.
* `np.unique(..., axis=0)` on 6.1 M row-triples cost minutes per call; a linear 1-D key with
  `np.unique` on int64 brings each grouping step to seconds.
* Quaternion double cover: a plain mean of `q` and `-q` lands near zero, and renormalising that
  yields a random rotation (worst |dot| 0.00005). Members are now sign-aligned against the mean before
  averaging.
* Opacity was averaged in logit space, which is an average of odds: one opaque member drags a voxel's
  median from 0.12 to 0.21. Now averaged in linear space and re-logit-ed.
* A 3-bit DC code against a per-voxel level collapsed small colour coefficients to zero (decoded DC
  median −0.34 → 0.00); 6 bits plus the level fix brings the relative error from 31 % to 9 %.
* `write_container` silently dropped the twelve new `a_*` streams and then the six `p_*` ones — the
  same defect N32 documents, in the same file, two rounds later. It now **raises** on any stream
  outside `ORDER`; both occurrences were caught by that guard within one run each.
