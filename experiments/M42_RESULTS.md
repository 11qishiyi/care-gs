# M42 — where the encoder's 18.8 GB went, and how much of it was removable

Round 25, 2026-11-17. Node 2141494 (A100-PCIE-40GB, ¥2.80/h), rented 04:45, released after the A/B.
Pre-registered in `tools/m42_spec.md` before any measurement.

## The probe first

`tools/m42_mem.py` runs the shipping build stage by stage in one process and prints current and peak RSS
(`experiments/artifacts/a4/m42_probe.log`, bicycle):

| stage | current | peak | note |
|---|---|---|---|
| start | 0.4 GB | 0.4 GB | |
| load_model | 1.8 GB | 4.3 GB | 6,131,954 primitives, PLY parse spikes |
| attribute_arrays | 4.5 GB | 4.8 GB | rest block is 2.21 GB of float64 |
| morton_order | 4.6 GB | 4.9 GB | |
| **encode_layout[bits]** | 4.8 GB | **18.8 GB** | the peak lives here, and the current RSS afterwards is 4.8 GB |
| encode_layout[bytes] | 5.1 GB | 18.8 GB | |
| alphabet_choice | 5.1 GB | 18.8 GB | |
| rest_matrix | 6.2 GB | 18.8 GB | |
| basis_fit | 6.6 GB | 18.8 GB | |

So the 18.8 GB was **transient**, inside `m4_bytes._encode`: `codes_published_sh_parts` allocated four full-size
float64 temporaries (2.2 GB each for 276 M SH codes) and `pack_bits` built an `int64` plane array of
`codes x bits` (6.6 GB, twice). Neither is required by the format — the quantiser's scale is a per-row maximum
and a chunk of 8 codes occupies a whole number of bytes, so both stages slice exactly.

## The change

* `m4_bytes.codes_published_sh_parts(block, bits, chunk=1<<20)`: per-row work in `chunk`-row slices into one
  pre-allocated `int64` output; arithmetic unchanged.
* `m4_bytes.pack_bits(codes, bits, chunk=1<<24)`: bit planes in slices whose bit count is a multiple of 8, so the
  concatenation equals the whole-array `packbits`.
* `experiments/tests/test_m42_encoder_mem.py` holds both to the whole-array formulas, at every bit width the
  format uses, including chunk sizes that do not divide the row count.

## The A/B, on one node

Old and new in separate processes on the same host, same model, same spec, same `--jobs 4`:

| scene | build, whole-array | build, sliced | speed | peak RSS, whole-array | peak RSS, sliced | memory | container |
|---|---|---|---|---|---|---|---|
| bicycle | 190.1 s | **150.1 s** | 1.27× | 18.38 GB | **11.63 GB** | **−37 %** | 76,598,203 B, md5 `151dd603…` both |
| stump | 127.2 s | **103.9 s** | 1.22× | 14.94 GB | **9.51 GB** | **−36 %** | 62,649,653 B, md5 `2a9ad2c1…` both |
| bonsai | 21.4 s | **19.9 s** | 1.08× | 4.07 GB | **2.78 GB** | **−32 %** | 15,297,685 B, md5 `cae84e94…` both |

## Verdict — `cheaper_but_not_enough` (a label chosen after the data, not pre-registered)

* **L3 PASS.** The containers are byte-identical to the M40/M41 files on all three scenes, at every stage of the
  A/B. The slicing is a pure memory/time change.
* **L4 PASS.** Same file ⇒ same tensors (`read_container` + `decode` equality is in the test suite).
* **L1 FAIL.** Peak RSS 11.63 GB against a target of 6.0 GB. The two spikes are gone; what is left is not
  spikes but **live data**: the float64 attribute arrays (4.5 GB, of which the SH rest block is 2.21 GB), the
  `int64` code array (2.21 GB), and three candidate layout encodings alive at once (0.5 GB).
* **L2 FAIL.** 150 s of build against a target of 100 s. Note the cross-host caveat below: this is a slower host
  than M41's, so the honest comparison is the same-node ratio, 1.27×, not the absolute number.

The branch names pre-registered for this round (`encoder_fits_in_memory` / `the_memory_is_the_format` /
`cheaper_and_different`) do not describe the outcome: it is cheaper, it is not cheap enough, and it is not
different. The label above says that, and the failed criteria are reported as failures rather than re-scaled
after the fact.

## What is left, measured rather than guessed

1. **Code arrays are `int64` where `uint8` would do** (codes ≤ 2^bits ≤ 64 at 5-bit SH): 2.21 GB → 0.28 GB.
2. **The SH rest block is float64 in RAM** because `_attribute_arrays` upcasts the PLY's float32; the fit needs
   float64 to stay byte-identical, but the quantiser does not — it could read a float32 view.
3. **Three layout candidates are materialised at once** (`cand = {lay: _encode(...) for lay in LAYOUTS}`): the
   alphabet choice only needs the SH streams of two layouts, so geometry can be built once.
4. **`load_model` itself spikes 4.3 GB** to read a 1.52 GB PLY, before any encoding starts.

Together these bound the next attempt at ~3 GB and would also cut the build — the same three structures are what
the encode spends its time on.

## Cross-host caveat worth recording

M41 measured the bicycle build at 58.9 s and this round at 150.1 s for the *same* code path and the same model,
on two A100-PCIE hosts in the same pool. That is a 2.5× spread in wall clock, so encode-time claims are only
meaningful as same-node A/B — which is why this round re-measured the old implementation instead of quoting
M41's number as a baseline.

## Files

`experiments/M42_RESULTS.md` (this), `experiments/artifacts/a4/m42_{bicycle,stump,bonsai}_{sliced,legacy}.json`,
`m42_probe.log`, `experiments/run_m42.sh`, `tools/m42_mem.py` (stage probe), `tools/m42_encode.py` (A/B driver
with `--legacy`), `experiments/tests/test_m42_encoder_mem.py` (4 cases).

## Reproduce

```bash
bash experiments/run_m42.sh     # six runs: 3 scenes x {sliced, legacy}
python -m pytest experiments/tests/test_m42_encoder_mem.py -q
```

Cost: ~0.6 h ≈ ¥1.7.
