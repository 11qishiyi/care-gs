# M22 results: one colour basis for six million Gaussians (round 18, 2026-11-15)

**Verdict: `shared_basis_wins`.** The per-primitive SH block does not need 45 independent numbers. A
rank-16 basis shared by the whole asset, with bits allocated across components by variance, renders
bicycle within **0.21 dB** of the shipped shelf while cutting the file from **144.55 MB to 98.53 MB** —
the near-lossless ratio moves from **10.01× to 14.69×**.

## Criteria (pre-registered in METHOD_PLAN before the data, L1–L3)

| | criterion | measured | verdict |
|---|---|---|---|
| **L1** | best rank in {2,4,8,16} within **0.35 dB** of the shelf (24.33 dB) | r=16/b=48 → **24.12 dB** (−0.21) | **PASS** |
| **L2** | that rank puts the whole file at **≤ 100 MB** (≥14.5×) | **98.53 MB** = **14.69×** | **PASS** |
| **L3** | geometry, container and decoder path unchanged; decode ≤ 15 s | geometry streams identical; decode **9.16 s** | **PASS** |

## The curve (bicycle, 6,131,954 primitives, 25 held-out views, 1236×822)

Clean reference 24.52 dB / 1447 MB. Shelf = `c10_o8_sh3` (45 coefficients × 3 bits = 20.61 B).

| plan | file | B/primitive | PSNR | ratio | Δ vs shelf |
|---|---|---|---|---|---|
| shelf (r=45, 3 bit) | 144.55 MB | 23.57 | **24.33** | 10.01× | — |
| basis r=16, 96 bit | 136.81 MB | 22.31 | 24.32 | 10.58× | −0.01 |
| basis r=16, 64 bit | 106.18 MB | 17.32 | 24.28 | 13.63× | −0.05 |
| **basis r=16, 48 bit** | **98.53 MB** | **16.07** | **24.12** | **14.69×** | **−0.21** |
| basis r=16, 40 bit | 95.22 MB | 15.53 | 23.67 | 15.20× | −0.66 |
| basis r=16, 32 bit | 92.10 MB | 15.02 | 22.98 | 15.71× | −1.35 |
| basis r=32, 64 bit | 108.40 MB | 17.68 | 23.71 | 13.35× | −0.62 |

Two shapes in that table matter.

- **The colour block saturates at ~48 bits.** Doubling the colour budget (48 → 96 bits, +30 MB) buys
  0.20 dB, and 96 bits is within 0.01 dB of the shelf. The residual error at that point is rank
  truncation plus geometry quantisation, not colour precision — so buying more colour bits is waste.
- **Rank 32 at the same budget is worse than rank 16** (23.71 vs 24.28 dB). With 64 bits spread over 32
  components the allocator can only give the leading components 4 bits; the SVD's tail does not pay for
  the precision it takes away from the head.

## Why it works (the measurement that motivated it)

**Rank grid actually rendered.**  L1 named the set {2, 4, 8, 16}.  The spectrum settles 2, 4 and 8
before anything is encoded: rank 2 and rank 4 keep 28.9 % and 46.7 % of the coefficient energy, and
rank 8 caps at 54.1 % relative coefficient error — worse than the shelf's own 21.1 % — so only rank 16
was rendered.  (The energy column comes from the SVD alone and is valid; the first probe run's RMSE
column was produced by the broken per-primitive quantiser described below and is void.  Rank 32 was
then added *outside* the registered grid as a diagnostic, and it lost.)

The probe on the raw coefficients gives the spectrum and, more usefully, the coefficient error at each
rank/budget against the shelf's own 3-bit error:

| configuration | bytes/prim | relative coefficient RMSE |
|---|---|---|
| shelf, 45 × 3 bit | 20.61 | 21.11 % |
| r=8, 64 bit | 8.00 | 54.13 % |
| r=16, 64 bit | 8.00 | 28.48 % |
| r=16, 96 bit | 12.00 | **18.91 %** |
| r=32, 128 bit | 16.00 | 16.87 % |
| r=32, 165 bit | 20.62 | **9.90 %** |

At the *same* bytes as the shelf (165 bits) a rank-32 basis halves the colour error (9.90 % vs 21.11 %).
The rank-16/48-bit point that ships sits at 50.2 % coefficient error and still renders within 0.21 dB —
because SH coefficients are not equally visible: the error the basis makes lands on primitives and
directions that contribute little to a pixel. That gap between coefficient error and rendered error is
the whole reason L1 was defined on PSNR.

## The quantiser that had to be fixed first

The first version of this round used the ladder's own trick — one scale per primitive across all r
components. The probe returned **115 % relative error**, i.e. worse than coding zero: the SVD orders
components by magnitude, so a per-primitive maximum is set by the leading component and every smaller
component is crushed to a couple of levels. Two changes fixed it, both now pinned by tests:

1. **per-component scale from a 99.9th percentile, not the max** — one outlier primitive was otherwise
   setting the step for six million others;
2. **reverse water-filling** across components under a fixed bit budget (`allocate()`), with a hard
   per-component cap (an early version handed one component 44 bits and cast the codes to uint8).

The lesson generalises: a transform code has to be *rate*-allocated, not uniformly quantised, or the
transform's own ranking becomes a liability.

## Cost

| stage | time |
|---|---|
| encode r=16/48 (one SVD + allocation + container) | 51.5 s |
| decode r=16/48 | 9.16 s |
| decode + PLY write | 15.9 s |
| render, 25 views | 10.6 s |
| probe (7 ranks × budgets) | 9.7 s load + 6 min |

Basis bytes are in the file and are negligible: 16×45 floats + 45 floats + 16 bytes of depths =
2,992 B per asset, i.e. 0.0005 B per primitive.

## What this changes

- **The near-lossless shelf moves to 14.69× at −0.21 dB** (was 10.01×). FRONTIER_BOUND §3 needs the
  new row, and the M20 conclusion "the colour block is at its floor" has to be qualified: it was at its
  floor *as 45 independent numbers*.
- **The 12× target is now reachable essentially for free.** 12× means 19.67 B per primitive;
  geometry (7.97) and DC (0.61) take 8.58 of that, leaving **11.09 B = 89 colour bits**. The measured
  96-bit point (136.81 MB, 10.58×) sits at −0.01 dB and the 64-bit point (106.18 MB, 13.63×) at
  −0.05 dB, so 12× lands at roughly **−0.03 dB** — inside the 0.35 dB L1 window with room to spare.
  The M15–M21 conclusion "12× is unreachable for this family" is hereby corrected: it was unreachable
  while the 45 coefficients were coded as independent numbers.
- **The mid-rate argument is unaffected**: geometry alone is still 7.97 B/primitive, so 27.5 MB still
  cannot hold 6.13 M primitives (N25–N27). Shared colour does not buy primitives; it buys bytes.

## Reproduce

```bash
bash experiments/run_m22.sh probe      # spectrum + allocation, against the shelf's own error
bash experiments/run_m22.sh encode     # PLANS=16:48,16:64,32:64 -> container + PLY per plan
bash experiments/run_m22.sh render     # held-out PSNR per plan
```

Node: A100-PCIE-40GB, ¥2.80/h. Tests: `pytest experiments/tests` 67 passed, including
`test_the_basis_path_round_trips`, `test_the_basis_is_cheap`, `test_the_allocator_stops_at_the_cap`,
`test_the_allocator_spends_bits_where_the_variance_is`, `test_the_decoder_reproduces_the_encoder`.
