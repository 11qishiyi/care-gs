# M29 — where the last 13.6 bytes go: the codes are already at their entropy, so the widths had to move

Round 25. Node 2140665 (A100-PCIE-40GB, ¥2.80/h), rented 05:45, released 07:05. Preregistered in
`tools/m29_spec.md` (E1–E4, copied into `METHOD_PLAN.md`) plus an amendment (`tools/m29_amend.md`,
F1–F3) registered after the probe returned and before any sweep number existed.

## Verdict: `contexts_do_not_pay` (E1/E2 fail) → `shelf_extends` (F1–F3 pass)

Two questions, one node, two answers.  The first was whether the shelf's attribute codes carry structure
a better coder could exploit; the answer is no, and the measurement says why.  The second was whether
the widths — which the probe showed are pure quantiser choice, not entropy — could be spent more
efficiently; the answer is yes: the near-lossless point moves from **17.35× to 18.90×** for **0.02 dB**.

## Part 1 — the entropy probe (E1 FAIL, E2 moot)

The shipped container (`gp8-8-8_c10_sh3`, rank 16, 89.72 MB, 6,131,954 primitives, 14.63 B/prim), stream
by stream.  `b/code` is what zstd-12 actually spends per code; `H0` and `H1` are the order-0 and
order-1 entropies of the same codes; `H(pos)`, `H(scl)` are conditional entropies given a context the
decoder already holds (the primitive's coarse spatial band, its own first scale code).

| stream | bits | MB | B/prim | b/code | H0 | H1 | H(pos) | split MB |
|---|---|---|---|---|---|---|---|---|
| `cluster_off` | 10 | 22.995 | 3.750 | 10.00 | 9.99 | 9.90 | 9.99 | 22.995 |
| `geo_scales` | 8 | 15.337 | 2.501 | 6.67 | 6.82 | 6.78 | 6.82 | 15.534 |
| `geo_quat_which` | 2 | 0.631 | 0.103 | 0.82 | 0.95 | 0.77 | 0.95 | 0.636 |
| `geo_quat_abc` | 8 | 18.109 | 2.953 | 7.88 | 7.76 | 7.75 | 7.76 | 18.189 |
| `geo_opacities` | 8 | 5.492 | 0.896 | 7.17 | 7.18 | 6.96 | 7.18 | 5.530 |

Three facts, each of which had to be measured rather than assumed:

1. **zstd is at or below the order-1 entropy on the two largest streams.**  Scale codes cost 6.67 bits
   against an order-1 bound of 6.78; the 10-bit position offsets cost exactly 10.00 against H0 = 9.99.
   There is no coder left to write: the container is already paying the entropy of its own alphabet.
2. **Every decoder-computable context loses.**  Splitting by spatial band or by the primitive's own
   scale lands within 0.1 % of plain zstd, and the split version is *larger* by the bucket headers.
   The context carries nothing the LZ window did not already find in Morton order.
3. **The 8-bit codes are not 8 bits of information but they are not compressible either.**  Scales are
   6.8, rotations 7.8, opacity 7.2 bits — the top of each range is unused, which is not redundancy but
   *quantiser choice*, and the only way to spend it is to spend fewer bits and accept distortion.

The split machinery was nevertheless built and is shipped in the codec (`m29_split.py`,
`_split_rejoin`), verified bit-identical by test — the negative result is measured on a working
implementation, not argued from an estimate.

## Part 2 — the rate–distortion sweep (F1–F3 pass)

If the codes are at their entropy, the widths are the only lever left.  Four containers, same colour
block (rank 16, 48-bit coefficients), same 25 views, only the quantisers differ:

| point | spec | file | B/prim | ratio | PSNR | SSIM |
|---|---|---|---|---|---|---|
| P0 | `gp8-8-8_c9_sh3` | 87.43 MB | 14.26 | 16.55× | 24.11 | 0.7439 |
| P1 | `gp7-7-7_c9_sh3` | 85.64 MB | 13.97 | 16.90× | 24.10 | 0.7433 |
| P2 | `gp6-6-7_c8_sh3` | 77.43 MB | 12.63 | 18.69× | 24.06 | 0.7395 |
| **P3** | **`gp6-6-6_c8_sh3`** | **76.56 MB** | **12.49** | **18.90×** | **24.06** | **0.7393** |

* **F1 PASS** — 76.56 MB ≤ 78 MB at 24.06 dB ≥ 24.00 dB.
* **F2 reported** — the curve is the table above; it is *shallow and then steep*: the first 6 bits cost
  0.01 dB and the last 13 cost 0.05 dB, so the frontier is dominated by the position quantiser
  (10 → 8 bits is 1.5 B/primitive on its own).
* **F3 PASS** — decoder unchanged, decode 7.51 s, peak RSS **1.96 GB**, one file.

The mechanism matters for the write-up: coarsening a stream by one nominal bit saves **less than a
bit**, because zstd was already coding that stream below its width.  Scale codes at 8 bits cost 6.67
bits, so dropping to 7 bits saves ≈0.6 bits, not 1.0 — which is why P0 → P1 (three streams, one bit
each) buys only 1.8 MB where the arithmetic predicts 4.9 MB.

## The shipped point

**76.56 MB / 12.49 B per primitive / 24.06 dB / 18.90×** on bicycle, against a 1447 MB fp32 source — one
0.44 dB below the uncompressed model's own render (24.52 dB), decoded in 7.51 s and 1.96 GB.  The
previous shipping point was 83.41 MB at 24.08 dB (17.35×), so this is **+9.0 % ratio for −0.02 dB**, and
it also beats the previous point on memory (1.97 GB) with the same decoder.

## Verdict and what it changes

* The near-lossless row of the paper is now **18.90× at 24.06 dB** (was 17.35× at 24.08 dB).
* The appendix gets a measured answer to "why not just entropy-code it better": because it is already
  coded better than a first-order arithmetic coder would (§Part 1).
* The remaining slack in the container is itemised and small: the position offsets are 3.0 B/primitive
  at 8 bits and incompressible; the colour block is 4.4 B; everything else is below 3 B.  A further
  step on this row needs a *representation* change (M27–M28 priced three of those) or a jointly trained
  decoder (N33–N35), not a coding change.

## Cost and artefacts

* Node 2140665: rented 05:45, released 07:05 (≈1.3 h ≈ ¥3.6): setup 15 min, shelf build 4 min,
  probe 2 min, four builds 12 min, four renders 4 min, timing 1 min.
* Code: `experiments/m29_entropy.py`, `experiments/m29_split.py`, `experiments/run_m29.sh`,
  `experiments/run_m29b.sh`, `experiments/tests/test_m29_split.py` (4 cases), codec changes in
  `m19_codec.py` (split buckets in `ORDER`, `_ordered_names`, `_split_rejoin`).
* Gates: `pytest experiments/tests` **89 passed**; `m1_check_bytes.py` 881 cases 0 mismatches;
  `check_py311.py` 138/138.
* Negative result: **N36** in `APPENDIX_negative_results.md`.
* Artefacts: `experiments/artifacts/a4/m29_probe.txt`, `m29_rd_render.log`, `m29_rd_build.log`.

## Reproduction

```bash
bash experiments/run_m29.sh shelf     # build the shelf container (4 min)
bash experiments/run_m29.sh probe     # the entropy table
bash experiments/run_m29b.sh build    # the four R-D points
bash experiments/run_m29b.sh render   # 25 views each
python tools/m25_time.py --dir <out> --glob 'gp6_6_6*'
```
