# M10 - two-stage dictionary (residual VQ)

| criterion | verdict | detail |
|---|---|---|
| L1 near-lossless >= 12x, >= 6/8 assets | **FAIL** | 2/8 assets have a member |
| L2 residual stage beats single stage at +-10% bytes (>= 0.3 pp) | **FAIL** | 5/8 assets, median +0.42 pp |
| L3 envelope owns 15-25x (>= 1.0 pp) | **FAIL** | 0/8 assets, median +0.22 pp |

**outcome: `dead_write_N19`**

## L1 - per asset

| asset | best two-stage point | rate | drop pp | dPSNR | member |
|---|---|---|---|---|---|
| bicycle | `rvq12-4_c8_o8` | 19.25x | -1.47 | +0.085 | no |
| bicycle_i7k | `rvq10-6_c8_o8` | 19.57x | -0.55 | +0.054 | yes |
| flowers | `rvq10-6_c8_o8` | 18.96x | -1.20 | -0.586 | no |
| flowers_i7k | `rvq10-6_c8_o8` | 19.36x | -0.31 | -0.322 | no |
| stump | `rvq12-4_c8_o8` | 19.39x | -2.37 | +0.029 | no |
| stump_i7k | `rvq10-6_c8_o8` | 19.50x | -0.89 | +0.072 | yes |
| treehill | `rvq10-6_c8_o8` | 18.93x | -0.24 | -1.289 | no |
| treehill_i7k | `rvq8-2_c8_o8` | 21.00x | +0.44 | -1.877 | no |

## L2 - two-stage vs single-stage at matched bytes

| asset | two-stage | single | rate | drop two-stage | drop single | diff pp |
|---|---|---|---|---|---|---|
| bicycle | `rvq12-4_c8_o8` | `vq10_c8_o8` | 19.25x | -1.47 | -2.55 | +1.09 |
| bicycle_i7k | `rvq10-6_c8_o8` | `vq10_c8_o8` | 19.57x | -0.55 | -0.90 | +0.35 |
| flowers | `rvq10-6_c8_o8` | `vq10_c8_o8` | 18.96x | -1.20 | -1.86 | +0.67 |
| flowers_i7k | `rvq10-6_c8_o8` | `vq12_c8_o8` | 19.36x | -0.31 | -0.44 | +0.14 |
| stump | `rvq12-4_c8_o8` | `vq10_c8_o8` | 19.39x | -2.37 | -3.68 | +1.32 |
| stump_i7k | `rvq10-6_c8_o8` | `vq10_c8_o8` | 19.50x | -0.89 | -1.38 | +0.48 |
| treehill | `rvq10-6_c8_o8` | `vq12_c8_o8` | 18.93x | -0.24 | -0.43 | +0.20 |
| treehill_i7k | `rvq8-2_c8_o8` | `vq12_c8_o8` | 21.00x | +0.44 | +0.17 | +0.26 |

## L3 - envelope over the target band

| asset | two-stage best | rate | drop | other best | rate | drop | diff pp |
|---|---|---|---|---|---|---|---|
| bicycle | `rvq12-4_c8_o8` | 19.25x | -1.47 | `vq12_c8_o8` | 20.02x | -1.89 | +0.42 |
| bicycle_i7k | `rvq10-6_c8_o8` | 19.57x | -0.55 | `vq12_c8_o8` | 20.38x | -0.70 | +0.14 |
| flowers | `rvq10-6_c8_o8` | 18.96x | -1.20 | `vq12_c8_o8` | 19.70x | -1.44 | +0.24 |
| flowers_i7k | `rvq10-6_c8_o8` | 19.36x | -0.31 | `vq10_c8_o8` | 20.62x | -0.43 | +0.13 |
| stump | `rvq12-4_c8_o8` | 19.39x | -2.37 | `vq12_c8_o8` | 20.16x | -2.66 | +0.30 |
| stump_i7k | `rvq10-6_c8_o8` | 19.50x | -0.89 | `vq12_c8_o8` | 20.33x | -1.08 | +0.19 |
| treehill | `rvq10-6_c8_o8` | 18.93x | -0.24 | `vq10_c8_o8` | 20.12x | -0.35 | +0.11 |
| treehill_i7k | `rvq8-2_c8_o8` | 21.00x | +0.44 | `vq10_c8_o8` | 20.81x | +0.18 | +0.26 |
