import io

entry = r'''
## 9. And the widths were already an allocation (M30, 2026-11-16)

M29 ended with one lever on the table: the near-lossless container codes each position offset at 8 bits
on a grid over its own 256-primitive cluster box, so a per-cluster width looked like free money.  It was
not.  Eight allocations were built and rendered, and every one of them lost:

| allocation | file | ratio | PSNR |
|---|---|---|---|
| fixed 8 bit | 76.56 MB | 18.90x | **24.06** |
| constant step, one bit coarser | 75.56 MB | 19.15x | 23.89 |
| constant step, 1.8 bits coarser | 73.37 MB | 19.72x | 23.48 |
| constant step, 2.4 bits coarser | 72.29 MB | 20.02x | 22.90 |
| budget-neutral tilt toward dense | 76.76 MB | 18.85x | 23.98 |
| budget-neutral tilt toward sparse | 76.71 MB | 18.86x | 24.03 |

The measurement that explains it: with a fixed width, the absolute position error is proportional to the
cluster extent, and the ratio is constant — 0.00134 in every size quartile.  The grid therefore delivers
0.13 % relative precision at every density, which is precisely what the renderer rewards; equalising the
absolute step instead takes the densest quartile's mean error from 0.25 mm to 2.39 mm and costs 0.58 dB
for 4 % of the file.

So the near-lossless row is **18.90x at 24.06 dB, 12.49 B/primitive**, and every block of it now has a
measured reason: the colour block is a shared rank-16 basis (M22), the DC and geometry widths are at their
entropy (M29), the position grid is a rate allocation in local units (M30), and the container is a single
self-describing file that decodes in 7.5 s under 2 GB (M19, M25).  12x was reached in M22 and is now
reached at 0.04 dB of the source; going below 12.5 B/primitive means giving up the per-primitive
representation itself, which is where the mid-rate experiments (M27, M28) already looked and lost.
'''

p = "D:/3dsg_1/experiments/FRONTIER_BOUND.md"
s = io.open(p, encoding="utf-8").read()
if "## 9. And the widths" in s:
    print("already there")
else:
    io.open(p, "w", encoding="utf-8").write(s.rstrip() + "\n" + entry)
    print("FRONTIER_BOUND §9 appended")
