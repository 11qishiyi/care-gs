# M20 — the SH block: layout wins, modelling does not

**Round 16, 2026-11-15. Node 2140325 (A100-PCIE-40GB, ¥2.80/h).**

The SH block is the file. On bicycle it is 74.4 MB of a 151.7 MB container: 45 coefficients at
3 bits (103.48 MB raw), their per-primitive scales (12.26 MB), and the DC block (6.90 MB). M15 §4
priced entropy coding as the last lever in the family and guessed 15 %; M19 made the block a real
stream, so the guess could finally be measured.

## 1. Probe: what the bytes actually cost

Per stream, bicycle `c10_o8_sh3`, zstd-12 (`experiments/m20_probe.py`):

| stream | raw | zstd | note |
|---|---|---|---|
| `sh_rest` | 103.48 MB | **70.45 MB** | 11.49 B/prim; the file's centre of mass |
| `geo_quats` | 24.53 MB | 23.69 MB | smallest-three, 8 bit |
| `cluster_off` | 22.99 MB | 23.00 MB | **zstd recovers nothing** |
| `geo_scales` | 18.40 MB | 15.34 MB | |
| `sh_scale` | 12.26 MB | 8.19 MB | two 8-bit scales per primitive |
| `sh_dc` | 6.90 MB | 3.76 MB | |
| `geo_opacities` | 6.13 MB | 5.49 MB | |

Eleven layouts over the same codes, all lossless re-arrangements:

| layout | MB | B/prim | vs V0 |
|---|---|---|---|
| V0 bit-packed, one frame (current) | 70.45 | 11.49 | — |
| V1 coefficient-major | 82.61 | 13.47 | −17.3 % |
| V2 one frame per coefficient | 83.63 | 13.64 | −18.7 % |
| V3 split by bit-plane | 77.66 | 12.66 | −10.2 % |
| V4 plane × coefficient frames | 89.37 | 14.57 | −26.9 % |
| V5 delta vs previous primitive | 73.71 | 12.02 | −4.6 % |
| V6 delta vs coefficient −3 | 81.12 | 13.23 | −15.1 % |
| **V7 one byte per code, prim-major** | **64.64** | **10.54** | **+8.2 %** |
| V8 one byte per code, coef-major | 84.68 | 13.81 | −20.2 % |
| V10 byte delta vs previous | 74.77 | 12.19 | −6.1 % |
| V11 byte delta vs band | 75.39 | 12.29 | −7.0 % |

**The conditional entropies say the opposite of what the intuition says.** On the same codes:

| bound | B/prim |
|---|---|
| H0 per-coefficient order-0 | 13.96 |
| H1 given the previous primitive's code (Morton) | 11.93 |
| H2 given previous + DC bucket | 11.84 |
| H3 per bit-plane given the previous primitive's bit | 14.90 |
| H4 given the coefficient three columns away (adjacent band) | 13.65 |
| **zstd-12 on V0** | **11.49** |

Every context I could think of bounds the block *above* what plain zstd already achieves. zstd's
block-adaptive FSE/Huffman tables are exploiting serial structure that per-coefficient static
contexts throw away — the "context model the SH block" plan would have built a coder that is 3 %
worse than the compressor already in the format. What zstd was missing was not a better model but
a better alphabet: handed bit-planes it can only model bit marginals, handed bytes it models the
eight symbols as symbols. **8.2 % fell out of a one-line layout change.**

## 2. Shipped

`sh_layout="bytes"` is now the container default (`experiments/m19_codec.py`); the header records
which layout a file uses, so `bits` files still decode.

| scene | variant | bits | bytes | verdict |
|---|---|---|---|---|
| bicycle | `c10_o8_sh3` | 151.72 MB / 9.54× / dec 8.05 s | **144.55 MB / 10.01× / dec 5.33 s** | **C8 pass** |
| bicycle | `c8_o8_sh3` | 146.93 MB / 9.85× / 3.99 s | **139.76 MB / 10.35× / 3.99 s** | |
| bicycle | `c8_o8_sh2` | — | **103.28 MB / 14.01× / 3.52 s** | |
| bicycle | `m16_o8_sh4` | 190.76 MB (model) | **186.84 MB / 7.75× / 3.92 s** | was undecodable |
| bicycle | `vq12_c8_o8` | 72.15 MB / 20.05× / 2.86 s | **72.30 MB / 20.02× / 2.82 s** | +0.04 %, see below |
| stump | `c10_o8_sh3` | 124.19 MB / 9.43× / 4.42 s | **118.88 MB / 9.85× / 4.42 s** | |

