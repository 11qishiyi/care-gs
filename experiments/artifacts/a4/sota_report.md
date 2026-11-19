# S1 — our ladder versus the published-format baselines, at the baselines' own bytes

Verdict **S1 = False** — 0/8 assets beat every baseline by at least 1.0 points at the baseline's own measured budget (need 6); delta median +6.67 pp, range -1.17 … +20.76 pp.

| asset | baseline | base rate | base loss | our variant | our rate | our loss | delta |
|---|---|---|---|---|---|---|---|
| bicycle | SH 8-bit | 2.80× | +0.00 | `sh12_g16` | 2.67× | -0.43 | **-0.43** |
| bicycle | SH 4-bit | 3.99× | -0.02 | `m16_o8_sh8` | 4.18× | -0.43 | **-0.40** |
| bicycle | prune 50% + SH 8-bit | 5.59× | -7.05 | `msc12-6-a1_c8_o8` | 5.27× | -0.07 | **+6.98** |
| bicycle | prune 50% + SH 4-bit | 7.94× | -7.08 | `msc12-6-a1_c8_o8` | 5.27× | -0.07 | **+7.01** |
| bicycle | prune 30% + SH 4-bit | 13.21× | -12.82 | `msc12-6-a1_c8_o8` | 5.27× | -0.07 | **+12.75** |
| bicycle | prune 30% + SH 2-bit | 17.00× | -15.88 | `msc12-6-a1_c8_o8` | 5.27× | -0.07 | **+15.81** |
| bicycle_i7k | SH 8-bit | 2.81× | -0.00 | `sh16_g16` | 2.15× | -0.12 | **-0.12** |
| bicycle_i7k | SH 4-bit | 4.08× | -0.01 | `sh16_g16` | 2.15× | -0.12 | **-0.11** |
| bicycle_i7k | prune 50% + SH 8-bit | 5.62× | -4.80 | `msc12-6-a4_c8_o8` | 5.36× | -0.04 | **+4.76** |
| bicycle_i7k | prune 50% + SH 4-bit | 8.09× | -4.82 | `msc12-6-a4_c8_o8` | 5.36× | -0.04 | **+4.77** |
| bicycle_i7k | prune 30% + SH 4-bit | 13.43× | -7.63 | `msc12-6-a4_c8_o8` | 5.36× | -0.04 | **+7.59** |
| bicycle_i7k | prune 30% + SH 2-bit | 17.09× | -9.49 | `msc12-6-a4_c8_o8` | 5.36× | -0.04 | **+9.44** |
| flowers | SH 8-bit | 2.78× | -0.00 | `sh12_g16` | 2.61× | -0.57 | **-0.57** |
| flowers | SH 4-bit | 3.93× | -0.02 | `sh12_g16` | 2.61× | -0.57 | **-0.55** |
| flowers | prune 50% + SH 8-bit | 5.53× | -13.02 | `msc12-6-a1_c8_o8` | 5.14× | -0.12 | **+12.90** |
| flowers | prune 50% + SH 4-bit | 7.82× | -13.04 | `msc12-6-a1_c8_o8` | 5.14× | -0.12 | **+12.92** |
| flowers | prune 30% + SH 4-bit | 13.04× | -19.18 | `msc12-6-a1_c8_o8` | 5.14× | -0.12 | **+19.07** |
| flowers | prune 30% + SH 2-bit | 16.92× | -20.88 | `msc12-6-a1_c8_o8` | 5.14× | -0.12 | **+20.76** |
| flowers_i7k | SH 8-bit | 2.77× | +0.00 | `sh16_g16` | 2.10× | -0.14 | **-0.14** |
| flowers_i7k | SH 4-bit | 3.97× | -0.02 | `sh8_g16` | 3.57× | -0.14 | **-0.11** |
| flowers_i7k | prune 50% + SH 8-bit | 5.54× | -6.72 | `msc12-6-a4_c8_o8` | 5.13× | -0.05 | **+6.67** |
| flowers_i7k | prune 50% + SH 4-bit | 7.86× | -6.72 | `msc12-6-a4_c8_o8` | 5.13× | -0.05 | **+6.67** |
| flowers_i7k | prune 30% + SH 4-bit | 13.05× | -13.65 | `msc12-6-a4_c8_o8` | 5.13× | -0.05 | **+13.60** |
| flowers_i7k | prune 30% + SH 2-bit | 16.87× | -14.80 | `msc12-6-a4_c8_o8` | 5.13× | -0.05 | **+14.75** |
| stump | SH 8-bit | 2.77× | +0.00 | `sh16_g16` | 2.05× | -1.17 | **-1.17** |
| stump | SH 4-bit | 3.97× | -0.05 | `sh8_g16` | 3.57× | -1.17 | **-1.12** |
| stump | prune 50% + SH 8-bit | 5.53× | -8.87 | `msc12-6-a1_c8_o8` | 5.14× | -0.13 | **+8.74** |
| stump | prune 50% + SH 4-bit | 7.91× | -8.90 | `msc12-6-a1_c8_o8` | 5.14× | -0.13 | **+8.77** |
| stump | prune 30% + SH 4-bit | 13.09× | -13.49 | `msc12-6-a1_c8_o8` | 5.14× | -0.13 | **+13.36** |
| stump | prune 30% + SH 2-bit | 16.93× | -20.54 | `msc12-6-a1_c8_o8` | 5.14× | -0.13 | **+20.41** |
| stump_i7k | SH 8-bit | 2.77× | +0.00 | `sh16_g16` | 2.05× | -0.53 | **-0.53** |
| stump_i7k | SH 4-bit | 4.08× | -0.03 | `sh8_g16` | 3.56× | -0.53 | **-0.50** |
| stump_i7k | prune 50% + SH 8-bit | 5.51× | -4.89 | `msc12-6-a4_c8_o8` | 5.21× | -0.07 | **+4.82** |
| stump_i7k | prune 50% + SH 4-bit | 8.06× | -4.91 | `msc12-6-a4_c8_o8` | 5.21× | -0.07 | **+4.85** |
| stump_i7k | prune 30% + SH 4-bit | 13.29× | -9.23 | `msc12-6-a4_c8_o8` | 5.21× | -0.07 | **+9.17** |
| stump_i7k | prune 30% + SH 2-bit | 16.99× | -14.61 | `msc12-6-a4_c8_o8` | 5.21× | -0.07 | **+14.54** |
| treehill | SH 8-bit | 2.81× | -0.00 | `sh16_g16` | 2.14× | -0.09 | **-0.09** |
| treehill | SH 4-bit | 3.96× | -0.03 | `sh16_g16` | 2.14× | -0.09 | **-0.06** |
| treehill | prune 50% + SH 8-bit | 5.57× | -3.59 | `msc12-6-a1_c8_o8` | 5.22× | -0.05 | **+3.55** |
| treehill | prune 50% + SH 4-bit | 7.86× | -3.62 | `d2_m16_o8_sh8` | 6.29× | +0.27 | **+3.89** |
| treehill | prune 30% + SH 4-bit | 13.07× | -8.51 | `d2_m16_o8_sh8` | 6.29× | +0.27 | **+8.78** |
| treehill | prune 30% + SH 2-bit | 16.86× | -10.35 | `d2_m16_o8_sh8` | 6.29× | +0.27 | **+10.62** |
| treehill_i7k | SH 8-bit | 2.83× | +0.00 | `sh16_g16` | 2.16× | -0.04 | **-0.04** |
| treehill_i7k | SH 4-bit | 4.05× | -0.02 | `sh8_g16` | 3.66× | -0.04 | **-0.02** |
| treehill_i7k | prune 50% + SH 8-bit | 5.63× | -2.90 | `msc12-6-a1_c8_o8` | 5.30× | -0.02 | **+2.87** |
| treehill_i7k | prune 50% + SH 4-bit | 8.01× | -2.92 | `d2_m16_o8_sh8` | 6.40× | +0.24 | **+3.16** |
| treehill_i7k | prune 30% + SH 4-bit | 13.29× | -7.15 | `d1_m16_o8_sh8` | 10.29× | +0.33 | **+7.48** |
| treehill_i7k | prune 30% + SH 2-bit | 16.99× | -8.99 | `d0_m16_o8_sh8` | 16.10× | +0.36 | **+9.35** |

Losses are coverage points against the clean asset (negative = lost). Delta = ours − baseline, positive when we lose less.
