import io

p = "D:/3dsg_1/experiments/artifacts/a4/sota_table.md"
s = io.open(p, encoding="utf-8").read()

entry = r'''
### the position block, and why its width is not a free parameter (M30)

| allocation | file | ratio | PSNR |
|---|---|---|---|
| fixed 8-bit grid over the local cluster box (shipping) | 76.56 MB | 18.90x | 24.06 |
| constant absolute step, one bit coarser | 75.56 MB | 19.15x | 23.89 |
| constant absolute step, 1.8 bits coarser | 73.37 MB | 19.72x | 23.48 |
| budget-neutral tilt toward the dense clusters | 76.76 MB | 18.85x | 23.98 |
| budget-neutral tilt toward the sparse clusters | 76.71 MB | 18.86x | 24.03 |

With a fixed width the absolute error is proportional to the cluster extent at every density (ratio
0.00134 in all four size quartiles).  That is a rate allocation in units of local primitive spacing, and
every alternative measured at the same or smaller byte count was worse.
'''

if "M30)" in s:
    print("already there")
else:
    io.open(p, "w", encoding="utf-8").write(s.rstrip() + "\n" + entry)
    print("sota_table updated")
