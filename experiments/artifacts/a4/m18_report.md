# M18: 30 k finetune steps at the two published budgets (bicycle)

Base model: 24.52 dB

| configuration | primitives | clean dB | vs base | ft gain | best <= 27.54 MB | best <= 19.09 MB |
|---|---|---|---|---|---|---|
| `k25s30_ft` | 1,532,988 | 21.97 | -2.55 | -- | `vq12_c8_o8` 18.40 MB / 21.50 dB | `vq12_c8_o8` 18.40 MB / 21.50 dB |
| `k35s30_ft` | 2,146,184 | 22.54 | -1.98 | -- | `vq12_c8_o8` 25.67 MB / 22.08 dB | *none* |
| `base` | 0 | 24.52 | +0.00 | -- | *none* | *none* |

## C5: best row at or below 27.54 MB must reach 24.50 dB

Best: `vq12_c8_o8` on `bicycle_k35s30_ft` -- 25.67 MB / 22.08 dB (-2.42 dB against the bar, -2.97 dB against HAC's own row).

**Verdict: `representation_bound_confirmed`**
