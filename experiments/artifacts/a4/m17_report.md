# M17 pilot: our frontier at HAC's operating point (bicycle)

Base model: 24.52 dB

| configuration | primitives | clean dB | vs base | ft gain | best <= 27.54 MB | best <= 19.09 MB |
|---|---|---|---|---|---|---|
| `base` | 6,131,954 | 24.52 | +0.00 | -- | *none* | *none* |
| `k50_pre` | 3,065,977 | 19.78 | -4.75 | -- | *none* | *none* |
| `k35_pre` | 2,146,184 | 16.88 | -7.65 | -- | `vq12_c8_o8` 25.64 MB / 16.93 dB | *none* |
| `k50l3_pre` | 3,065,977 | 19.78 | -4.75 | -- | *none* | *none* |
| `k50l3_ft` | 3,065,977 | 22.67 | -1.85 | +2.89 | *none* | *none* |
| `k35l3_pre` | 2,146,184 | 16.88 | -7.65 | -- | `vq12_c8_o8` 25.64 MB / 16.93 dB | *none* |
| `k35l3_ft` | 2,146,184 | 21.81 | -2.71 | +4.93 | `vq12_c8_o8` 25.67 MB / 21.51 dB | *none* |

## C5: best row at or below 27.54 MB must reach 24.50 dB

Best: `vq12_c8_o8` on `bicycle_k35l3_ft` -- 25.67 MB / 21.51 dB (-2.99 dB against the bar, -3.54 dB against HAC's own row).

**Verdict: `representation_bound_confirmed`**
