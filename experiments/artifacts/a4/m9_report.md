# M9 — view-dependent dictionary (vector-quantised SH)

rate axis: `measured` (measured bytes when available)

| criterion | verdict | detail |
|---|---|---|
| K1 near-lossless >= 12x, >= 6/8 assets | **FAIL** | 2/8 assets have a member |
| K2 VQ beats scalar SH at +-15% bytes | **FAIL** | 5/8 assets >= 1.0 pp |
| K3 codebook is paid for | **PASS** | median share 0.31% of the file |

**outcome: `dead_write_N18`**

## K1 — best qualified member above 12x

| asset | member | rate | coverage loss | dPSNR |
|---|---|---|---|---|
| bicycle | — | — | — | — |
| bicycle_i7k | `vq14_c8_o8` | 19.88x | -0.40 pp | +0.100 dB |
| flowers | — | — | — | — |
| flowers_i7k | — | — | — | — |
| stump | — | — | — | — |
| stump_i7k | `vq14_c8_o8` | 19.82x | -0.80 pp | +0.153 dB |
| treehill | — | — | — | — |
| treehill_i7k | — | — | — | — |

## K2 — dictionary vs per-coefficient at matched bytes

| asset | dictionary | B/prim | loss | per-coefficient | B/prim | loss | diff |
|---|---|---|---|---|---|---|---|
| bicycle | `vq14_c8_o8` | 12.07 | -1.46 | `d1_c8_o6_sh2` | 11.68 | -5.37 | **+3.90** |
| bicycle_i7k | `vq14_c8_o8` | 11.87 | -0.40 | `d1_c8_o6_sh2` | 11.58 | -2.28 | **+1.88** |
| flowers | `vq14_c8_o8` | 12.30 | -1.13 | `d1_c8_o6_sh2` | 11.95 | -3.18 | **+2.06** |
| flowers_i7k | `vq14_c8_o8` | 12.03 | -0.38 | `d1_c8_o6_sh2` | 11.89 | -1.13 | **+0.74** |
| stump | `vq14_c8_o8` | 12.00 | -2.10 | `d1_c8_o6_sh2` | 11.70 | -10.58 | **+8.48** |
| stump_i7k | `vq14_c8_o8` | 11.91 | -0.80 | `d1_c8_o6_sh2` | 11.64 | -6.28 | **+5.48** |
| treehill | `d2_vq12_c8_o8` | 11.98 | +0.09 | `d1_c8_o6_sh2` | 11.92 | -0.94 | **+1.03** |
| treehill_i7k | `vq6_c8_o8` | 10.83 | +0.47 | `d0_c10_o6_sh2` | 10.43 | -0.56 | **+1.03** |

## K3 — codebook ledger

