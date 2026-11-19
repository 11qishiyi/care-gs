# M7 — cluster-relative positions vs the scene-wide grid

matched-byte window ±15%, rate axis: measured (n_measured=144)

| criterion | verdict | evidence |
|---|---|---|
| H1 local coding wins | FAIL | median of per-asset medians +0.28 pp (need ≥ +2.0); positive on 8/8 (need 6) |
| H2 frontier ≥12x | FAIL | 0/8 assets (need 6) |

| H3 dominance (E1 replay) | FAIL | passing 2/8 rate points ['9.0', '12.0']; measured at ['9.0', '12.0'] |

**outcome: `local_coding_negative_dominance_untested`**

## H1 — per asset

| asset | cluster pts | grid pts | pairs | median Δ (pp) | best pair Δ (pp) |
|---|---|---|---|---|---|
| bicycle | 9 | 3 | 7 | +0.43 | +0.43 |
| bicycle_i7k | 9 | 3 | 7 | +0.12 | +0.12 |
| flowers | 9 | 3 | 7 | +0.57 | +0.57 |
| flowers_i7k | 9 | 3 | 7 | +0.14 | +0.14 |
| stump | 9 | 3 | 7 | +1.19 | +1.29 |
| stump_i7k | 9 | 3 | 7 | +0.53 | +0.55 |
| treehill | 9 | 3 | 7 | +0.09 | +0.12 |
| treehill_i7k | 9 | 3 | 7 | +0.04 | +0.05 |

## H2 — qualified near-lossless members

| asset | member | rate | drop (pp) | dPSNR (dB) |
|---|---|---|---|---|
| bicycle | — | — | — | — |
| bicycle_i7k | — | — | — | — |
| flowers | — | — | — | — |
| flowers_i7k | — | — | — | — |
| stump | — | — | — | — |
| stump_i7k | — | — | — | — |
| treehill | — | — | — | — |
| treehill_i7k | — | — | — | — |
