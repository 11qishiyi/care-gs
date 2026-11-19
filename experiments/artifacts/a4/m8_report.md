# M8 — band truncation at the high-rate corner

rate axis: measured (n_measured=120)

| criterion | verdict | evidence |
|---|---|---|
| J1 near-lossless ≥12× | FAIL | 2/8 assets (need 6) |
| J2 band vs all-band (15–25 B) | FAIL | winner `equivalent`, median Δ +0.08 pp, 4/8 positive (need +1.0 on 6) |

**outcome: `dead_write_N17`**

## J1 — qualified near-lossless members

| asset | member | rate | drop (pp) | dPSNR (dB) |
|---|---|---|---|---|
| bicycle | — | — | — | — |
| bicycle_i7k | `d2_c10_o8_sh3` | 12.50× | -0.48 | +0.101 |
| flowers | — | — | — | — |
| flowers_i7k | — | — | — | — |
| stump | — | — | — | — |
| stump_i7k | `d2_c10_o8_sh3` | 12.41× | -0.69 | +0.094 |
| treehill | — | — | — | — |
| treehill_i7k | — | — | — | — |

## J2 — per asset

| asset | band pick | Δ vs all-band (pp) | all-band pick |
|---|---|---|---|
| bicycle | `d2_c8_o8_sh4` 10.64× (-1.80 pp) | -1.48 | `c8_o8_sh3` 9.63× (-0.31 pp) |
| bicycle_i7k | `d2_c8_o8_sh4` 11.10× (-0.42 pp) | -0.31 | `c10_o8_sh3` 9.66× (-0.11 pp) |
| flowers | `d2_c10_o8_sh3` 11.60× (-0.45 pp) | +1.07 | `c12_o8_sh2` 12.61× (-1.52 pp) |
| flowers_i7k | `d2_c8_o8_sh4` 10.56× (-0.16 pp) | +0.50 | `c12_o8_sh2` 12.67× (-0.66 pp) |
| stump | `d2_c8_o8_sh4` 10.61× (-1.45 pp) | -0.92 | `c8_o8_sh3` 9.62× (-0.53 pp) |
| stump_i7k | `d2_c8_o8_sh4` 11.07× (-0.55 pp) | -0.32 | `c10_o8_sh3` 9.63× (-0.23 pp) |
| treehill | `d2_c8_o8_sh4` 10.52× (+0.30 pp) | +1.02 | `c12_o8_sh2` 12.60× (-0.73 pp) |
| treehill_i7k | `d1_c12_o8_sh4` 13.42× (+0.35 pp) | +0.47 | `c10_o8_sh3` 9.52× (-0.12 pp) |
