# J3 — ablation and cost ladder (all rows provenance-checked)

## Container ladder (bicycle, 6,131,954 primitives, 25 held-out views)

| stage | what it changes | file | B/prim | PSNR | ratio |
|---|---|---|---|---|---|
| A0 shelf | 45 coefficients, 3 bit each, per primitive | 144.55 MB | 23.57 | 24.33 | 10.01x |
| A1 shared rank-16 basis | one rank-16 basis per asset, 48 bit | 98.53 MB | 16.07 | 24.12 | 14.69x |
| A2 rank 32 | rank 32 at 64 bit (control that loses) | 108.40 MB | 17.68 | 23.71 | 13.35x |
| A3 smallest-three quaternions | 26 bit instead of 32 | 93.57 MB | 15.26 | 24.12 | 15.47x |
| A4 container repairs | one scale level, 8-bit quats, bit-identical model | 89.72 MB | 14.64 | 24.12 | 16.13x |
| A5 6-bit scales and opacity | first visible step below 8 bits | 85.71 MB | 13.98 | 24.09 | 16.88x |
| A6 shipped near-lossless | gp8-6-6_c9_sh3, 9-bit positions | 83.41 MB | 13.60 | 24.08 | 17.35x |

## Geometry bit widths at mid rate (m50, one model)

| spec | what it turns | bytes | PSNR | SSIM |
|---|---|---|---|---|
| `gp6-6-6_c8` | control | 20,561,912 | 22.87 | 0.6999 |
| `gp4-6-6_c8` | quaternions 6 -> 4 | 19,228,871 | 22.58 | 0.6839 |
| `gp6-4-6_c8` | scales 6 -> 4 | 19,011,806 | 21.96 | 0.6675 |
| `gp6-6-4_c8` | opacity 6 -> 4 | 20,073,993 | 22.88 | 0.6955 |
| `gp6-6-6_c7` | positions 8 -> 7 | 19,990,939 | 22.76 | 0.6884 |
| `gp6-6-6_c6` | positions 8 -> 6 | 19,410,087 | 22.43 | 0.6563 |
| `gp4-4-4_c8` | three fields coarsened | 17,190,847 | 21.65 | 0.6440 |
| `gp4-4-4_c6` | three fields + 6-bit opacity | 16,039,022 | 21.36 | 0.6079 |

## Colour budget at mid rate (m49)

| colour bits | file | PSNR |
|---|---|---|
| 96 | 30.78 MB | 23.04 |
| 64 | 22.91 MB | 23.01 |
| 48 | 20.56 MB | 22.87 |
| 40 | 19.47 MB | 22.63 |
| 32 | 18.35 MB | 21.94 |

## Decode cost (m51)

| scene | spec | file | PSNR | SSIM | decode (s) | decode peak (GB) |
|---|---|---|---|---|---|---|
| bicycle | `gp6-6-6_c8` | 76,598,203 B | 24.06 | 0.7393 | 15.95 | 4.27 |
| bicycle | `gp6-6-4_c8` | 74,802,867 B | 23.95 | 0.7330 | 15.76 | 4.27 |
| stump | `gp6-6-6_c8` | 62,649,653 B | 25.52 | 0.7432 | 12.85 | 3.49 |
| stump | `gp6-6-4_c8` | 61,191,922 B | 25.41 | 0.7368 | 12.72 | 3.49 |
| bonsai | `gp6-6-6_c8` | 15,297,685 B | 27.08 | 0.8868 | 3.25 | 0.95 |
| bonsai | `gp6-6-4_c8` | 14,927,795 B | 26.97 | 0.8824 | 3.22 | 0.95 |

## Encode/decode stages (m22)

| stage | seconds |
|---|---|
| encode r=16 / 48 bit (one SVD + allocation + container) | 51.5 |
| decode r=16 / 48 bit | 9.16 |
| decode + PLY write | 15.9 |
| render, 25 held-out views | 10.6 |
