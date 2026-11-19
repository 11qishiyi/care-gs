# M15: packed geometry (st3 quaternions + 5/4 bit groups + c6 positions)

source: `experiments/artifacts/a4/m15_rd.json`

**outcome** `dead_write_N24`

| criterion | verdict | detail |
|---|---|---|
| R1_packing_is_free | FAIL | gp8-5-4_c6 vs clean: 1/8; gp8-5-4_c6_sh3 vs c8_o8_sh3: 1/8; gp8-5-4_c6_sh3 vs c10_o8_sh3: 1/8 (need 6) |
| R2_floor_moves_past_10.8x | FAIL | top of tier 0/1 assets >= 10.8x (median 9.00x; cheapest member median 9.00x) |
| R3_12x_probe | FAIL | 0/8 assets (need 6) |

## R1 same-SH-width pairs (packed vs unpacked)

### `gp8-5-4_c6 vs clean` -- 1/8 pass, need 6

| asset | packed rate | drop | unpacked rate | drop | gap pp | gap dB | ok |
|---|---|---|---|---|---|---|---|
| bicycle | 1.36x | -2.28 | 1.00x | +0.00 | -2.28 | +0.293 | NO |
| bicycle_i7k | 1.38x | -0.72 | 1.00x | +0.00 | -0.72 | +0.242 | NO |
| flowers | 1.34x | -1.73 | 1.00x | +0.00 | -1.73 | +0.172 | NO |
| flowers_i7k | 1.35x | -0.80 | 1.00x | +0.00 | -0.80 | +0.183 | NO |
| stump | 1.30x | -2.92 | 1.00x | +0.00 | -2.92 | +0.419 | NO |
| stump_i7k | 1.31x | -1.47 | 1.00x | +0.00 | -1.47 | +0.342 | NO |
| treehill | 1.38x | -0.78 | 1.00x | +0.00 | -0.78 | -0.163 | NO |
| treehill_i7k | 1.40x | -0.44 | 1.00x | +0.00 | -0.44 | +0.027 | yes |

### `gp8-5-4_c6_sh3 vs c8_o8_sh3` -- 1/8 pass, need 6

| asset | packed rate | drop | unpacked rate | drop | gap pp | gap dB | ok |
|---|---|---|---|---|---|---|---|
| bicycle | 10.87x | -2.53 | 9.63x | -0.31 | -2.22 | +0.235 | NO |
| bicycle_i7k | 11.33x | -0.82 | 10.01x | -0.15 | -0.67 | +0.219 | NO |
| flowers | 10.45x | -1.88 | 9.28x | -0.26 | -1.62 | +0.169 | NO |
| flowers_i7k | 10.59x | -0.90 | 9.42x | -0.15 | -0.75 | +0.166 | NO |
| stump | 10.86x | -3.41 | 9.62x | -0.53 | -2.88 | +0.383 | NO |
| stump_i7k | 11.32x | -1.70 | 9.99x | -0.28 | -1.42 | +0.303 | NO |
| treehill | 10.63x | -0.93 | 9.43x | -0.16 | -0.76 | -0.159 | NO |
| treehill_i7k | 11.11x | -0.57 | 9.84x | -0.14 | -0.43 | +0.018 | yes |

### `gp8-5-4_c6_sh3 vs c10_o8_sh3` -- 1/8 pass, need 6

| asset | packed rate | drop | unpacked rate | drop | gap pp | gap dB | ok |
|---|---|---|---|---|---|---|---|
| bicycle | 10.87x | -2.53 | 9.29x | -0.24 | -2.29 | +0.246 | NO |
| bicycle_i7k | 11.33x | -0.82 | 9.66x | -0.11 | -0.71 | +0.230 | NO |
| flowers | 10.45x | -1.88 | 9.00x | -0.16 | -1.72 | +0.170 | NO |
| flowers_i7k | 10.59x | -0.90 | 9.13x | -0.11 | -0.79 | +0.174 | NO |
| stump | 10.86x | -3.41 | 9.28x | -0.42 | -2.99 | +0.405 | NO |
| stump_i7k | 11.32x | -1.70 | 9.63x | -0.23 | -1.47 | +0.318 | NO |
| treehill | 10.63x | -0.93 | 9.14x | -0.13 | -0.80 | -0.151 | NO |
| treehill_i7k | 11.11x | -0.57 | 9.52x | -0.12 | -0.44 | +0.018 | yes |

## R2 the packed near-lossless tier

top = the most expensive packed SH-quantised row inside 0.5 pp (the frontier's
extent, which is what the verdict uses); cheapest = the least expensive such
row (the literal "cheapest rate" reading, decided by the grid rather than the
data).

| asset | top variant | rate | drop pp | dPSNR | ok | cheapest | rate |
|---|---|---|---|---|---|---|---|
| bicycle | - | - | - | - | no candidate | - | - |
| bicycle_i7k | - | - | - | - | no candidate | - | - |
| flowers | - | - | - | - | no candidate | - | - |
| flowers_i7k | - | - | - | - | no candidate | - | - |
| stump | - | - | - | - | no candidate | - | - |
| stump_i7k | - | - | - | - | no candidate | - | - |
| treehill | - | - | - | - | no candidate | - | - |
| treehill_i7k | `gp8-5-4_c6_sh4` | 9.00x | -0.46 | +0.028 | NO | `gp8-5-4_c6_sh4` | 9.00x |

## R3 members at >= 12x

| asset | variant | rate | drop pp | dPSNR |
|---|---|---|---|---|

