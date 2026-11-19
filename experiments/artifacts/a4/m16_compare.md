# M16 -- our curve on the published axes

reference: `Kerbl et al. 2308.04079, per-scene table as reproduced in HAC (2403.14530) supp. Table G`; protocol {'dataset': 'MipNeRF360', 'images': 'images_4', 'iterations': 30000, 'lpips': 'vgg'}

## C1 protocol (does our clean render reproduce the published 3DGS?)

n/a -- 0/2 scenes within 0.35 dB (need 2), mean |delta| 0.55 dB (need <= 0.25)

| scene | ours | published 3DGS | delta dB | dSSIM | dLPIPS |
|---|---|---|---|---|---|
| bicycle | 24.52 | 25.11 | -0.59 | 0.025 | - |
| bonsai | - | 32.12 | +- | - | - |
| counter | - | 29.07 | +- | - | - |
| flowers | - | 21.36 | +- | - | - |
| garden | - | 27.30 | +- | - | - |
| kitchen | - | 31.47 | +- | - | - |
| room | - | 31.74 | +- | - | - |
| stump | 26.15 | 26.66 | -0.51 | 0.009 | - |
| treehill | - | 22.62 | +- | - | - |

## C2 equal size vs `hac`

n/a -- 0/2 scenes at or above its PSNR within its own size (need 2), mean dPSNR -5.61 dB

| scene | its MB | its PSNR | our variant | our MB | our PSNR | dPSNR | ok |
|---|---|---|---|---|---|---|---|
| bicycle | 27.5 | 25.05 | `vq12_c8_o8` | 14.7 | 20.08 | -4.97 | no |
| bonsai | 8.6 | 32.28 | *no candidate* | - | - | - | no |
| counter | 7.3 | 29.35 | *no candidate* | - | - | - | no |
| flowers | 19.6 | 21.26 | *no candidate* | - | - | - | no |
| garden | 22.7 | 27.28 | *no candidate* | - | - | - | no |
| kitchen | 8.1 | 31.16 | *no candidate* | - | - | - | no |
| room | 5.5 | 31.55 | *no candidate* | - | - | - | no |
| stump | 18.1 | 26.58 | `p30_vq12_c8_o8` | 17.6 | 20.33 | -6.25 | no |
| treehill | 20.0 | 23.30 | *no candidate* | - | - | - | no |

## C2 equal size vs `pcgs`

n/a -- 0/2 scenes at or above its PSNR within its own size (need 2), mean dPSNR -7.51 dB

| scene | its MB | its PSNR | our variant | our MB | our PSNR | dPSNR | ok |
|---|---|---|---|---|---|---|---|
| bicycle | 19.1 | 25.12 | `vq12_c8_o8` | 14.7 | 20.08 | -5.04 | no |
| bonsai | 7.4 | 33.20 | *no candidate* | - | - | - | no |
| counter | 6.8 | 29.75 | *no candidate* | - | - | - | no |
| flowers | 15.7 | 21.33 | *no candidate* | - | - | - | no |
| garden | 18.3 | 27.37 | *no candidate* | - | - | - | no |
| kitchen | 7.7 | 31.55 | *no candidate* | - | - | - | no |
| room | 5.0 | 32.07 | *no candidate* | - | - | - | no |
| stump | 13.5 | 26.61 | `p10_vq12_c8_o8` | 5.9 | 16.63 | -9.98 | no |
| treehill | 16.2 | 23.32 | *no candidate* | - | - | - | no |

## how far down our own range goes

| scene | cheapest variant | MB | PSNR |
|---|---|---|---|
| bicycle | `p10_vq12_c8_o8` | 1.54 | 16.75 |
| stump | `p10_vq12_c8_o8` | 5.89 | 16.63 |
