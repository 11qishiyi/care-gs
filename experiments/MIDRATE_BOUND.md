# The mid-rate bound of the current representation (M52 analysis round, 2026-11-17)

**Round 35. No node was used: the A40 attempt in 1区 was aborted after the COLMAP fetch ran at 180 kB/s and the model
download projected to 2.3 h (see §5), and every 16区 A100 pool was sold out. This round instead closes the question the
node was rented to answer, from measurements already in the repository.**

The question: at 19 MB, is our pipeline sitting at the right (primitive count, geometry precision, colour budget)
point, or is there an allocation that buys decibels without new code? The answer, from measured components, is that
**the trade loses in every direction available to us**, and the loss is quantifiable.

## 1. Where the bytes are (measured, `artifacts/a4/m24_encode_streams.txt`)

`gp8-6-6_c9_sh3`, 6,131,954 primitives, 83.41 MB = 13.60 B/primitive:

| stream | MB | B/prim | group |
|---|---|---|---|
| cluster_off (positions) | 20.70 | 3.38 | geometry |
| geo_quat_abc | 18.11 | 2.95 | geometry |
| geo_scales | 12.50 | 2.04 | geometry |
| geo_opacities | 4.31 | 0.70 | geometry |
| geo_quat_which + cluster_hdr | 1.16 | 0.19 | geometry |
| sh_coef | 18.58 | 3.03 | colour |
| sh_scale | 4.36 | 0.71 | colour |
| sh_dc | 3.69 | 0.60 | colour |

Geometry **9.16 B/primitive (67 %)**, colour **4.34 B (32 %)**. The shipping near-lossless row `gp6-6-6_c8_sh3` is the
same split within a point (12.49 B total).

## 2. The exchange rate that decides everything

Two measured facts, both on bicycle, both at 25 % keep:

* **Buying primitives.** 1.53 M → 2.15 M (+40 %) buys **+0.57 dB** coded (M18, 30 k finetune both sides).
* **Selling geometry bits.** `gp6-6-6_c8` → `gp4-4-4_c6` saves **2.03 B/primitive** and costs **1.51 dB** (M50:
  20.56 MB / 22.87 dB → 16.04 MB / 21.36 dB).

Chain them. `gp4-4-4_c6` saves 2.95 B/primitive (13.41 → 10.46 at 1.53 M), which at a fixed file size grows the
primitive count by 13.41 / 10.46 = **+28.2 %**, worth **+0.40 dB** at M18's rate. Net: **−1.11 dB**. The same
arithmetic per field, from M50/M51's rows:

| knob | B/prim saved | dB cost | dB per B |
|---|---|---|---|
| positions 8 → 7 | 0.37 | 0.11 | 0.30 |
| quaternions 6 → 4 | 0.87 | 0.29 | 0.33 |
| opacity 6 → 4 | 0.29 | 0.11 (M51) | 0.38 |
| scales 6 → 4 | 1.01 | 0.91 | 0.90 |
| all four together | 2.95 | 1.51 | 0.51 |

Buying a primitive costs 12.49 B and pays 0.57 dB per 0.61 M of them, i.e. **0.075 dB per byte**. Selling geometry costs
**0.30–0.90 dB per byte**. The wall is a factor of **4–12**, not a few percent: within this representation the geometry
bytes are worth more where they are than any primitive they could buy.

## 3. What that implies for the 2.5 dB

Take the best measured mid-rate row (19.47 MB / 22.63 dB) and ask what a *perfect* re-allocation could reach: nothing,
by §2. Ask instead what a different representation would have to deliver. To carry 2.8 M primitives in 19.5 MB the
container needs 6.9 B/primitive. With the colour block held at 32 bits (2.9 B), geometry must come down to **4.0 B** —
a 2.3× reduction on today's 9.16 B. At the measured price of 0.30–0.90 dB/B, that reduction costs 1.5–4.6 dB on its
own, while the extra 1.27 M primitives buy +0.9 dB. **A byte-shaving representation makes it worse unless the same
bytes become cheaper in distortion terms** — i.e. unless the coding is trained through, which is exactly what
anchor/VQ methods do and what post-hoc pruning cannot.

That is the honest statement of the mid-rate situation: not a physical limit (PCGS demonstrates 19 MB → 25.12 dB), and
not an allocation error, but a **reconstruction-cost wall**: our geometry code is cheap to decode and expensive per
byte, and every byte we remove costs 4–11× more distortion than the primitive it would buy.

## 4. Correction (2026-11-17 14:10, same day): the 4.0 B/primitive target in §3 was set before the per-field floors were added up

`quaternions 2.95 + scales 2.04 + opacity 0.70 + headers 0.19 = 5.88 B/primitive` — the *attributes alone* already exceed a
4.0 B geometry budget, so "anchor the positions and reach 4.0 B" is not reachable by field-wise coarsening. The floor
that field-wise coarsening actually gives:

| plan | geometry B/prim | quality cost |
|---|---|---|
| today (`gp6-6-6_c8`) | 9.16 | — |
| quat 4 + scales 4 + opacity 4 | 3.71 | ≈ 1.31 dB (0.29 + 0.91 + 0.11) |
| + anchored positions at ~1.0 B | **4.71** | + the anchor error, unmeasured |

4.71 B/primitive saves 4.45 B, which at fixed bytes buys ×1.50 primitives (+49.7 %) = **+0.70 dB**, against ≥1.31 dB of
coarsening plus the anchor error. **Net −0.6 to −1.1 dB.** So neither anchored positions nor field-wise coarsening wins;
the attributes have to be *predicted*, not merely coarsened.

## 4b. What would have to be true for the anchor round to win

Revised, falsifiable target: **geometry at ≤ 2.8 B/primitive with ≤ 0.4 dB loss** at equal bytes. Reaching it means
anchored positions (~1.0 B) *plus* anchor-conditioned prediction of quaternions, scales and opacity down to ~1.8 B
combined — i.e. prediction has to remove about 2 B of the 3.71 B that coarsening alone leaves. If a prototype cannot get
the attributes below 3 B/primitive, the arithmetic loses and the anchor programme should not be run.

## 5. Operational finding (why this round has no node numbers)

The 1区 A40 pool is unusable for this pipeline: `download.pytorch.org` throttles to ~110 kB/s (the 528 MB VGG backbone
needs 80 min) and the HF model pull ran at ~180 kB/s (the 1.52 GB bicycle PLY projects to 2.3 h), while 16区 pulls the
same file in ~3 min and has `/mnt/m35cache` with the three PLYs. The A40 attempt cost 44 min ≈ ¥2.1 (13:01–13:45) and was released.

Two fixes are now in the scripts and must stay:

* `tools/m52_go.sh` caches COLMAP to `/mnt/colmap3.tgz` and the model PLY to `/mnt`, so the 20–30 min staging cost is
  paid once per region rather than once per round;
* `experiments/probe_render_psnr.sh` renders without `--fidelity`, because SSIM/LPIPS need the 528 MB VGG download and
  neither criterion in this programme has ever been an SSIM criterion. Rounds that need SSIM must say so up front and
  budget the download.

Rule for subsequent rounds: **rent 16区 A100 only.** If it is sold out, do an analysis round rather than a slow one.
