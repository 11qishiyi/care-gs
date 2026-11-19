# J1 — rate–reliability frontier and the coverage-aware planner (CPU, from the M5 grid)

Usable assets: **bicycle, bicycle_i7k, flowers, flowers_i7k, stump, stump_i7k**. Excluded: **treehill, treehill_i7k** (rule: no variant improves coverage (any positive drop => protocol artefact)).

## E1 — largest rate within a coverage tolerance

| eps (pp) | asset | planner pick | rate | drop (pp) | PSNR | SSIM | LPIPS | best prune | best prune rate |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | bicycle | m18_o6_sh3 | 9.01 | -0.43 | 21.98 | 0.7512 | 0.2022 | — | 0.00 |
| 0.5 | bicycle_i7k | m16_o6_sh3 | 9.93 | -0.29 | 21.99 | 0.6337 | 0.3689 | — | 0.00 |
| 0.5 | flowers | m18_o6_sh3 | 8.72 | -0.30 | 16.59 | 0.6065 | 0.3451 | — | 0.00 |
| 0.5 | flowers_i7k | d1_m16_o8_sh4 | 12.97 | -0.45 | 18.84 | 0.5005 | 0.4882 | — | 0.00 |
| 0.5 | stump | — | 0.00 | +0.00 | 0.00 | 0.0000 | 0.0000 | — | 0.00 |
| 0.5 | stump_i7k | m18_o6_sh3 | 9.25 | -0.35 | 24.18 | 0.7006 | 0.2970 | — | 0.00 |
| 1.0 | bicycle | m16_o6_sh3 | 9.68 | -0.83 | 21.90 | 0.7431 | 0.2060 | — | 0.00 |
| 1.0 | bicycle_i7k | d1_m16_o8_sh4 | 13.27 | -0.95 | 22.08 | 0.6266 | 0.3674 | — | 0.00 |
| 1.0 | flowers | d2_m16_o8_sh4 | 9.64 | -0.89 | 17.45 | 0.5851 | 0.3535 | — | 0.00 |
| 1.0 | flowers_i7k | d0_m16_o8_sh8 | 15.78 | -0.74 | 18.92 | 0.4908 | 0.4928 | — | 0.00 |
| 1.0 | stump | m18_o6_sh3 | 8.97 | -0.72 | 23.62 | 0.7537 | 0.1889 | — | 0.00 |
| 1.0 | stump_i7k | m16_o6_sh3 | 9.90 | -0.85 | 24.05 | 0.6901 | 0.3007 | — | 0.00 |
| 2.0 | bicycle | m16_o6_sh3 | 9.68 | -0.83 | 21.90 | 0.7431 | 0.2060 | p90 | 1.27 |
| 2.0 | bicycle_i7k | d0_m16_o8_sh8 | 15.93 | -1.33 | 22.01 | 0.6202 | 0.3702 | p90 | 1.29 |
| 2.0 | flowers | d1_m16_o8_sh8 | 9.95 | -1.99 | 17.90 | 0.5601 | 0.3688 | — | 0.00 |
| 2.0 | flowers_i7k | d0_m16_o8_sh8 | 15.78 | -0.74 | 18.92 | 0.4908 | 0.4928 | p90 | 1.26 |
| 2.0 | stump | m16_o6_sh3 | 9.60 | -1.84 | 23.41 | 0.7335 | 0.1964 | p90 | 1.22 |
| 2.0 | stump_i7k | d1_m16_o8_sh4 | 13.19 | -1.84 | 24.26 | 0.6812 | 0.2942 | p90 | 1.23 |
| 5.0 | bicycle | m16_o6_sh2 | 14.16 | -2.64 | 21.15 | 0.7130 | 0.2465 | p70 | 1.63 |
| 5.0 | bicycle_i7k | d0_m16_o8_sh8 | 15.93 | -1.33 | 22.01 | 0.6202 | 0.3702 | p50 | 2.32 |
| 5.0 | flowers | d0_m16_o8_sh8 | 15.65 | -4.04 | 17.98 | 0.5279 | 0.3892 | p90 | 1.25 |
| 5.0 | flowers_i7k | d0_m16_o8_sh8 | 15.78 | -0.74 | 18.92 | 0.4908 | 0.4928 | p70 | 1.62 |
| 5.0 | stump | d1_m16_o8_sh4 | 12.94 | -4.32 | 24.05 | 0.7163 | 0.2032 | p70 | 1.57 |
| 5.0 | stump_i7k | d0_m16_o8_sh8 | 15.72 | -2.80 | 24.07 | 0.6723 | 0.2983 | p50 | 2.22 |

## E2 — matched-rate collision (eps = 1 pp)

