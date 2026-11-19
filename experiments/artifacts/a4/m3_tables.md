outcome `m3_dominance_only` over 8 assets

### E1 — dominance at matched bytes

| asset | 5× (QFP / prune / Δ) | 7× (QFP / prune / Δ) | 9× (QFP / prune / Δ) | 12× (QFP / prune / Δ) |
|---|---|---|---|---|
| bicycle | -1.25 / -20.43 / **+19.17** | -0.61 / -26.53 / **+25.91** | -2.79 / -32.63 / **+29.83** | -5.17 / -38.34 / **+33.17** |
| bicycle_i7k | -0.30 / -9.62 / **+9.32** | -0.22 / -11.81 / **+11.59** | -1.53 / -13.99 / **+12.46** | -1.24 / -16.82 / **+15.58** |
| flowers | -0.72 / -23.20 / **+22.48** | -0.63 / -26.80 / **+26.17** | -2.17 / -30.40 / **+28.23** | -3.54 / -34.00 / **+30.46** |
| flowers_i7k | -0.18 / -15.32 / **+15.14** | -0.22 / -16.94 / **+16.71** | -0.79 / -18.55 / **+17.75** | -0.67 / -20.57 / **+19.91** |
| stump | -1.81 / -20.79 / **+18.98** | -1.41 / -26.95 / **+25.54** | -7.56 / -33.12 / **+25.56** | -6.26 / -38.95 / **+32.69** |
| stump_i7k | -0.76 / -12.74 / **+11.98** | -0.67 / -15.93 / **+15.26** | -4.53 / -19.12 / **+14.59** | -2.56 / -22.89 / **+20.33** |
| treehill | +0.08 / -12.87 / **+12.96** | -0.22 / -15.72 / **+15.50** | -0.83 / -18.56 / **+17.73** | -0.78 / -21.33 / **+20.55** |
| treehill_i7k | +0.09 / -9.02 / **+9.12** | -0.16 / -10.68 / **+10.52** | -0.82 / -12.33 / **+11.51** | +0.35 / -14.15 / **+14.49** |

pooled mean Δ by rate: 5.0× +14.89 pp (min +9.12, 8/8 assets), 7.0× +18.40 pp (min +10.52, 8/8 assets), 9.0× +19.71 pp (min +11.51, 8/8 assets), 12.0× +23.40 pp (min +14.49, 8/8 assets)

### E2 — degree truncation vs. bit truncation

| asset | degree-truncated | bits-truncated | Δ (deg − bits) | winner |
|---|---|---|---|---|
| bicycle | d2_m16_o8_sh8 -2.12 pp | m18_o6_sh3 -0.43 pp | -1.69 pp | bits |
| bicycle_i7k | d2_m16_o8_sh8 -0.49 pp | m16_o8_sh4 -0.14 pp | -0.35 pp | bits |
| flowers | d2_m16_o8_sh8 -0.86 pp | m18_o6_sh3 -0.30 pp | -0.56 pp | bits |
| flowers_i7k | d2_m16_o8_sh8 -0.23 pp | m18_o6_sh3 -0.16 pp | -0.07 pp | bits |
| stump | d2_m16_o8_sh8 -2.47 pp | m18_o6_sh3 -0.72 pp | -1.75 pp | bits |
| stump_i7k | d2_m16_o8_sh8 -0.99 pp | m18_o6_sh3 -0.35 pp | -0.65 pp | bits |
| treehill | d2_m16_o8_sh8 +0.27 pp | m16_o8_sh4 -0.13 pp | +0.40 pp | degree |
| treehill_i7k | d1_m16_o8_sh8 +0.33 pp | m16_o8_sh4 -0.07 pp | +0.40 pp | degree |

winner **bits**, mean Δ -0.534 pp, agreement 6/8, window 25–45 B, verdict **True**

### E3 — near-lossless shelf above 8×

| asset | members ≥8× (≤1.0 pp, ≤0.3 dB) | best near-lossless rate |
|---|---|---|
| bicycle | none | 7.21× |
| bicycle_i7k | d2_m16_o8_sh4 (8.00×, -0.50 pp), d1_m16_o8_sh8 (8.43×, -0.94 pp), d1_m16_o8_sh4 (10.73×, -0.95 pp) | 10.73× |
| flowers | d2_m16_o8_sh4 (8.00×, -0.89 pp) | 8.00× |
| flowers_i7k | d2_m16_o8_sh4 (8.00×, -0.25 pp), d1_m16_o8_sh8 (8.43×, -0.43 pp), d1_m16_o8_sh4 (10.73×, -0.45 pp), d0_m16_o8_sh8 (12.42×, -0.74 pp) | 12.42× |
| stump | none | 7.21× |
| stump_i7k | none | 7.21× |
| treehill | d2_m16_o8_sh4 (8.00×, +0.25 pp), d1_m16_o8_sh8 (8.43×, -0.23 pp), d1_m16_o8_sh4 (10.73×, -0.25 pp), d0_m16_o8_sh8 (12.42×, -0.95 pp) | 12.42× |
| treehill_i7k | d2_m16_o8_sh4 (8.00×, +0.22 pp), d1_m16_o8_sh8 (8.43×, +0.33 pp), d1_m16_o8_sh4 (10.73×, +0.31 pp), d0_m16_o8_sh8 (12.42×, +0.36 pp) | 12.42× |

assets with a member **5/8** (need 6), verdict **False**
