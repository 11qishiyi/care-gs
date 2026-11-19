# M22: one colour basis for six million Gaussians

Measured file sizes (`zstd -12` + Morton, container path) and PSNR on the held-out views.
The shelf row is the 45-independently-coded-coefficients variant the basis replaces;
`bits` is the colour block's budget per primitive, i.e. the number the round turns.

## bicycle

| plan | colour bits | file | B/primitive | PSNR | ratio | vs shelf |
|---|---|---|---|---|---|---|
| r=16 | 96 | 136.81 MB | 22.31 | 24.32 | 10.58x | -0.01 dB |
| r=16 | 64 | 106.18 MB | 17.32 | 24.28 | 13.63x | -0.05 dB |
| r=32 | 64 | 108.40 MB | 17.68 | 23.71 | 13.35x | -0.62 dB |
| r=16 | 48 | 98.53 MB | 16.07 | 24.12 | 14.69x | -0.21 dB |
| r=16 | 40 | 95.22 MB | 15.53 | 23.67 | 15.20x | -0.66 dB |
| r=16 | 32 | 92.10 MB | 15.02 | 22.98 | 15.71x | -1.35 dB |
| shelf `c10_o8_sh3` (45 x 3 bit) | 165 | 144.55 MB | 23.57 | 24.33 | 10.01x | -- |

Pre-registered L1 window (within 0.35 dB of the shelf): best point **r=16, 48 bits -> 98.53 MB, 14.69x, -0.21 dB**.

## stump

| plan | colour bits | file | B/primitive | PSNR | ratio | vs shelf |
|---|---|---|---|---|---|---|
| r=16 | 64 | 86.84 MB | 17.50 | 25.73 | 13.49x | -0.08 dB |
| r=16 | 48 | 80.72 MB | 16.27 | 25.57 | 14.51x | -0.24 dB |
| shelf `c10_o8_sh3` (45 x 3 bit) | 165 | 118.88 MB | 24.42 | 25.81 | 9.85x | -- |

Pre-registered L1 window (within 0.35 dB of the shelf): best point **r=16, 48 bits -> 80.72 MB, 14.51x, -0.24 dB**.