Decoded codes are bit-identical in every comparison (`codes==True`): this is a re-layout, not a
trade. Decode is 34 % faster on bicycle because a byte stream needs no bit-plane unpacking; the
zstd output is smaller, so there is less to inflate as well.

One measured regression, reported rather than hidden: the vector-quantised row grows 0.15 MB
(72.15 → 72.30, +0.04 %) because its DC block also switches layout while its 45 coefficients are a
codebook index, not a ladder. A per-stream choice would keep both wins; the magnitude (0.04 % on a
row that is not the near-lossless claim) did not justify another round of measurement here.

## 3. Criteria

- **C8** (≤ 145.0 MB at ≥ 24.20 dB): **PASS** — 144.55 MB = 10.01×, and fidelity is unchanged by
  construction since every code is identical (rendered 24.33 dB in M19).
- **C9** (≤ 133.0 MB, 10.9×): **FAIL** — 144.55 MB. The 2 B out of 21.7 B that 12× would need are
  not in this block's layout; the block is at 10.54 B/prim before its scales and DC.
- **C10** (decode ≤ 31.4 s): **PASS** — 5.33 s, and faster than the layout it replaces.

**Verdict: `sh_partial_win`.** The near-lossless shelf moves from 9.54× to 10.01× on bicycle and
9.43× to 9.85× on stump, for free. 12× remains out of reach, and the reason is now measured rather
than asserted: the SH block costs 10.54 B/prim with the best layout available, the geometry 7.97 B,
the scales 1.34 B, so a primitive cannot be cheaper than ~19.9 B and 12× needs ≤ 19.7 B.

## 4. A third and fourth defect of the M19 class

Shipped containers for the older geometry variants could not be decoded at all: `m16_o8_sh4` and
`sh16_g16` grid-code the *positions*, and the header carried the min/step of scales, quaternions and
opacities but never of the positions — `KeyError: 'means'`. Fixed by covering `means` whenever
`means_cluster_bits is None` (88 B instead of 64 B per file), reading it in the same order, and
charging it in both byte models.

Then it failed again, one layer down: the encoder did write `streams["geo_means"]`, but the
container's fixed `ORDER` tuple did not list it, so `write_container` silently dropped it and
`m16_o8_sh4` / `sh16_g16` still could not be read back. One name in a tuple; the shelf test now
walks `m16_o8_sh4`, `c8_o8_sh2` and `sh16_g16` as well, so a stream that exists but is not carried
fails in CI instead of in a measurement.

That is four appearances of the same class — a stream is produced, but its header, its carrier, or
its charge is missing — and every one was found by trying to decode, never by counting bits. The
pattern is worth naming in the paper: **a byte model is a claim about a format; until the format
decodes, the claim is untested.**

## 5. Reproduction

```bash
bash experiments/m20_setup.sh                     # 2.7 GB of reference PLYs from hf-mirror
bash experiments/m20_run.sh probe   --scenes bicycle --specs c10_o8_sh3
bash experiments/m20_run.sh measure --scenes bicycle,stump --specs c10_o8_sh3,c8_o8_sh3 \
                                    --layouts bits,bytes
```
Cost: probe 6 min (load 1.5 GB, 11 zstd passes over 103 MB, five entropy bounds), measurement
1 min per spec-layout pair. `huggingface.co` is reset from this node (`curl: (35)`); `hf-mirror.com`
answers at 2.0 MB/s, which is why `m20_setup.sh` names the mirror.

## 6. What is left in the family

Arithmetic, at bicycle scale (6,131,954 primitives, 236.0 B/prim fp32):

| item | B/prim | × |
|---|---|---|
| SH rest, best layout | 10.54 | |
| SH DC | 0.61 | |
| SH scales | 1.34 | |
| geometry (cluster 10 + 8-bit grids + st3-8) | 7.97 | |
| headers | 0.00 | |
| **total shipped** | **23.57** | **10.01×** |

12× needs ≤ 19.67 B. The gap is 3.9 B, of which 3.4 B would have to come out of 12.5 B of SH that
is already at its empirical floor under every context measured here. The honest conclusion, now
with numbers behind each clause: within this representation, near-lossless stops at 10×, and the
next factor has to come from primitives that carry fewer bits of their own — anchors, shared
decoders, or nothing at all.
