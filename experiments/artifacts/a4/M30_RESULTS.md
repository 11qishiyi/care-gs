# M30 — per-cluster position widths: the fixed width was already the allocation

Pre-registered in `tools/m30_spec.md` before any adaptive run.  Node 2140676 (A100-PCIE-40GB, ¥2.80/h),
rented 07:00, released 07:35.

## What was tested

M29 left exactly one lever in the near-lossless container: the *width* of each stream.  The position
offsets inside a 256-primitive cluster are coded at 8 bits per axis on a grid over that cluster's own
bounding box, the same width everywhere — and the boxes are not all the same size, so a per-cluster width
looked like free money.  `experiments/m30_adapt.py` re-codes the position stream cluster by cluster and
writes the width sequence into a `cluster_bits` stream; nothing else in the file changes.

Two families of allocation were measured, both derived from geometry alone (never from a render):

* **constant step** — pick a target metres-per-level and give each cluster `ceil(log2(extent/target))`
  bits, so every cluster ends up with roughly the same *absolute* precision;
* **tilted** — `b_c = 8 + tilt * log2(extent / median extent)`, then shifted so the total byte count
  matches the fixed-width file.  `tilt = -1` spends the same budget but favours the dense (small-box)
  clusters, `tilt = +1` favours the sparse ones.

## Measurements (bicycle, 6,131,954 primitives, 25 held-out views, clean 24.52 dB / 1447 MB)

| allocation | position bytes | file | B/prim | ratio | PSNR | Δ vs fixed |
|---|---|---|---|---|---|---|
| **fixed 8 bit (shipping)** | 18.40 MB | **76.56 MB** | 12.49 | **18.90×** | **24.06** | — |
| constant step, div 255 | 19.55 (+6.2 %) | 77.86 MB | 12.70 | 18.58× | 24.01 | −0.05 |
| constant step, div 127 | 17.28 (−6.1 %) | 75.56 MB | 12.33 | 19.15× | 23.89 | −0.17 |
| constant step, div 64 | 15.26 (−17.0 %) | 73.37 MB | 11.97 | 19.72× | 23.48 | −0.58 |
| constant step, div 48 | 14.35 (−22.0 %) | 72.29 MB | 11.79 | 20.02× | 22.90 | −1.16 |
| tilt −0.5 (budget-neutral) | 18.44 | 76.76 MB | 12.52 | 18.85× | 23.98 | −0.08 |
| tilt −1.0 (budget-neutral) | 18.07 | 76.27 MB | 12.44 | 18.97× | 23.79 | −0.27 |
| tilt +0.5 (budget-neutral) | 18.40 | 76.71 MB | 12.51 | 18.86× | 24.03 | −0.03 |

Decode path unchanged (7.5 s, 1.96 GB), one file, `cluster_bits` optional so older containers still load.

## Why it lost — measured, not argued

`experiments/m30_pos.py` compares each decoded model with the source and splits the error by the size of
the cluster the primitive belongs to:

| cluster extent quartile | 25–324 mm | 324–655 mm | 655–1313 mm | 1313–168651 mm |
|---|---|---|---|---|
| fixed 8 bit: mean&#124;Δ&#124; / extent | **0.00134** | **0.00134** | **0.00133** | **0.00130** |
| constant step div 127 | 0.00697 | 0.00299 | 0.00133 | 0.00135 |
| constant step div 64 | 0.01277 | 0.00517 | 0.00274 | 0.00134 |

The fixed width makes the absolute error **proportional to the local extent**, at every density — the
ratio is 0.00134 in all four quartiles.  That is the property the renders reward: where primitives are
packed tightly the boxes are small *because* the detail is there, and the 8-bit grid hands those clusters
micrometre precision for free.  Equalising the step (what "spend bits where the geometry needs them"
sounds like) destroys exactly those clusters: at div 64 the smallest quartile's mean error goes 0.25 →
2.39 mm, a 9.9× increase, while the largest quartile barely moves (4.58 → 4.70 mm).  Total mean error
1.73 → 3.15 mm.

The tilted allocations say the same thing from the other side: at *equal bytes*, tilting toward the dense
regions loses 0.08 dB and tilting toward the sparse ones loses 0.03 dB.  The fixed width is not merely
convenient, it sits at the top of this family in both directions.

## Verdict

**G1 FAIL** — the best point inside the 73 MB bar costs 0.58 dB (24.06 → 23.48), and the point that
reaches 72.29 MB costs 1.16 dB.  **G2 not run**: the mechanism is a ratio that held constant across four
orders of magnitude of cluster size, so it is not a property of this scene.  **G3/G4 hold** — the decoder
is unchanged and needs no new code path unless the stream is present.

Branch: `widths_are_already_uniform`.  The near-lossless row stays at **18.90× / 24.06 dB / 12.49
B/primitive**, and the position block stays at 3.0 B/primitive, which is no longer "the number we have
not attacked yet" — it is the number that keeps every cluster at constant relative precision.

## What this changes for the paper

The method section gains a sentence it could not have written before: the position quantiser is a fixed
grid **in units of the local cluster extent**, which is equivalent to a rate allocation proportional to
local primitive spacing, and both an equalised-step allocation and a density-tilted allocation were
measured to be worse at the same byte count.  That closes the "position bits are uniform, surely they can
be spent better" review question with data.

## Artifacts

`experiments/artifacts/a4/m30_{build.log,adapt.log,render.log}`; `experiments/m30_adapt.py`,
`experiments/m30_pos.py`, `experiments/tests/test_m30_widths.py` (3 cases).  Gate: **92 tests passed**.
