import io

entry = r'''
## M30 round result (round 26, 2026-11-16 07:35, after the data)

Spec `tools/m30_spec.md`.  Node 2140676 (A100-PCIE-40GB, ¥2.80/h), rented 07:00, released 07:35.
Verdict: **`widths_are_already_uniform`** — G1 FAIL, G2 not run, G3/G4 hold.

| allocation | file | B/prim | ratio | PSNR | delta vs fixed |
|---|---|---|---|---|---|
| fixed 8 bit (shipping) | 76.56 MB | 12.49 | 18.90x | **24.06** | -- |
| constant step, div 255 | 77.86 MB | 12.70 | 18.58x | 24.01 | -0.05 |
| constant step, div 127 | 75.56 MB | 12.33 | 19.15x | 23.89 | -0.17 |
| constant step, div 64 | 73.37 MB | 11.97 | 19.72x | 23.48 | -0.58 |
| constant step, div 48 | 72.29 MB | 11.79 | 20.02x | 22.90 | -1.16 |
| tilt -0.5 (equal bytes) | 76.76 MB | 12.52 | 18.85x | 23.98 | -0.08 |
| tilt -1.0 (equal bytes) | 76.27 MB | 12.44 | 18.97x | 23.79 | -0.27 |
| tilt +0.5 (equal bytes) | 76.71 MB | 12.51 | 18.86x | 24.03 | -0.03 |

Mechanism (`experiments/m30_pos.py`, error split by cluster-extent quartile): the fixed width makes the
absolute error proportional to the local extent — the ratio mean|delta|/extent is 0.00134 / 0.00134 /
0.00133 / 0.00130 across the four quartiles, i.e. constant 0.13 % relative precision at every density.
Equalising the absolute step (div 64) takes the smallest quartile from 0.25 mm to 2.39 mm (9.9x) while the
largest quartile moves 4.58 to 4.70 mm; total mean error 1.73 -> 3.15 mm.  Budget-neutral tilts in both
directions also lost, so the fixed width is at the top of this family, not merely untested.

Implementation kept: `experiments/m30_adapt.py` (`choose_bits`, `choose_bits_tilted`, `adapt(...,
target_div/tilt/match_bytes)`), the decoder's `cluster_bits` branch in `m19_codec.decode` (optional stream,
older containers unaffected), `experiments/m30_pos.py`, `experiments/tests/test_m30_widths.py` (3 cases),
`experiments/run_m30.sh`, `tools/m30_{spec,audit,tilt,render}.sh`.  Gate: **92 tests passed**.

Docs: `experiments/M30_RESULTS.md`, appendix **N37**, `FRONTIER_BOUND.md` §9.

Cost: 0.58 h * ¥2.80 = ¥1.63.
'''

p = "D:/3dsg_1/experiments/METHOD_PLAN.md"
s = io.open(p, encoding="utf-8").read()
if "M30 round result" in s:
    print("already there")
else:
    io.open(p, "w", encoding="utf-8").write(s.rstrip() + "\n" + entry)
    print("METHOD_PLAN appended")