| asset | rate | planner | planner drop | fidelity-first | its drop | prune-first | its drop |
|---|---|---|---|---|---|---|---|
| bicycle | 9.68 | m16_o6_sh3 | -0.83 | d2_m16_o8_sh8 | -2.12 | p20 | -20.43 |
| bicycle_i7k | 13.27 | d1_m16_o8_sh4 | -0.95 | d2_m16_o8_sh8 | -0.49 | p10 | -15.09 |
| flowers | 9.64 | d2_m16_o8_sh4 | -0.89 | d2_m16_o8_sh8 | -0.86 | p20 | -23.20 |
| flowers_i7k | 15.78 | d0_m16_o8_sh8 | -0.74 | d0_m16_o8_sh8 | -0.74 | p10 | -19.35 |
| stump | 8.97 | m18_o6_sh3 | -0.72 | d2_m16_o8_sh8 | -2.47 | p20 | -20.79 |
| stump_i7k | 9.90 | m16_o6_sh3 | -0.85 | d2_m16_o8_sh8 | -0.99 | p20 | -12.74 |

## E2b — planners under a leave-one-asset-out coverage prior


**eps = 1.0 pp**

| planner | mean rate / oracle | violations | mean excess when violating (pp) |
|---|---|---|---|
| oracle | 1.0 | 0/6 | 0.0 |
| carp | 0.911 | 3/6 | 0.89 |
| maxrate | 2.1 | 6/6 | 35.82 |
| safe8 | 0.384 | 1/6 | 0.18 |
| prune_safe | None | 0/0 | 0.0 |

| asset | oracle rate | carp rate | carp drop | maxrate drop | safe8 drop | prune-safe drop |
|---|---|---|---|---|---|---|
| bicycle | 9.68 | 9.93 | -2.14 | -48.99 | -0.43 | — |
| bicycle_i7k | 13.27 | 9.93 | -0.29 | -23.75 | -0.12 | — |
| flowers | 9.64 | 9.36 | -0.83 | -41.21 | -0.58 | — |
| flowers_i7k | 15.78 | 9.41 | -0.29 | -25.47 | -0.14 | — |
| stump | 8.97 | 9.82 | -2.51 | -49.95 | -1.18 | — |
| stump_i7k | 9.90 | 10.19 | -1.02 | -31.58 | -0.53 | — |

**eps = 2.0 pp**

| planner | mean rate / oracle | violations | mean excess when violating (pp) |
|---|---|---|---|
| oracle | 1.0 | 0/6 | 0.0 |
| carp | 1.006 | 3/6 | 1.43 |
| maxrate | 1.918 | 6/6 | 34.82 |
| safe8 | 0.351 | 0/6 | 0.0 |
| prune_safe | 0.106 | 1/6 | 0.68 |

| asset | oracle rate | carp rate | carp drop | maxrate drop | safe8 drop | prune-safe drop |
|---|---|---|---|---|---|---|
| bicycle | 9.68 | 13.09 | -3.96 | -48.99 | -0.43 | -1.15 |
| bicycle_i7k | 15.93 | 10.24 | -0.50 | -23.75 | -0.12 | -1.62 |
| flowers | 9.95 | 12.77 | -2.01 | -41.21 | -0.58 | -2.68 |
| flowers_i7k | 15.78 | 10.04 | -0.43 | -25.47 | -0.14 | -1.27 |
| stump | 9.60 | 12.94 | -4.32 | -49.95 | -1.18 | -1.62 |
| stump_i7k | 13.19 | 10.19 | -1.02 | -31.58 | -0.53 | -1.30 |

**eps = 5.0 pp**

| planner | mean rate / oracle | violations | mean excess when violating (pp) |
|---|---|---|---|
| oracle | 1.0 | 0/6 | 0.0 |
| carp | 1.057 | 2/6 | 1.23 |
| maxrate | 1.512 | 6/6 | 31.82 |
| safe8 | 0.276 | 0/6 | 0.0 |
| prune_safe | 0.108 | 1/6 | 2.81 |

| asset | oracle rate | carp rate | carp drop | maxrate drop | safe8 drop | prune-safe drop |
|---|---|---|---|---|---|---|
| bicycle | 14.16 | 15.91 | -5.57 | -48.99 | -0.43 | -3.69 |
| bicycle_i7k | 15.93 | 15.93 | -1.33 | -23.75 | -0.12 | -2.70 |
| flowers | 15.65 | 15.65 | -4.04 | -41.21 | -0.58 | -7.81 |
| flowers_i7k | 15.78 | 15.78 | -0.74 | -25.47 | -0.14 | -3.83 |
| stump | 12.94 | 15.73 | -6.90 | -49.95 | -1.18 | -4.35 |
| stump_i7k | 15.72 | 15.72 | -2.80 | -31.58 | -0.53 | -2.92 |

## E3 — how many coverage points is a decibel?

| asset | pairs | pp per dB (median) | min | max |
|---|---|---|---|---|
| bicycle | 12 | 3.86 | 1.68 | 35.27 |
| bicycle_i7k | 9 | 2.01 | 1.13 | 11.26 |
| flowers | 8 | 3.02 | 1.61 | 9.9 |
| flowers_i7k | 5 | 0.91 | 0.81 | 1.27 |
| stump | 9 | 3.77 | 2.59 | 37.9 |
| stump_i7k | 12 | 3.5 | 1.46 | 16.16 |

Across assets: **[0.91, 3.86] pp/dB, spread 4.2x**.
