# M24 results: choose the alphabet per stream (round 20, 2026-11-15)

**Verdict: `alphabet_per_stream` — but not for the reason the round was proposed.**  The inherited
one-code-per-byte rule turned out to be *right* for the only stream that had a choice, and the 8.3 MB
the round was hunting came from somewhere else: a scale level the basis decoder never reads.  Shelf:
**93.30 MB → 83.41 MB**, 15.51× → **17.35×**, at −0.04 dB.

## Criteria

| | pre-registered | measured | verdict |
|---|---|---|---|
| **C1** | ≤ 85 MB (≥ 17.0×) at ≥ 24.02 dB | **83.41 MB = 17.35×** at **24.08 dB** | **PASS** |
| **C2** | container change is lossless | the container-only arm decodes **bit-identically**; PSNR 24.12 dB, exactly the M23 value | **PASS** |
| **C3** | decode ≤ 12 s | **11.80 s** (peak RSS 7.4 GB) | **PASS** |

## Attribution, in the order the round found them

| change | file | Δ | PSNR | cost |
|---|---|---|---|---|
| M23 shelf (`gp8-8-8_c10_sh3`) | 93.30 MB | — | 24.12 | — |
| **+ one scale level instead of two** | **89.72 MB** | **−3.58** | 24.12 | **free (lossless)** |
| + 6-bit scales and opacity (`o6`) | 85.71 MB | −4.01 | 24.09 | −0.03 dB |
| + 9-bit positions (`c9`) | **83.41 MB** | −2.30 | 24.08 | −0.01 dB |

### The alphabet question, answered honestly

| stream | packed bits (raw → zstd) | one code per byte (raw → zstd) | kept |
|---|---|---|---|
| `sh_dc` (3 cols × 3 bits) | 6.90 → **3.76 MB** | 18.40 → **3.69 MB** | **bytes** |
| `sh_scale` (1 level) | 6.13 → 4.36 MB | 6.13 → 4.36 MB | bits (identical) |

Packing the DC block shrinks it 2.7× before compression and **loses 0.07 MB after** it: one code per
byte lets the entropy coder see the correlation between the three colour channels, which is worth more
than the packing saves.  M20's rule, applied to a block it was not measured on, holds.  The round's
hypothesis was wrong and the measurement cost ten minutes.

### Where the bytes actually were

`sh_scale` carried **two** 8-bit levels per primitive — one for the DC block and one for the rest block.
Since M22 the rest block is not coded by the ladder at all: it is a basis, its scales are per-component
and global.  The second level was written, compressed, and then **never read by the decoder**.  One byte
per primitive of pure waste, 6.13 MB raw, 3.58 MB after zstd — 3.8 % of the file, larger than every
"clever" transform M23 tried.

The decoder now takes `sh_scale_levels` from the meta (default 2 for old files), and the encoder writes
one.

## Shipping point

`gp8-6-6_c9_sh3`, rank-16 basis at 48 bits per primitive:

| | |
|---|---|
| file | **83.41 MB** |
| bytes per primitive | **13.60** |
| PSNR (25 held-out views, 1236×822) | **24.08 dB** (clean 24.52, M23 shelf 24.12) |
| ratio vs fp32 (1447 MB) | **17.35×** |
| decode | 11.80 s, peak RSS 7.4 GB |
| encode | 51 s |

For anyone who wants the quality back: the container-only, lossless arm is 89.72 MB / 16.13× / 24.12 dB,
which is bit-identical to the M23 model and 3.58 MB smaller.

## What this round says about the series

Six rounds have now ended with "the alphabet, not the model": M20 (+8.2 % from one code per byte), M21
(bit planes cost 23 %), M23 (st3 −25 % of a stream), and two statistical models that lost to zstd.  This
round adds the counterpart lesson — **the alphabet rule is also not a magic wand**: applied honestly it
said "keep what you had", and the bytes came from an accounting defect instead.  Both lessons point the
same way: at this precision the container's job is to *not waste* bytes, and the model's job is to decide
what the bytes mean.  N32 records it.

## Reproduce

```bash
bash experiments/run_m24.sh setup
PLANS=gp8-8-8_c10_sh3:16:48 bash experiments/run_m24.sh encode   # 89.72 MB, lossless arm
PLANS=gp8-6-6_c10_sh3:16:48  bash experiments/run_m24.sh encode   # 85.71 MB
PLANS=gp8-6-6_c9_sh3:16:48   bash experiments/run_m24.sh encode   # 83.41 MB
bash experiments/run_m24.sh render
python3 tools/m24_time.py                                          # decode time and RSS
```

Node: A100-PCIE-40GB (2140540), rented 22:17, released 23:32, ~1.25 h ≈ ¥3.5.  Three encode+render
rounds, six containers, four renders.  Tests: **74 passed**, including
`test_the_rule_keeps_the_smaller_stream`, `test_the_layout_does_not_change_the_model` (bit-identical
tensors across alphabets) and `test_the_auto_container_is_no_larger_than_either_fixed_choice`.

## Artifacts

`experiments/m24_alpha.py`, `experiments/run_m24.sh`, `experiments/tests/test_m24_alpha.py`,
`tools/m24_time.py`, `tools/m24_spec.md`,
`experiments/artifacts/a4/m24_{encode_streams.txt,render.log,decode_time.txt}`.
