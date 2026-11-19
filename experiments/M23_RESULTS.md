# M23 results: geometry, coded again (round 19, 2026-11-15)

**Verdict: `deltas_not_enough`** — of the three changes, one paid and two did not.  Smallest-three
quaternions are free and worth **4.97 MB**; recoding the geometry as Morton-order deltas is lossless and
worth **0.27 MB**, i.e. nothing.  The near-lossless shelf moves from **14.69× to 15.51×**
(93.30 MB / 24.12 dB), not the 17× the round was aiming for.

## Criteria (pre-registered in METHOD_PLAN before the data, G1–G4)

| | criterion | measured | verdict |
|---|---|---|---|
| **G1** | rendered PSNR ≥ 24.02 dB (M22 point 24.12 − 0.10) | **24.12 dB**, all four variants | **PASS** |
| **G2** | file ≤ 85 MB (≥17.0×) | **93.30 MB** = 15.51× | **FAIL** |
| **G3** | decode ≤ 12 s | **10.45 s** | **PASS** |
| **G4** | delta path decodes to identical levels | identical tensors *and* identical packed streams | **PASS** |

## The four (six) variants, same model, same rank-16/48-bit colour

| variant | what it adds | file | B/prim | PSNR | ratio | Δ bytes |
|---|---|---|---|---|---|---|
| A_base | the M22 point, reproduced | 98.54 MB | 16.07 | 24.12 | 14.69× | — |
| B_delta | + int16 deltas on 3 streams | 100.74 MB | 16.43 | 24.12 | 14.37× | **+2.20** |
| C_st3 | + smallest-three quaternions | 93.57 MB | 15.26 | 24.12 | 15.47× | **−4.97** |
| D_both | B + C | 93.30 MB | 15.22 | 24.12 | 15.51× | −5.24 |
| E_block | + block-mean residuals (modular) | 98.27 MB | 16.03 | 24.12 | 14.73× | −0.27 |
| F_st3blk | C + E | 93.30 MB | 15.22 | 24.12 | 15.51× | −5.24 |

The first delta attempt was int16 and **cost 2.20 MB**.  The post-mortem is in the stream table below;
the modular-uint8 rewrite (same width as the levels, lower entropy) removed the loss but recovered only
0.27 MB.

## Stream-level post-mortem (raw bytes before the zstd frames)

Positions, scales and opacity, plain versus recoded (A → E_block):

| stream | plain | recoded | note |
|---|---|---|---|
| `cluster_off` | 22.99 MB | — | rejected: 10-bit packed is **1.25 B/level**, an int16 delta is 2.00 B; the alignment tax exceeded the correlation it exposed |
| `geo_scales` | 18.40 MB (3 B/prim) | 18.40 MB (residuals, same width) | −0.20 MB on the file |
| `geo_opacities` | 6.13 MB (1 B/prim) | 6.13 MB (residuals) | −0.07 MB on the file |

**That is the finding.**  Same width, same pre-zstd byte count, residuals instead of levels — and zstd's
answer moves by 1.5 %.  The quantised attribute fields carry no spatial redundancy that a byte coder can
see: whatever smoothness the continuous field has, the 8-bit quantiser has already flattened it into a
distribution that is uniform *conditional on position*.  The delta transform buys nothing because there
is nothing there.

Quaternions, plain versus st3 (A → C_st3):

| stream | plain | st3 |
|---|---|---|
| `geo_quats` | 24.53 MB (4 × 8 bit) | — |
| `geo_quat_abc` | — | **18.40 MB** (3 × 8 bit) |
| `geo_quat_which` | — | 0.77 MB (2 bit) |

25 % off the quaternion stream before zstd, 4.97 MB off the file, **0.00 dB** — which is what M15's
eight-asset attribution predicted (quaternion 8 → 6 bits with st3: 0.00 pp) and the first time it has
been measured inside the shipped container rather than through a variant sweep.

## Why the round missed G2

The 85 MB target assumed the three streams could give up 10 MB.  Their total after zstd is about 44 MB
(positions 23.0, scales 15.3, opacity 5.5), so 10 MB would have been a 23 % cut on blocks zstd already
considers incompressible.  The only stream with real headroom turned out to be the quaternions, and 5 MB
of it was structural (26 bits instead of 32), not statistical.  **Fifth time in this series that the
answer was "the alphabet, not the model"**: M20 (+8.2 % from one-code-per-byte), M21 (bit planes cost
23 %), M23 (st3 −25 % of a stream), and twice that a cleverer statistical model lost to zstd.

## What ships

`spec = gp8-8-8_c10_sh3` (positions c10, scales/opacity 8 bit, **quaternions via st3 at 8 bits**,
SH rest via the M22 rank-16 basis at 48 bits) at **93.30 MB / 15.22 B per primitive / 24.12 dB /
15.51×**, decode 10.45 s.  That is the new near-lossless shelf point and it should become the default
geometry coding: it is 5 % smaller than the shelf for the same pixels.

## Reproduce

```bash
bash experiments/run_m23.sh encode   # six variants, bit-exactness checked in-process
bash experiments/run_m23.sh render   # held-out PSNR of each
python experiments/m23_streams.py A.gs1 E.gs1   # the stream table above
```

Node: A100-PCIE-40GB (2140508), rented 21:17, released 22:28, ~1.2 h ≈ ¥3.3.  Encode 51 s, decode
10.5 s per variant.  Tests: `pytest experiments/tests` **71 passed**, including
`test_the_delta_path_is_bit_exact`, `test_the_restored_streams_are_identical`,
`test_the_density_of_the_deltas_is_what_pays`.

## Artifacts

`experiments/m23_pred.py`, `experiments/m23_run.py`, `experiments/m23_streams.py`,
`experiments/run_m23.sh`, `experiments/tests/test_m23_delta.py`,
`experiments/artifacts/a4/m23_{encode.json,render.log,streams_block.txt,streams_st3.txt}`,
`tools/m23_spec.md`.
