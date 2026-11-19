# Gap to the published frontier, computed from measured points

Our rows are the Pareto front of the shipping container (see `OURS` in `tools/gap_report.py` for the
round each point comes from); published rows are the transcribed paper numbers. Interpolation is linear
between adjacent measured points and is refused outside our measured range. The M16 protocol bias
(0.55 dB, our renders read low) is stated, not folded in.

| scene | method | their MB | their PSNR | our PSNR @their MB | gap (dB) | gap, bias-corrected | our MB @their PSNR | rate ratio |
|---|---|---|---|---|---|---|---|---|
| bicycle | 3DGS | 1336.45 | 25.11 | 24.48* | **+0.63** | +0.08 | unreachable | n/a |
| bicycle | HAC | 27.54 | 25.05 | 23.03 | **+2.02** | +1.47 | unreachable | n/a |
| bicycle | PCGS | 19.09 | 25.12 | 22.40 | **+2.72** | +2.17 | unreachable | n/a |
| stump | 3DGS | 1070.92 | 26.66 | 26.09* | **+0.57** | +0.02 | unreachable | n/a |
| stump | HAC | 18.11 | 26.58 | 24.30* | **+2.28** | +1.73 | unreachable | n/a |
| stump | PCGS | 13.49 | 26.61 | no row | n/a | n/a | unreachable | n/a |

* interpolated across a segment wider than 1.5x in file size - indicative, not a
measurement. The measured rows bracketing it are listed in `OURS`.

## Reading

* **bicycle**: our curve tops out at **24.52 dB / 1447.10 MB** (uncompressed published model (M16)). Every published method on this scene is above that PSNR, so the rate at matched quality is *undefined*, not large: they reach a quality we never reach at any size.
* **stump**: our curve tops out at **26.15 dB / 1170.98 MB** (uncompressed published model (M16)). Every published method on this scene is above that PSNR, so the rate at matched quality is *undefined*, not large: they reach a quality we never reach at any size.

At matched bytes the gap is +2.0 to +2.7 dB raw, +1.5 to +2.2 dB after the protocol bias. The `unreachable` column is literal on the raw scale; correcting the bias does not create a row either, it just moves the 
statement to `our uncompressed model (1447.1 MB / 24.52 dB, i.e. 25.07 corrected) is the published quality, 
at 76x the bytes`. Both forms belong in the paper; neither is an interpolation.