| asset | variant | B/prim | codebook | share of file |
|---|---|---|---|---|
| bicycle | `vq6_c8_o8` | 11.03 | 3072 B | 0.01% |
| bicycle | `vq8_c8_o8` | 11.17 | 12288 B | 0.02% |
| bicycle | `vq10_c8_o8` | 11.53 | 49152 B | 0.08% |
| bicycle | `vq12_c8_o8` | 11.79 | 196608 B | 0.32% |
| bicycle | `vq14_c8_o8` | 12.07 | 786432 B | 1.24% |
| bicycle | `vq10_c10_o8` | 12.42 | 49152 B | 0.08% |
| bicycle | `vq12_c10_o8` | 12.67 | 196608 B | 0.30% |
| bicycle | `vq12_c12_o8` | 13.42 | 196608 B | 0.28% |
| bicycle | `d2_vq12_c8_o8` | 11.78 | 110592 B | 0.18% |
| bicycle | `p30_vq12_c8_o8` | 11.77 | 196608 B | 1.06% |
| bicycle_i7k | `vq6_c8_o8` | 10.81 | 3072 B | 0.01% |
| bicycle_i7k | `vq8_c8_o8` | 10.97 | 12288 B | 0.04% |
| bicycle_i7k | `vq10_c8_o8` | 11.32 | 49152 B | 0.14% |
| bicycle_i7k | `vq12_c8_o8` | 11.58 | 196608 B | 0.55% |
| bicycle_i7k | `vq14_c8_o8` | 11.87 | 786432 B | 2.13% |
| bicycle_i7k | `vq10_c10_o8` | 12.17 | 49152 B | 0.13% |
| bicycle_i7k | `vq12_c10_o8` | 12.43 | 196608 B | 0.51% |
| bicycle_i7k | `vq12_c12_o8` | 13.18 | 196608 B | 0.48% |
| bicycle_i7k | `d2_vq12_c8_o8` | 11.58 | 110592 B | 0.31% |
| bicycle_i7k | `p30_vq12_c8_o8` | 11.73 | 196608 B | 1.80% |
| flowers | `vq6_c8_o8` | 11.20 | 3072 B | 0.01% |
| flowers | `vq8_c8_o8` | 11.37 | 12288 B | 0.03% |
| flowers | `vq10_c8_o8` | 11.72 | 49152 B | 0.13% |
| flowers | `vq12_c8_o8` | 11.98 | 196608 B | 0.52% |
| flowers | `vq14_c8_o8` | 12.30 | 786432 B | 2.05% |
| flowers | `vq10_c10_o8` | 12.51 | 49152 B | 0.13% |
| flowers | `vq12_c10_o8` | 12.78 | 196608 B | 0.49% |
| flowers | `vq12_c12_o8` | 13.53 | 196608 B | 0.46% |
| flowers | `d2_vq12_c8_o8` | 11.97 | 110592 B | 0.30% |
| flowers | `p30_vq12_c8_o8` | 11.97 | 196608 B | 1.75% |
| flowers_i7k | `vq6_c8_o8` | 10.94 | 3072 B | 0.01% |
| flowers_i7k | `vq8_c8_o8` | 11.12 | 12288 B | 0.05% |
| flowers_i7k | `vq10_c8_o8` | 11.45 | 49152 B | 0.20% |
| flowers_i7k | `vq12_c8_o8` | 11.71 | 196608 B | 0.77% |
| flowers_i7k | `vq14_c8_o8` | 12.03 | 786432 B | 2.99% |
| flowers_i7k | `vq10_c10_o8` | 12.23 | 49152 B | 0.18% |
| flowers_i7k | `vq12_c10_o8` | 12.50 | 196608 B | 0.72% |
| flowers_i7k | `vq12_c12_o8` | 13.25 | 196608 B | 0.68% |
| flowers_i7k | `d2_vq12_c8_o8` | 11.71 | 110592 B | 0.43% |
| flowers_i7k | `p30_vq12_c8_o8` | 11.87 | 196608 B | 2.53% |
| stump | `vq6_c8_o8` | 10.94 | 3072 B | 0.01% |
| stump | `vq8_c8_o8` | 11.09 | 12288 B | 0.03% |
| stump | `vq10_c8_o8` | 11.45 | 49152 B | 0.10% |
| stump | `vq12_c8_o8` | 11.71 | 196608 B | 0.39% |
| stump | `vq14_c8_o8` | 12.00 | 786432 B | 1.53% |
| stump | `vq10_c10_o8` | 12.36 | 49152 B | 0.09% |
| stump | `vq12_c10_o8` | 12.62 | 196608 B | 0.36% |
| stump | `vq12_c12_o8` | 13.36 | 196608 B | 0.34% |
| stump | `d2_vq12_c8_o8` | 11.70 | 110592 B | 0.22% |
| stump | `p30_vq12_c8_o8` | 11.77 | 196608 B | 1.30% |
| stump_i7k | `vq6_c8_o8` | 10.84 | 3072 B | 0.01% |
| stump_i7k | `vq8_c8_o8` | 11.01 | 12288 B | 0.03% |
| stump_i7k | `vq10_c8_o8` | 11.35 | 49152 B | 0.13% |
| stump_i7k | `vq12_c8_o8` | 11.61 | 196608 B | 0.51% |
| stump_i7k | `vq14_c8_o8` | 11.91 | 786432 B | 2.01% |
| stump_i7k | `vq10_c10_o8` | 12.24 | 49152 B | 0.12% |
| stump_i7k | `vq12_c10_o8` | 12.49 | 196608 B | 0.48% |
| stump_i7k | `vq12_c12_o8` | 13.24 | 196608 B | 0.45% |
| stump_i7k | `d2_vq12_c8_o8` | 11.61 | 110592 B | 0.29% |
| stump_i7k | `p30_vq12_c8_o8` | 11.74 | 196608 B | 1.70% |
| treehill | `vq6_c8_o8` | 11.22 | 3072 B | 0.01% |
| treehill | `vq8_c8_o8` | 11.37 | 12288 B | 0.03% |
| treehill | `vq10_c8_o8` | 11.73 | 49152 B | 0.12% |
| treehill | `vq12_c8_o8` | 11.99 | 196608 B | 0.49% |
| treehill | `vq14_c8_o8` | 12.29 | 786432 B | 1.90% |
| treehill | `vq10_c10_o8` | 12.54 | 49152 B | 0.12% |
| treehill | `vq12_c10_o8` | 12.80 | 196608 B | 0.46% |
| treehill | `vq12_c12_o8` | 13.55 | 196608 B | 0.43% |
| treehill | `d2_vq12_c8_o8` | 11.98 | 110592 B | 0.27% |
| treehill | `p30_vq12_c8_o8` | 11.95 | 196608 B | 1.63% |
| treehill_i7k | `vq6_c8_o8` | 10.83 | 3072 B | 0.01% |
| treehill_i7k | `vq8_c8_o8` | 11.00 | 12288 B | 0.05% |
| treehill_i7k | `vq10_c8_o8` | 11.34 | 49152 B | 0.21% |
| treehill_i7k | `vq12_c8_o8` | 11.60 | 196608 B | 0.82% |
| treehill_i7k | `vq14_c8_o8` | 11.93 | 786432 B | 3.18% |
| treehill_i7k | `vq10_c10_o8` | 12.14 | 49152 B | 0.20% |
| treehill_i7k | `vq12_c10_o8` | 12.40 | 196608 B | 0.76% |
| treehill_i7k | `vq12_c12_o8` | 13.15 | 196608 B | 0.72% |
| treehill_i7k | `d2_vq12_c8_o8` | 11.60 | 110592 B | 0.46% |
| treehill_i7k | `p30_vq12_c8_o8` | 11.78 | 196608 B | 2.68% |
