import io

entry = r'''
## N37. A uniform width is a rate allocation, not a default

**Round 26 · bicycle · 12 containers · 25 held-out views**

The position block of the container codes the offsets inside a 256-primitive cluster on an 8-bit grid
over that cluster's own bounding box.  Every cluster gets the same width, so the money looked obvious:
dense clusters sit in small boxes and need only a few levels, sparse ones sit in big boxes and need more.
`experiments/m30_adapt.py` re-codes the position stream cluster by cluster and writes the width sequence
into a `cluster_bits` stream; two allocation families were measured -- a constant absolute step, and a
budget-neutral tilt toward or away from the dense clusters.

Every one of them lost.

| allocation | file | ratio | PSNR | delta |
|---|---|---|---|---|
| fixed 8 bit | 76.56 MB | 18.90x | **24.06** | -- |
| constant step, same nominal | 77.86 MB | 18.58x | 24.01 | -0.05 |
| constant step, one bit coarser | 75.56 MB | 19.15x | 23.89 | -0.17 |
| constant step, 1.8 bits coarser | 73.37 MB | 19.72x | 23.48 | -0.58 |
| constant step, 2.4 bits coarser | 72.29 MB | 20.02x | 22.90 | -1.16 |
| tilt -0.5 toward dense, equal bytes | 76.76 MB | 18.85x | 23.98 | -0.08 |
| tilt -1.0 toward dense, equal bytes | 76.27 MB | 18.97x | 23.79 | -0.27 |
| tilt +0.5 toward sparse, equal bytes | 76.71 MB | 18.86x | 24.03 | -0.03 |

The reason is a ratio, not an intuition.  Comparing each decoded model with the source and splitting the
error by cluster size:

| cluster extent quartile | 25-324 mm | 324-655 mm | 655-1313 mm | 1313-168651 mm |
|---|---|---|---|---|
| fixed 8 bit, mean error / extent | 0.00134 | 0.00134 | 0.00133 | 0.00130 |
| constant step, one bit coarser | 0.00697 | 0.00299 | 0.00133 | 0.00135 |
| constant step, 1.8 bits coarser | 0.01277 | 0.00517 | 0.00274 | 0.00134 |

A fixed *width* over a *local* box is a rate allocation in which the absolute error is proportional to the
local primitive spacing -- constant relative precision, 0.13 %, at every density.  That is what a renderer
wants, because dense clusters are dense *because* the detail is there.  Equalising the absolute step,
which is what "spend the bits where the geometry needs them" sounds like, takes micrometre precision away
from exactly those clusters: the smallest quartile's mean error goes 0.25 mm to 2.39 mm (9.9x) while the
largest quartile moves 4.58 to 4.70 mm.

What we learned:

* "Uniform" is not the absence of an allocation.  Normalising by the local box *is* an allocation, and a
  good one; the word only hides it when you read the encoder instead of the error.
* The knob that sounds most principled (constant absolute error) is the one that hurts, and it hurts where
  the primitives are -- which is why the loss is 0.6 dB for 4 % of the file rather than a rounding error.
* A budget-neutral tilt is the sharpest way to test an allocation rule: both directions lost, so the fixed
  width sits at the top of the family rather than merely being untested.
* The three bytes per primitive that position costs are the ones the renderer leans on.  After this round
  the position block is no longer the unexamined part of the container -- it is the part with a measured
  optimum, and the paper can say so with two allocations that were tried and rejected.
'''

p = "D:/3dsg_1/APPENDIX_negative_results.md"
s = io.open(p, encoding="utf-8").read()
if "N37." in s:
    print("already there")
else:
    io.open(p, "w", encoding="utf-8").write(s.rstrip() + "\n" + entry + "\n")
    print("N37 appended ->", len(io.open(p, encoding="utf-8").read().splitlines()), "lines")
