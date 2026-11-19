# J4 results — the shipped quantile, measured against rate

## bicycle (q = 0.0891, 25 held-out views)

| configuration | MB | rate | PSNR | pixel cov | view cov | gap (pp) | audit (pp) |
|---|---|---|---|---|---|---|---|
| `clean` | 1447.14 | 1.0 | 24.65 | 0.910 | 0.722 | +18.77 | 3.86 |
| `gp6-6-6_c8_sh6` | 285.71 | 5.07 | 24.58 | 0.908 | 0.722 | +18.56 | 3.90 |
| `gp6-6-6_c8_sh4` | 212.13 | 6.82 | 24.56 | 0.908 | 0.722 | +18.53 | 3.89 |
| `gp6-6-6_c8_sh3` | 175.34 | 8.25 | 24.47 | 0.906 | 0.682 | +22.34 | 3.94 |
| `gp6-6-6_c8_sh2` | 138.54 | 10.45 | 23.54 | 0.874 | 0.521 | +35.34 | 4.55 |
| `gp4-6-6_c8_sh3` | 170.74 | 8.48 | 24.12 | 0.898 | 0.682 | +21.60 | 3.91 |
| `gp6-4-6_c8_sh3` | 170.74 | 8.48 | 23.54 | 0.880 | 0.478 | +40.27 | 4.28 |
| `gp6-6-4_c8_sh3` | 173.80 | 8.33 | 24.36 | 0.902 | 0.682 | +22.02 | 3.89 |
| `gp6-6-6_c7_sh3` | 173.04 | 8.36 | 24.40 | 0.904 | 0.682 | +22.16 | 3.94 |

- **C1: PASS** — {"coverage": [0.91, 0.9076, 0.9057, 0.8742], "rates": [1.0, 6.82, 8.25, 10.45], "read": "ascending rate: coverage must never increase"}
- **C2: FAIL** — {"fields_worse": 2, "detail": [{"geometry": "gp4-6-6_c8_sh3", "rate": 8.48, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 1.17, "ref_loss_pp": 0.43, "ratio": 2.72}, {"geometry": "gp6-4-6_c8_sh3", "rate": 8.48, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 2.97, "ref_loss_pp": 0.43, "ratio": 6.91}, {"geometry": "gp6-6-4_c8_sh3", "rate": 8.33, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 0.75, "ref_loss_pp": 0.43, "ratio": 1.74}, {"geometry": "gp6-6-6_c7_sh3", "rate": 8.36, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 0.61, "ref_loss_pp": 0.43, "ratio": 1.42}]}
- **C3: PASS** — {"gaps_desc_rate": [35.34, 21.6, 40.27, 22.16, 22.02, 22.34, 18.53, 18.56]}
- **C4: FAIL** — {"worst_pp": 4.55, "per_row": {"clean": 3.86, "gp6-6-6_c8_sh6": 3.9, "gp6-6-6_c8_sh4": 3.89, "gp6-6-6_c8_sh3": 3.94, "gp6-6-6_c8_sh2": 4.55, "gp4-6-6_c8_sh3": 3.91, "gp6-4-6_c8_sh3": 4.28, "gp6-6-4_c8_sh3": 3.89, "gp6-6-6_c7_sh3": 3.94}}

## stump (q = 0.0738, 16 held-out views)

| configuration | MB | rate | PSNR | pixel cov | view cov | gap (pp) | audit (pp) |
|---|---|---|---|---|---|---|---|
| `clean` | 1170.98 | 1.0 | 26.38 | 0.911 | 0.741 | +17.00 | 3.00 |
| `gp6-6-6_c8_sh6` | 231.19 | 5.07 | 26.31 | 0.909 | 0.741 | +16.83 | 2.98 |
| `gp6-6-6_c8_sh4` | 171.65 | 6.82 | 26.29 | 0.909 | 0.741 | +16.78 | 2.97 |
| `gp6-6-6_c8_sh3` | 141.88 | 8.25 | 26.18 | 0.906 | 0.741 | +16.48 | 2.95 |
| `gp6-6-6_c8_sh2` | 112.11 | 10.45 | 23.88 | 0.788 | 0.000 | +78.77 | 2.86 |
| `gp4-6-6_c8_sh3` | 138.16 | 8.48 | 26.11 | 0.904 | 0.741 | +16.28 | 2.96 |
| `gp6-4-6_c8_sh3` | 138.16 | 8.48 | 25.43 | 0.881 | 0.431 | +44.95 | 3.22 |
| `gp6-6-4_c8_sh3` | 140.64 | 8.33 | 26.06 | 0.903 | 0.741 | +16.13 | 2.96 |
| `gp6-6-6_c7_sh3` | 140.02 | 8.36 | 26.08 | 0.903 | 0.741 | +16.21 | 2.96 |

- **C1: PASS** — {"coverage": [0.9113, 0.9091, 0.9061, 0.7877], "rates": [1.0, 6.82, 8.25, 10.45], "read": "ascending rate: coverage must never increase"}
- **C2: FAIL** — {"fields_worse": 1, "detail": [{"geometry": "gp4-6-6_c8_sh3", "rate": 8.48, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 0.73, "ref_loss_pp": 0.52, "ratio": 1.4}, {"geometry": "gp6-4-6_c8_sh3", "rate": 8.48, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 3.06, "ref_loss_pp": 0.52, "ratio": 5.88}, {"geometry": "gp6-6-4_c8_sh3", "rate": 8.33, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 0.87, "ref_loss_pp": 0.52, "ratio": 1.67}, {"geometry": "gp6-6-6_c7_sh3", "rate": 8.36, "ref": "gp6-6-6_c8_sh3", "ref_rate": 8.25, "geo_loss_pp": 0.79, "ref_loss_pp": 0.52, "ratio": 1.52}]}
- **C3: PASS** — {"gaps_desc_rate": [78.77, 16.28, 44.95, 16.21, 16.13, 16.48, 16.78, 16.83]}
- **C4: FAIL** — {"worst_pp": 3.22, "per_row": {"clean": 3.0, "gp6-6-6_c8_sh6": 2.98, "gp6-6-6_c8_sh4": 2.97, "gp6-6-6_c8_sh3": 2.95, "gp6-6-6_c8_sh2": 2.86, "gp4-6-6_c8_sh3": 2.96, "gp6-4-6_c8_sh3": 3.22, "gp6-6-4_c8_sh3": 2.96, "gp6-6-6_c7_sh3": 2.96}}

