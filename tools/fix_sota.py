import io

p = "experiments/artifacts/a4/sota_table.md"
s = io.open(p, encoding="utf-8").read()

old_tail = """| this work (M27, scale/rotation/opacity per primitive, 5-bit offsets) | 69.19 MB | 11.28 | 21.58 | only colour shared |

The anchor bookkeeping is 3.8x cheaper per primitive than our own shelf (2.52 vs 13.60 B/prim) and
renders 4.3 dB below pruning at equal bytes: constant sharing is not the mechanism that wins this row.
The measured attribution is position quantum 1.72 dB, constant scale 2.46 dB, constant opacity 0.29 dB,
constant rotation 0.09 dB, shared rest colour ~2 dB at equal bytes (M27, N34).  The next candidate is
the one this round did not build: per-anchor feature plus an offset-conditioned predictor."""

new_tail = """| this work (M27, scale/rotation/opacity per primitive, 5-bit offsets) | 69.19 MB | 11.28 | 21.58 | only colour shared |
| this work (M28, anchors + offset-conditioned predictor, DC 4) | 27.13 MB | 4.42 | 17.04 | +0.08 dB over constant |
| this work (M28, anchors + offset-conditioned predictor, DC 6) | 33.57 MB | 5.47 | 17.05 | +0.08 dB over constant |

The anchor bookkeeping is 3.8x cheaper per primitive than our own shelf (2.52 vs 13.60 B/prim) and
renders 4.3 dB below pruning at equal bytes: constant sharing is not the mechanism that wins this row.
The measured attribution is position quantum 1.72 dB, constant scale 2.46 dB, constant opacity 0.29 dB,
constant rotation 0.09 dB, shared rest colour ~2 dB at equal bytes (M27, N34).  The predictor M27
pointed at was built in M28 and bought **+0.08 dB** at the same grid: the anchor mean explains only
R² = 0.63 / 0.38 / 0.60 of scale / opacity / rotation variance at 8 primitives per voxel, so the rest
is not in any input the decoder has (M28, N35).  Three post-hoc explanations of the mid-rate gap are
now priced and excluded -- supervision (N33), anchor representation (N34), predictor (N35) -- and what
remains is a jointly trained decoder with learned latents, which this pipeline does not have."""

assert old_tail in s
io.open(p, "w", encoding="utf-8").write(s.replace(old_tail, new_tail))
print("sota table updated")
