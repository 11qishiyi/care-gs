# M46 — the two colour alphabets run concurrently, and it is not worth it

**Round 29, node 2141501 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 06:12–06:25.** M45 left the alphabet search as one
geometry pass plus two independent colour passes and named a pool as the next lever. The pool works, keeps the bytes
identical, and takes 27 % off the phase — for **+3.9 GB of peak memory**, which is the wrong direction immediately after
four rounds spent removing 9.2 GB of peak. Verdict: `the_pool_costs_more_than_it_saves`; shipping stays sequential.

## Measured (one host, one session, one process per scene)

| scene | jobs | geometry | colour | phase | ratio vs sequential | peak | streams |
|---|---|---|---|---|---|---|---|
| bicycle | 1 | 8.9 s | 17.4 s | 26.3 s | — | 9.18 GB | `400a24b9…` |
| bicycle | 2 | 8.9 s | 10.3 s | 19.2 s | **0.734×** | 13.07 GB | same |
| bicycle | 4 | 8.9 s | 10.3 s | 19.2 s | **0.730×** | 13.07 GB | same |
| stump | 1 | 7.2 s | 14.0 s | 21.1 s | — | 7.48 GB | `68f5773e…` |
| stump | 2 | 7.2 s | 8.4 s | 15.6 s | **0.739×** | 10.98 GB | same |
| stump | 4 | 6.8 s | 8.3 s | 15.2 s | **0.720×** | 10.98 GB | same |
| bonsai | 1 | 1.3 s | 3.4 s | 4.7 s | — | 2.18 GB | `86e540f7…` |
| bonsai | 2 | 1.3 s | 2.1 s | 3.4 s | **0.723×** | 3.04 GB | same |
| bonsai | 4 | 1.3 s | 2.1 s | 3.3 s | **0.702×** | 3.04 GB | same |

## Criteria

* **N1 (≤ 0.70×) — FAIL**: 0.734 / 0.739 / 0.723 at two workers, 0.730 / 0.720 / 0.702 at four. Perfect two-way scaling
  would be 0.50; the measured 0.73 means the colour passes are ~46 % serialised against each other.
* **N2 (same bytes) — PASS**: the merged-stream digest is identical between sequential and pooled on all three scenes
  and the container md5s are the shipped ones (`151dd603…`, `2a9ad2c1…`, `cae84e94…`).
* **N3 (peak ≤ +0.7 GB) — FAIL**: +3.89 GB (bicycle), +3.50 GB (stump), +0.86 GB (bonsai). One extra stream set is
  ~0.36 GB; the other 3.5 GB is the two passes' per-slice float64 temporaries living at the same time.
* **N4 (`jobs=1` stays sequential) — PASS**: 26.3 / 21.1 / 4.7 s against M45's 26.3 / 21.2 / 4.6 s, and a test asserts no
  executor is constructed.
* **N5 (suite) — PASS**: 155 tests, 881 byte cases.

## Why it is GIL-bound, in one number

Two workers give 1.67× on the colour phase (17.4 → 10.3 s) and four workers give exactly the same 10.3 s. If the passes
were compute-bound and independent, two workers would give ~2× and four would still be ~2× (there are only two
alphabets) — but the flat response between 2 and 4 shows the limit is not the worker count, and 1.67× rather than 2×
shows the limit is the interpreter. The work inside `codes_published_sh_parts` and `pack_bits` is numpy ufuncs, which
release the GIL only in blocks; the surrounding Python (slicing, dtype handling, per-stream bookkeeping) does not.

## Decision

`build(..., jobs=1)` remains the default and every shipping path calls it. The pooled path is kept because it is tested
and because it is the right shape for a process pool — a `fork`-based pool would share the arrays copy-on-write and
would not pay the 3.5 GB — but that is a different round with its own criterion, and it must beat 0.73× without adding
memory before it ships.

## What this round adds to the encoder's ledger

| round | build (bicycle) | peak | what it bought |
|---|---|---|---|
| pre-M42 | 189.6 s | 18.38 GB | — |
| M42 | 135.8 s | 11.66 GB | sliced quantiser and packer |
| M43 | 126.9 s | 11.65 GB | narrow codes, one candidate |
| M44 | 108.9 s | 9.60 GB | gather instead of copy |
| M45 | 78.3 s | 9.18 GB | geometry built once |
| M46 | 78.3 s (sequential, kept) | 9.18 GB | pool measured and rejected |

Container: bit-identical throughout (76,598,203 B / `151dd603…`).

## Reproduction

```bash
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
bash experiments/run_m46.sh      # jobs 1, 2, 4 per scene
```

Artifacts: `experiments/artifacts/a4/m46/{m46.log,m46_bicycle.json,m46_stump.json,m46_bonsai.json}`.

## Cost

15 min of A100-PCIE-40GB ≈ ¥0.7.
