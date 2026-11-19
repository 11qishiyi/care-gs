# M43 + M44 — the encoder's peak memory, taken in the order it was actually stored in

**Rounds 26–27, node 2141496 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 05:05–06:05.** Both rounds ask the same question
M42 left open — *hold the encoder under 6 GB* — and both answers are the same shape: the peak was never where the last
round said it was. M43 narrowed the code arrays and freed dead candidates and the peak did not move; M44 found the copy
that did move it, and the 6 GB target is still 3.6 GB away because what is left is the model, not a temporary.

## What was measured

One host, one session, one process per encode, three variants of the same code path:

* `legacy` — pre-M42: whole-array quantiser and whole-array bit planes.
* `m42` — sliced, but the code array is `int64` and the packer widens the whole array; three layout candidates alive.
* `m43` — `uint8`/`uint16` codes, packer slices before widening, one candidate kept.
* `m44` — plus the Morton permutation gathered inside the quantiser's loop instead of materialised.

| scene | variant | build | peak RSS | total | md5 (12) |
|---|---|---|---|---|---|
| bicycle | legacy | 189.6 s | 18.38 GB | 208.4 s | `151dd603497c` |
| bicycle | m42 | 135.8 s | 11.66 GB | 152.2 s | `151dd603497c` |
| bicycle | m43 | 126.9 s | 11.65 GB | 143.2 s | `151dd603497c` |
| bicycle | **m44** | **108.9 s** | **9.60 GB** | **125.2 s** | `151dd603497c` |
| stump | legacy | 139.7 s | 14.94 GB | 152.9 s | `2a9ad2c1ccae` |
| stump | m42 | 156.3 s | 9.52 GB | 172.0 s | `2a9ad2c1ccae` |
| stump | m43 | 89.9 s | 9.49 GB | 102.9 s | `2a9ad2c1ccae` |
| stump | **m44** | **82.6 s** | **7.83 GB** | **95.9 s** | `2a9ad2c1ccae` |
| bonsai | legacy | 21.5 s | 4.07 GB | 24.9 s | `cae84e9421e4` |
| bonsai | m42 | 19.9 s | 2.92 GB | 23.2 s | `cae84e9421e4` |
| bonsai | m43 | 18.8 s | 2.70 GB | 22.1 s | `cae84e9421e4` |
| bonsai | **m44** | **19.0 s** | **2.27 GB** | **22.4 s** | `cae84e9421e4` |

The container bytes and the md5 are identical for all four variants on all three scenes, which is the point: five
successive rewrites of the encoder's memory behaviour and not one bit of the file changed.

## M43 — `narrowing_is_not_enough`

The narrowed codes are eight times smaller (276 MB against 2.21 GB on bicycle) and the three-candidate window closed
before the basis fit. Peak: **11.66 → 11.65 GB**, i.e. nothing. Build did improve (bicycle 0.934×, stump 0.575×,
bonsai 0.945×), so the change was not useless — it just was not where the memory was.

The stage probe from the same build says why:

```
load_model          cur 1760 MB   peak  4263 MB    n=6,131,954
attribute_arrays    cur 4522 MB   peak  4756 MB    rest=2.21 GB float64
morton_order        cur 4593 MB   peak  4944 MB
encode_layout[bits] cur 4785 MB   peak 11758 MB    <- 7.0 GB live only inside _encode
encode_layout[bytes]cur 5149 MB   peak 11932 MB
alphabet_choice     cur 5150 MB   peak 11932 MB
rest_matrix         cur 6202 MB   peak 11932 MB    1.10 GB
basis_fit           cur 6613 MB   peak 11932 MB    basis=(16,45)
write_container     cur 7236 MB   peak 11932 MB    -> after_free 5226 MB
```

`current` never exceeds 7.2 GB. The peak is a temporary inside `_encode`, and after M43 removed the code array from
that list, what remained was the float64 SH block plus its Morton-ordered copy.

## M44 — `the_peak_had_moved`

`codes_published_sh_parts` now takes `perm` and gathers `flat[perm[i:i+chunk]]` per slice; `_encode` no longer calls
`take(block)` on the quantised SH path. One temporary less, 2.2 GB on bicycle, and the file is unchanged because the
gathered rows are the same rows in the same order — `experiments/tests/test_m44_gather.py` pins that against
`block[perm]` at four bit widths, with a chunk that does not divide the row count, and asserts the input array is not
modified.

Peak **11.65 → 9.60 GB** on bicycle (−17.6 %), 9.49 → 7.83 GB on stump, 2.70 → 2.27 GB on bonsai. Build also fell
again (126.9 → 108.9 s): gathering 6.13 M rows in 1 M-row slices is cheaper than copying 2.2 GB and then reading it.

Criterion M1 asked for ≤ 9.6 GB and measured 9.60 GB, so it is met at the boundary and should be read that way — the
prediction was 9.45 GB, the temporary turned out to be ~2.05 GB rather than 2.21 GB, and a target of 9.4 GB would have
failed. M2 (build ≤ 1.00× of M43) passes at 0.858×, M3 (same md5) passes on all three scenes, M4 (suite) passes at
145 tests.

## What is left, measured rather than guessed

The encoder is now 9.60 GB on bicycle with a *live* footprint of 7.2 GB, and the live part is the model:

| resident | size | removable? |
|---|---|---|
| float64 attribute arrays (means, scales, quats, opacities, SH dc + rest) | 4.5 GB | only by changing the fit |
| int64 position codes + per-cluster header | 0.5 GB | yes, same trick as M43, worth ~0.4 GB |
| three layout candidate stream sets | 0.5 GB | already removed in M43 |
| `load_model` reading the 1.52 GB PLY | 4.3 GB peak | only with a streaming PLY reader |

The SH rest block is 2.21 GB of that 4.5 and it is float64 for one reason: `m22_basis.fit` runs `svd_lowrank` on it,
and the basis it returns is what determines the file. Narrowing the attributes to float32 would change the fit's
rounding and therefore the container — so the 6 GB target cannot be reached by memory work alone. It needs either a
float64 fit that streams (compute `xc = rest - mean` in slices and feed `svd_lowrank` a chunked operator) or a decision
that the encoder's byte-identical contract is worth more than 3.6 GB. That is a question for the next round, and it
should be asked before it is implemented.

## Reproduction

```bash
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
for V in legacy m42 m43; do python3 -m tools.m43_ab --ply /mnt/m35cache/bicycle.ply --variant $V --jobs 4; done
bash experiments/run_m44.sh                       # the current code, three scenes
python3 -m tools.m43_table --dir /workspace/res/m43
python3 -m tools.m42_mem --ply /mnt/m35cache/bicycle.ply   # stage probe
```

Artifacts: `experiments/artifacts/a4/m43/{ab.log,ab_m44.log,enc_*.json,probe.log,mem43.json,run.log}`.

## Cost

1.0 h of A100-PCIE-40GB ≈ ¥2.8, of which ~14 min is the twelve encodes, ~6 min the stage probe, and the rest the
bundle pushes and two `pip install` rounds (`pytest` is not in this image).
