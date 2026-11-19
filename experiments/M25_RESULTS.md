# M25 results: the decoder is now deployable (round 21, 2026-11-16)

**Verdict: `decoder_deployable`.**  Same file, same pixels, **7.41 GB → 1.97 GB** of peak decode memory
(−73 %) and **11.80 s → 7.69 s**.  The bitstream did not move by one byte.

## Criteria

| | pre-registered | measured | verdict |
|---|---|---|---|
| **D1** | peak RSS ≤ 2.0 GB | **1.97 GB** (from 7.41) | **PASS** |
| **D2** | decode ≤ 9.0 s | **7.69 s** (from 11.80) | **PASS** |
| **D3** | rendered PSNR within 0.005 dB of 24.08 | **24.08 dB**, SSIM identical to 8 digits | **PASS** |
| **D4** | no regressions | 77 tests, containers of every earlier round still decode | **PASS** |

## Where the 5.4 GB went

| change | why it was 7.41 GB | effect |
|---|---|---|
| reconstruct in float32, not float64 | every attribute was widened to float64 for arithmetic the renderer throws away | the rest block alone: 2.21 GB → 1.10 GB |
| solve the basis in chunks of 1 M primitives | `coef @ basis` materialised a full 6.13 M × 45 float64 result | peak = answer + one chunk, not three answers |
| narrow integer code arrays (uint8/uint16, not int64) | 48-bit colour codes were 8 bytes each where 1 was enough | 785 MB → 98 MB |
| chunked bit unpacking | `unpackbits` expands to a byte per bit, then the accumulate doubled it | no full-size temporary |
| quaternions decoded straight to float32 | smallest-three ran in float64 and stayed there | 196 MB → 98 MB |

**The floor is the answer.**  The decoded tensors are 1447 MB in float32 — 89 % of the final 1.97 GB
figure.  The decoder's own overhead is now 0.52 GB (36 %), and no further change can go much below
1.45 GB without changing what `decode()` returns (a streaming API that hands out chunks and never
materialises the whole block would; that is a different interface, not a cheaper decoder).

## Deployment table, with the numbers a reader asks for

| | bicycle, `gp8-6-6_c9_sh3` r16/48 |
|---|---|
| file | 83.41 MB (17.35×) |
| primitives | 6,131,954 |
| encode | 51 s |
| decode | **7.69 s** |
| peak decode RSS | **1.97 GB** |
| decoded tensors | 1447 MB (float32) |
| PSNR | 24.08 dB (clean 24.52) |

For comparison at a similar operating point: PCGS reports 20.5 s decode and HAC's decoder is
reported in the same order; both operate on 1–2 M primitives.  On 6.1 M primitives our decoder is
faster than PCGS's on a third of the primitives, and its footprint is now comparable to the renderer's
own.

## What this changes in the paper

The deployment section can now claim three things that were not true before: a 17× model decodes in
under eight seconds, in under 2 GB, on one core, with the same pixels.  The memory number also closes
the last dimension where this codec looked worse than the published ones — it was the only row in the
comparison table where we had no defence.

## Reproduce

```bash
bash experiments/run_m25.sh setup
bash experiments/run_m25.sh encode   # 83.41 MB container
bash experiments/run_m25.sh time     # fresh process per file: 7.69 s, 1.97 GB
bash experiments/run_m25.sh render   # 24.08 dB
```

Node: A100-PCIE-40GB (2140571), rented 23:34, released 00:08, ~35 min of it setup, ≈ ¥2.2.  Tests:
**77 passed**, including the three new ones in `test_m25_decode.py` (chunk invariance, float32 contract,
smallest-three path matches the encoder).

## Artifacts

`experiments/run_m25.sh`, `tools/m25_time.py` (fresh process per measurement — `ru_maxrss` is a
high-water mark, so timing after an encode would report the encoder's peak), `tools/m25_spec.md`,
`experiments/tests/test_m25_decode.py`,
`experiments/artifacts/a4/m25_{time.log,render.log,encode.log}`.
