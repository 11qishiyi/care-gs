# M38 — the joint geometry codebook: fewer symbols, at a price the picture notices

Round 34 · node 2141436 (A100-PCIE-40GB, ¥2.80/h, rented 00:19, released 01:20 ≈ ¥2.9) · pre-registered in
[`tools/m38_spec.md`](../tools/m38_spec.md) at 00:20, before the code existed.

## The question

M29 established that the geometric codes are *at their entropy*: `cluster_off` sits at 10.00 B/code against
H0 = 9.99, `geo_scales` 6.67 against 6.82, `geo_quat_abc` 7.88 against 7.76. No coder can take bytes out of
symbols that are already independent. The only remaining lever is to spend **fewer symbols**: one index into
a shared codebook for the 8-dimensional tuple

    x = (log σx, log σy, log σz, qw, qx, qy, qz, logit α)

instead of four independently coded groups (44 bits/primitive today: 18 scale + 20 rotation + 6 opacity).

## Design

Fit a k-means codebook (k ∈ {4096, 16384, 65536}) on the published bicycle model's 6,131,954 attributes,
assign every primitive, and replace the four scalar streams with `geo_vq_idx` (log2 k bits) + `geo_vq_cb`
(k × 8 float16). Everything else — cluster positions `c8`, SH DC 6-bit, the rank-16/48-bit colour basis — is
the M35 shipping configuration, so the container is byte-comparable with the 76.56 MB / 24.06 dB baseline.

Attributes are reordered by the same Morton permutation as the position stream: the first version of
`encode_attrs` skipped it and described the wrong primitive per row, which the round-trip test caught as a
0.04 disagreement in log-scale.

## Measurements (bicycle, 25 held-out views, same archive and protocol as every round since M31)

| k | container | B/primitive | PSNR | SSIM | index bits | codebook |
|---|---|---|---|---|---|---|
| 4096 | 54,606,955 B | 8.905 | 19.58 | 0.5149 | 12 | 65,536 B |
| 16384 | 56,338,847 B | 9.188 | 19.61 | 0.5270 | 14 | 262,144 B |
| 65536 | 58,598,006 B | 9.556 | 20.36 | 0.5587 | 16 | 1,048,576 B |
| scalar baseline (M35 `gp6-6-6_c8_sh3`) | 76,556,000 B | 12.480 | **24.06** | 0.7393 | — | — |

Codebook distortion (relative RMSE over the 8-D tuple): 8.24 % / 6.92 % / 5.83 %; the log-scale dims carry
the largest absolute MSE (0.167 / 0.113 / 0.078 — an RMSE of 0.28 in log units is a 32 % scale error at
k = 65536).

## Verdict

* **L1 FAIL** — the best codebook reaches 20.36 dB, not 24.00. The byte target was met easily (58.6 MB ≤ 66)
  and the quality target missed by 3.7 dB.
* **L2 moot** — the codebook is not the cost at any of the three sizes (65 kB–1 MB against a 58 MB file);
  the distortion is.
* **L3 PASS** — encode 166–174 s, decode and render unchanged (10.5–11.8 s per render).
* **L4 PASS** — codebook bytes inside the container, scalar attribute streams *removed* (a test asserts
  they are gone, so nothing is paid for twice).

Branch: **`scalar_is_already_better`**.

## At equal bytes it is 2.2 dB worse, which is the comparison that matters

The container shrank by 18–22 MB, so the honest question is what the *scalar* path does at 58.6 MB. M35's
measured curve answers it: `gp4-4-4_c6_sh3` is 57.23 MB at 22.53 dB and `gp5-5-5_c7_sh3` is 69.34 MB at
23.80 dB, so at 58.6 MB the scalar container renders **≈ 22.6 dB** — 2.2 dB *above* the k = 65536 codebook at
the same size. The codebook is not merely worse than the baseline; it is below the curve the baseline already
traces.

## Why it fails, in one paragraph

A codebook wins when the data lies near a low-dimensional manifold, so that one cell in 8-D replaces many
per-dimension cells. These attributes do not: at k = 65536 and 6.13 M primitives every cell holds ~93 points,
and the local spread of a scale triple plus a unit quaternion plus an opacity is large — the quaternion alone
fills a 3-sphere. Scaling the codebook 16× (4096 → 65536) buys 0.78 dB for 4 MB, i.e. the curve is flat in
the direction that matters, while the scalar path at 44 bits/primitive spends its bits where the variance
actually is, one dimension at a time, after entropy coding.

**The negative result has a sharp edge worth keeping**: M29 said the codes are at their entropy, and M38 now
says their *joint* distribution is not compressible either — at least not by a vector quantiser at these
budgets. What both rounds together rule out is the whole family "reduce the number of symbols per primitive".
The bytes are in the *number of primitives*, which is what M26's prune-and-fine-tune pipeline exploits and
what HAC/PCGS do with anchors instead.

## Cost

Node 2141436: one hour of A100 ≈ ¥2.9 (three encodes, three renders, one setup).

## Reproduce

```bash
bash experiments/run_m38.sh setup
for K in 4096 16384 65536; do bash experiments/run_m38.sh encode $K; bash experiments/run_m38.sh render $K; done
```

## Files

* code — `experiments/m38_vq.py` (`attr_matrix`, `fit`, `assign`, `build`, `decode_attrs`), `experiments/run_m38.sh`, `tools/m38_build.py`
* container — `experiments/m19_codec.py` (`ORDER` gains `geo_vq_cb`/`geo_vq_idx`; `decode` dispatches to the codebook path)
* tests — `experiments/tests/test_m38_vq.py` (4: round trip, codebook counted once, missing codebook fails loudly, quaternion sign canonicalisation)
* artifacts — `experiments/artifacts/a4/m38/{render.txt,m38_time.txt,k4096.json,k16384.json,k65536.json,m38.log}`
