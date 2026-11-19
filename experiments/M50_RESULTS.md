# M50 — the geometry block is at its rate, except opacity, which is 2.4 % of the file for free

**Round 33, node 2141648 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 11:26–11:42 ≈ ¥0.75**, continuing the same session as
M49 (the finetuned model was already on the node). M49 showed geometry is about two thirds of a mid-rate container (measured attribution; the first write-up said 85 %, corrected 13:20 on 11-17); this round
prices each geometry field on that same model. Encode-only: every row differs from the control only in the geometry
code. Pre-registered in `METHOD_PLAN.md` ("M50 spec", 11:35) before any row existed.

## Result (bicycle, 1,532,988 primitives, 48-bit colour, 25 held-out views, factor 1)

| spec | what changed | file | MB | PSNR | SSIM | Δ dB | Δ bytes | dB per 1 % saved |
|---|---|---|---|---|---|---|---|---|
| `gp6-6-6_c8` | control (shipping) | 20,561,912 | 20.56 | **22.87** | 0.6999 | — | — | — |
| `gp6-6-4_c8` | opacity 6 → 4 bits | 20,073,993 | 20.07 | **22.88** | 0.6955 | **+0.01** | **−2.37 %** | **0.00** |
| `gp6-6-6_c7` | positions 8 → 7 bits | 19,990,939 | 19.99 | 22.76 | 0.6884 | −0.11 | −2.78 % | 0.040 |
| `gp6-6-6_c6` | positions 8 → 6 bits | 19,410,087 | 19.41 | 22.43 | 0.6563 | −0.44 | −5.60 % | 0.079 |
| `gp4-6-6_c8` | quaternions 6 → 4 bits | 19,228,871 | 19.23 | 22.58 | 0.6839 | −0.29 | −6.48 % | 0.045 |
| `gp6-4-6_c8` | scales 6 → 4 bits | 19,011,806 | 19.01 | 21.96 | 0.6675 | −0.91 | −7.54 % | 0.121 |
| `gp4-4-4_c8` | quat + scales + opacity all 4 | 17,190,847 | 17.19 | 21.65 | 0.6440 | −1.22 | −16.40 % | 0.074 |
| `gp4-4-4_c6` | all of the above + 6-bit positions | 16,039,022 | 16.04 | 21.36 | 0.6079 | −1.51 | −22.00 % | 0.069 |

## Verdict — `shipping_spec_is_at_its_rate`, with one free byte

* **H1 FAILS.** No field saves ≥ 8 % of the file for ≤ 0.25 dB. The best real knob is 7-bit positions: −2.78 % for
  −0.11 dB. Everything that saves 6 % or more costs 0.3 dB or more.
* **H2.** The primitive exchange rate measured in M17/M18 (25 % → 35 % keep: +32.7 % bytes for +0.43 dB) is
  0.013 dB per 1 % of bytes. Every geometry knob costs *more* than that per byte saved (0.040–0.121 dB per 1 %), so
  reallocating bytes between geometry precision and primitive count does not pay in either direction: **our geometry
  bits are already well spent, and the mid-rate deficit versus PCGS cannot be reached by moving this slider.** It
  needs a cheaper *representation* of geometry (anchor/offset or VQ), which is what M27/M28 started and M50 now
  bounds from the other side.
* **The exception is opacity: 4 bits instead of 6 is free** — −2.37 % of the file for **+0.01 dB** and −0.004 SSIM.
  At six bits the field carries almost no information the renderer uses; the quantiser's own alphabets had already
  been choosing coarse steps for it. This is the first shippable container change since M34's frame layout.

## What the free 2.4 % is worth

| configuration | before | with 4-bit opacity | ratio |
|---|---|---|---|
| near-lossless shelf (bicycle, `gp6-6-6_c8_sh3` r16/48) | 76.56 MB / 24.06 dB / 18.90× | 74.80 MB / 23.95 dB / 19.35× (**M51: not free — −0.11 dB**) | +0.45× |
| mid-rate equal-bytes point (M49) | 19.47 MB / 22.63 dB | ≈ **19.01 MB** / 22.63 dB | — |

**Correction (M51, 2026-11-17 12:55): the near-lossless row was measured with this change and it is *not* free — 0.11 dB on all three scenes. See `M51_RESULTS.md`.** The near-lossless row is the paper's headline ratio, so a byte-free 2.4 % there is worth more than the mid-rate
version of the same change. **M51 must re-measure it, not extrapolate it**: the shelf row is a different model (no
pruning, 165-bit colour) and this round measured a 25 %-pruned one at 48 bits.

## Caveats, stated rather than smoothed

* One scene, one seed, one model — as the spec required.
* The 4-bit opacity row is a *single* container; the −2.37 % is the measured `*.gs1` length difference, not a byte
  model estimate.
* `gp6-6-4` was not re-checked against the volume-pruned arm or at the near-lossless colour budget; that is M51.

## Reproduction

```bash
# on the node, with M49's model at /workspace/res/m49/arm_g/point_cloud.ply
bash tools/m50_drive.sh      # eight specs: encode -> archive -> render at factor 1, idempotent
```

Files: `tools/m50_drive.sh`, `experiments/artifacts/a4/m50/` (rows, stage log, eight render logs),
`experiments/artifacts/a4/m50_bundle.tgz`, `experiments/M50_RESULTS.md`, `METHOD_PLAN.md` (spec + result),
`FRONTIER_BOUND.md` §28.

## Cost

Same node as M49: the encode sweep itself 11:26–11:42 ≈ **16 min ≈ ¥0.75** (eight encodes ≈ 90 s each, eight renders
≈ 11 s each); the node was released immediately after the last row.
