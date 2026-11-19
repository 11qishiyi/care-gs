# M21 — a file worth truncating

*Round 17, 2026-11-15. Node 2140398 (A100-PCIE-40GB, ¥2.80/h, 17:01–19:20). Pre-registration:
METHOD_PLAN.md, "M21 spec", written 17:05 before any data.*

## What was asked

M20 closed the rate axis inside this representation: the near-lossless shelf sits at 10.01× on
bicycle and its SH block is at its empirical floor. The one axis left that no published method
competes on is *delivery*: a single file that can be cut anywhere and still decode. The
pre-registered question was whether a truncated `.gs1` is a usable model, what that costs in bytes,
and whether the cost is worth paying.

## Two artefacts, and what each one is for

| file | layout | bicycle size | purpose |
|---|---|---|---|
| best-rate | SH codes as one zstd stream, byte per code | 144.55 MB | smallest file this family produces |
| rate-scalable | same codes split into three bit-planes, coarse first, plus a 1.3 kB reconstruction LUT | 178.18 MB | a byte prefix is a complete model at lower colour precision |

The scalable file costs **+23.3 %** (bicycle) / **+23.5 %** (stump). Pre-registered bound was 12 %
(P2), so **P2 fails** — and the reason is structural, not an implementation detail: the joint
entropy of an 8-level SH code is 1.92 bit, while its three bit marginals sum to 2.90 bit. Splitting
the symbol into bits throws away exactly the correlation that made M20's byte alphabet win. There is
no layout that is both separable and as cheap as the joint symbol.

## The measured ladder (bicycle, 25 held-out views, 1236×822)

| step | bytes | % of payload | PSNR | SSIM |
|---|---|---|---|---|
| geometry + DC only | 79.95 MB | 44.9 % | **22.84** | 0.7034 |
| + 1 plane | 104.87 MB | 58.9 % | 18.98 | 0.7149 |
| + 2 planes | 138.65 MB | 77.8 % | 22.63 | 0.7386 |
| full | 178.18 MB | 100 % | 24.33 | 0.7596 |

**The ladder is not monotone: one plane is 3.86 dB worse than no colour at all.** A single bit per
coefficient forces every SH coefficient to one of two levels, and the reconstruction that minimises
the error of *that* estimate is still a much larger excursion than the true value, so the model gains
high-frequency colour noise it never had. Bicycle is where it shows; stump is monotone but flat:

| stump | bytes | % of payload | PSNR |
|---|---|---|---|
| DC only | 65.43 MB | 44.6 % | 24.44 |
| 1 plane | 87.00 MB | 59.2 % | 25.08 |
| 2 planes | 115.35 MB | 78.5 % | 25.66 |
| full | 146.86 MB | 100 % | 25.81 |

The last 21 % of the stump file buys 0.15 dB — the colour block is already saturated at two planes.
**P1 fails on bicycle** (non-monotone) and passes on stump. Verdict: `progressive_not_worth_it` for
the bit-plane design.

## What is worth shipping: the free boundary

The best-rate file is already ordered geometry → colour, so cutting it just before the SH rest block
leaves every primitive with position, opacity, scale, rotation and DC colour — a degree-0 model — at
*zero* extra bytes. Measured:

| scene | full file | cut before colour | Δ | Δ bytes |
|---|---|---|---|---|
| bicycle c10_o8_sh3 | 144.55 MB / 24.33 dB | 79.95 MB (55.3 %) / **22.84 dB** | −1.49 dB | −44.7 % |
| stump c10_o8_sh3 | 118.88 MB / 25.81 dB | 65.43 MB (55.0 %) / **24.44 dB** | −1.37 dB | −45.0 % |

That is the same 22.84 dB the scalable ladder reaches at its DC step — for 23 % fewer bytes. A
two-step ladder (colour / no colour) is therefore free, and a finer ladder costs a quarter of the
file. **P3 passes**: the DC prefix decodes in 6.10 s against 13.59 s for the full file (0.45×), both
in one process, so decode cost tracks the bytes actually present.

