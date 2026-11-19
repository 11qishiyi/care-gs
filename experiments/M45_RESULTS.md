# M45 — the alphabet search built the geometry three times

**Round 28, node 2141499 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 06:00–06:20.** The build encodes the model once per SH
layout to choose the smallest colour alphabet. The geometry streams are identical in all three layouts and are 64 % of
the container, so two of the three geometry passes were waste. They are gone; the file is unchanged; the search phase
is 25 % cheaper, which is **less than the 34 % the arithmetic promised** — and the reason is the interesting part.

## Change

`m4_bytes._encode(..., parts=("geo", "sh"))` restricts the work to one half, and `m24_alpha.build` now encodes the
geometry once plus the colour streams per layout, then merges the winner's colour streams with that single geometry set.
`{k: v for k, v in whole.items()} == geo_only ∪ sh_only` and the two halves are disjoint — pinned by
`experiments/tests/test_m45_parts.py` at three layouts, including that the geometry is byte-identical under all three.

## Measured (one host, one session, one process per scene)

| scene | n | old phase (3 full encodes) | geometry once | colour ×3 | new phase | ratio | geo == sh == old? | build | peak | container |
|---|---|---|---|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 35.1 s | 8.9 s | 17.4 s | 26.3 s | **0.750** | yes | 78.3 s | 9.18 GB | 76,598,203 B |
| stump | 4,961,797 | 28.0 s | 7.2 s | 14.0 s | 21.2 s | **0.755** | yes | 62.8 s | 7.48 GB | 62,649,653 B |
| bonsai | 1,244,819 | 5.9 s | 1.3 s | 3.4 s | 4.6 s | **0.782** | yes | 14.3 s | 2.18 GB | 15,297,685 B |

`per_prim` is 58.5938 B for both paths on all three scenes, and the md5s are the shipped ones
(`151dd603…`, `2a9ad2c1…`, `cae84e94…`), so the stream bytes and the model's own arithmetic are untouched.

## Criterion

**M1 asked for ≤ 0.70× and measured 0.750× — missed.** M2 (same streams, same md5) passes on all three scenes. M3
(peak does not grow) passes: 9.18 GB against M44's 9.60 GB, which is itself a small win — one fewer concurrent
geometry stream set. M4 passes at 150 tests and 881 byte cases.

The miss is not noise, it is arithmetic that does not factor:

```
one full encode          11.7 s   (35.1 / 3)
geometry half             8.9 s
colour half               5.8 s
geometry + colour        14.7 s   > 11.7 s by 3.0 s
```

The two halves **share about 20 % of their work**: both walk the same Morton-permuted arrays, and the second walk finds
them in cache. Splitting the function means walking them twice from the start. So the best possible ratio for this
refactor is `(G + 3S) / (3G + 3S)` with `G + S = 1.25 × F`, which is 0.75 — exactly what was measured. The prediction
of 0.66 assumed `G + S = F`, which the probe on the same machine contradicts.

## What this round actually bought

End to end on this host: load 12.1 s + build 78.3 s + write 2.2 s = 92.6 s for a 76.6 MB container (bicycle). M44
measured 108.9 s for the same build on a different node and the same session structure, so the honest same-host claim
is the phase ratio: **the alphabet search is 25 % cheaper and produces the same bytes**, and the encoder's peak fell
0.4 GB on the way. Compared with the pre-M42 encoder (189.6 s build, 18.38 GB peak), the current one is 2.4× faster on
build and 50 % smaller in peak, with a bit-identical container throughout.

## The other thing this round proves

The three geometry encodes were not just wasted time, they were the only reason the phase could be parallelised in a
future round: after M45 the search is one geometry pass plus three colour passes, and the three colour passes are
independent. A thread pool over layouts is now the obvious next lever, and it would multiply by ~2 (three passes → one
wall-clock pass) at a peak cost of two extra colour stream sets (~0.7 GB). That is a trade worth pricing, but it is a
different round and it needs its own criterion.

## Reproduction

```bash
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
bash experiments/run_m45.sh          # phase ratios, three scenes
bash experiments/run_m45_peak.sh     # peak RSS + md5 of the split build
```

Artifacts: `experiments/artifacts/a4/m45/{m45.log,m45_peak.log,m45_bicycle.json,m45_stump.json,m45_bonsai.json,m45_peak_*.json}`.

## Cost

20 min of A100-PCIE-40GB ≈ ¥0.9 (two probes on three scenes, plus bundle pushes).