## The bug this round found, and why it mattered

The first measurement of the free boundary returned **9.93 dB** — a nearly black model. Cause: a lost
frame is filled with zero bytes, and a zero *code* is not "no colour". The SH ladder codes are
signed with an offset (`qmax + 1` is zero), so a run of zeros is the darkest level of every
coefficient: 64 lost frames of `sh_rest` became a black tint over the whole scene.

Fix, now part of the format: the encoder records each frame's raw size, the reader records which raw
byte ranges were lost, and the decoder patches those ranges with the neutral code (`qmax + 1`) for SH
streams only. Positions are deliberately left alone — a lost position has no neutral value, and
pretending otherwise moves geometry. The same truncation then renders 22.84 dB instead of 9.93 dB.

This is the fifth defect of the same family in this codec (M19/M20 found four): *a stream exists, but
its side information does not*. None of them is visible in a byte count; each one needed a decode.

## Timing and memory (P4)

| file | bytes | decode | decode + PLY | encode |
|---|---|---|---|---|
| bicycle c10_o8_sh3 | 144.55 MB | 6.82 s | 15.9 s | 52 s |
| bicycle c8_o8_sh3 | 139.76 MB | 5.41 s | 14.7 s | 61 s |
| bicycle c10_o8_sh3 (scalable) | 178.18 MB | 12.09 s | 19.8 s | 90 s |
| stump c10_o8_sh3 | 118.88 MB | 5.47 s | 12.6 s | 43 s |
| stump c10_o8_sh3 (scalable) | 146.86 MB | 9.72 s | 16.1 s | 75 s |

Peak RSS 13.7 GB for a 6.13 M-primitive model including the source; the decoder itself allocates
about 2.2 GB of float64 code arrays per attribute, which is the largest single item and the obvious
place to stop paying (int16 would halve it). Decode times above include cold file I/O when the
reader runs in a fresh process (28–34 s for the first read of a 178 MB file); the in-process numbers
in the ladder table are the honest ones for scaling claims.

Damage locality was established in M19 on the same frame layout (a 1 % burst damages one frame =
4.05 % of that stream, 0.00 % of positions move). Re-running it on the 178 MB scalable file was
started and had not finished after 20 minutes — the damage path re-decodes the whole model four
times — so this round reports M19's number and does not claim a new one.

## Verdict

`progressive_not_worth_it`, with a shipped consolation that is bigger than the thing that failed:
bit-plane separability costs 23 % and produces a non-monotone ladder, so the format keeps the
best-rate layout and gains a *free* two-step ladder from two changes — stream order (already right)
and neutral fill for lost code frames (new). Fine-grained rate scaling in this representation is not
worth a quarter of the file.

What would make it worth the bytes: layers that are not bit-planes. A codebook split (coarse shared
dictionary, then per-primitive residuals) degrades in the *reconstruction* rather than in the code
space, so each extra layer is guaranteed to help — that is the VQ direction M16 measured at 20 ×,
and it is the only refactor that could make a five-step ladder pay for itself.

## Reproduction

```bash
SCENE=bicycle bash experiments/run_m17.sh data      # COLMAP images_4 + mirror 30k PLY
SCENE=bicycle bash experiments/run_m17.sh base      # archive + clean PSNR (24.52 dB)
bash experiments/run_m21.sh encode                  # best-rate and rate-scalable files
bash experiments/run_m21.sh ladder                  # truncate at every layer boundary, export PLY
bash experiments/run_m21.sh render                  # archive entry + held-out PSNR per step
bash experiments/m21_free.sh                        # the free boundary on the best-rate file
python experiments/m21_lut_probe.py                 # which reconstruction level each cut should use
python experiments/m21_sizes.py --help              # attribute-level attribution of a file
```

Costs on the node: setup 37 min (2.6 GB PLYs + two scenes of COLMAP), encode 18 min, ladder 12 min,
render 16 min, free boundary 8 min. Total 2.3 h ≈ ¥6.4.
