# M33 — what a broken file looks like

**Round 29.** Pre-registration `tools/m33_spec.md` (12:05, before the first corrupted byte); node
2140862 (RTX A4000, ¥1.35/h), rented 11:59, released 15:30. Three scenes, the shipping container
`gp6-6-6_c8_sh3` (rank-16 basis, 48-bit coefficients), eleven conditions each: an intact control,
six burst-corruption levels and four truncation prefixes, every one decoded with
`read_container(tolerant=True)`, written to PLY, archived and rendered on the same held-out views as
every other number in this paper.

## The headline

A file that loses a frame still renders, and the two reasons it did *not* were both decoder bugs, not
properties of the format:

| condition (bicycle, 76.56 MB, control 24.06 dB) | before M33 | after the length fix | after both fixes |
|---|---|---|---|
| 0.1 % burst (one 4 MB frame) | **19.80** (−4.26) | 16.51 (−7.55) | **23.37** (−0.69) |
| 2 % burst | 16.97 | — | 22.76 (−1.30) |
| 5 % burst | 14.78 | — | 22.26 (−1.80) |
| prefix 75 % | 17.22 | — | 17.22 |
| prefix 90 % | 16.25 | — | 22.71 |

The middle column is the instructive one: fixing the *first* bug made the number worse, because the
first bug had been hiding the second.

## The two defects

1. **A lost frame shifted every byte after it.** `read_container(tolerant=True)` appended *nothing*
   for a frame that failed its CRC and padded the stream at the end, so the hole did not keep its
   length: every later byte in that stream was reinterpreted. A one-frame burst in `sh_coef` changed
   the colour of **all 6,131,954 primitives** (median |Δ| 0.33, max 1.08) instead of the 72.6 % the
   frame actually held. Fixed by appending `b"\x00" * raw_frames[i]` — the hole keeps its size, and
   `meta["damaged_bytes"]` now counts it. Regression test:
   `experiments/tests/test_m33_damage.py::test_a_lost_frame_does_not_move_the_bytes_after_it`.
2. **The basis block had no neutral code.** With the shift fixed, a lost frame decodes as zero bytes,
   and zero is not "no colour" in the M22 alphabet: a coefficient is decoded as
   `(code + 0.5) * step - 1`, so code 0 is the **most negative** coefficient the alphabet holds. A
   single frame therefore painted 72.6 % of bicycle as dark as the model could go (16.51 dB). The
   shelf streams always had a reserved neutral code (`qmax + 1`); the basis block's equivalent is the
   **midpoint** `2**(b-1)`, one per component. `m22_basis.neutralise_coef` maps each lost byte range
   to the component and primitive window it covers (the codes are concatenated component-major, so
   both follow from `n` and the component depths in the header) and writes the midpoint.
   Test: `experiments/tests/test_m33_basis_neutral.py` (windows are exact, nothing outside them moves,
   and the filled primitives decode near the model's mean residual rather than at the extreme).

## Measured (all three scenes, after both fixes)

| condition | bicycle 76.56 MB / 24.06 | stump 62.59 MB / 25.52 | bonsai 15.30 MB / 27.08 |
|---|---|---|---|
| control | 24.06 | 25.52 | 27.08 |
| 0.10 % burst | 23.37 (−0.69) | 24.67 (−0.85) | 23.44 (−3.64) |
| 0.25 % | 23.37 | 24.67 | 23.44 |
| 0.50 % | 23.37 | 24.67 | 23.44 |
| 1.0 % | 23.37 | 24.67 | 23.44 |
| 2.0 % | 22.76 (−1.30) | 24.67 | 23.44 |
| 5.0 % | 22.26 (−1.80) | 24.25 (−1.27) | 23.44 |
| prefix 25 % | 9.25 | 11.27 | 8.87 |
| prefix 50 % | 9.25 | 11.27 | 8.87 |
| prefix 75 % | 17.22 | 16.05 | 10.29 |
| prefix 90 % | 22.71 | 23.31 | 25.53 |

Frames lost: bicycle 1 / 1 / 1 / 1 / 2 / 3 (0.1→5 %); stump 1 / 1 / 1 / 1 / 1 / 2; bonsai **1 / 1 /
1 / 1 / 1 / 1** — its entire `sh_coef` block is one 4 MB frame, so no corruption level below 5 % can
cost it more than that frame, and none can cost it less.

Nothing else moved: `means`, `scales`, `opacities` and `quats` are byte-identical to the control in
every damaged condition (loss fraction 0.00 % in all 33 mechanical reports), because the damage lands
in the colour block and the geometry streams arrive first.

## Verdict: `degrades_but_visibly`

* **L1 (1 % burst within 2.0 dB, all scenes) — FAIL.** bicycle −0.69, stump −0.85 pass; **bonsai
  −3.64 fails**. The frame is 4 MB and bonsai's colour block is smaller than one frame, so its
  smallest possible corruption is its entire colour refinement.
* **L2 (monotone, 5 % ≥ 18 dB) — PASS.** bicycle 23.37 → 22.76 → 22.26, stump 24.67 → 24.25, bonsai
  flat at 23.44; every scene stays above 22 dB at 5 %.
* **L3 (50 % prefix ≥ 20 dB) — FAIL.** 9.25 / 11.27 / 8.87 dB. A prefix below ~75 % is an *empty*
  render, not a coarse one.
* **L4 (damaged decode ≤ 1.2× the intact cost) — PASS.** bicycle 11.28 s / 2.08 GB damaged vs
  11.28 s / 2.01 GB intact (time ratio 1.00, peak ratio 1.03); a truncated file is *cheaper*
  (7.4 s) because there is less to decode.

## Why L3 fails, and why reordering does not fix it

Geometry is 70 % of the payload (positions 18.2 + rotations 14.4 + scales 12.5 + opacities 4.3 MB of
76.6 MB). A renderable model needs *all* of it plus the DC term and its level — about 57 MB, i.e. 75 %
of the file — before any colour refinement arrives. Below that the render is black: a Gaussian with a
zero scale covers no pixels, which is why the 25 % and 50 % rows are identical (both have lost
`geo_scales`).

`tools/m33_reorder.py` rewrote the same streams (bit-identical decode, `streams_identical=True`) with
the colour header first and re-measured the ladder: 50 % still gives 9.25 dB. **The order is not the
constraint; the dependency set is.** The only way to move the ladder down is to ship a coarse
*predictive* stand-in for geometry (a lower-resolution splat set) in the first half of the file —
which is a different format, not a different order.

## What one lost frame costs, in primitives

The coefficient codes are concatenated **component-major**: component *k* owns a contiguous span, so a
4 MB frame inside an 18.6 MB block holds one component's values for 68 % of the primitives and the
remaining components stay intact. That is why 72.6 % of primitives "change" while the image only loses
0.69 dB: each affected primitive loses 1 of its 16 residual components, not its colour.

Interleaving the codes primitive-major (all 16 components of primitive *i*, then *i+1*) would put
~0.7 M primitives behind the same frame instead of 4.2 M. M20 measured that layout as *worse* for
compression (V1 coefficient-major beat it by 17 %), so this is a real trade — the shipping choice
buys bytes with damage granularity, and now both sides of it are measured.

## Cross-scene summary for the paper

* Corruption: **−0.69 / −0.85 / −3.64 dB** for the smallest detectable damage, **−1.80 / −1.27 /
  −3.64 dB** at 5 %. The file degrades, it does not fail.
* Truncation: a linearly decodable ladder from 75 % (17.2 / 16.1 / 10.3 dB) to 90 % (22.7 / 23.3 /
  25.5 dB).
* Cost: a damaged decode is the same speed and 3 % more memory than an intact one.

## Reproduce

```bash
bash experiments/run_m33.sh setup bicycle      # deps + PLY + COLMAP images
bash experiments/run_m33.sh build bicycle      # shipping container (76.56 MB)
bash experiments/run_m33.sh damage bicycle     # 11 conditions, decode + archive + render
bash tools/m33_dcf.sh bicycle                  # the prefix ladder with a DC-first order
python3 tools/m33_cost.py --dir /workspace/res/m33/bicycle/dmg
python3 tools/m33_collect.py --dir /workspace/res/m33
```

Local gates: `pytest experiments/tests` **99 passed** (4 new: three damage-decoder contracts, two
windows/neutral-fill contracts), `m1_check_bytes.py` 881 cases 0 mismatches, `check_py311.py`
147/147, `m19_codec --selftest` ALL PASS.

Artefacts: `experiments/artifacts/a4/m33/` (the three damage logs, the three DC-first logs,
`cost_bicycle.json`, container sizes, and 33 mechanical reports under `dmg/`).

## Cost

Node 2140862, 3.5 h at ¥1.35/h ≈ **¥4.7**, including two scene downloads that had to be re-fetched
after the first COLMAP pass silently fetched only 114 of bicycle's 194 images (space-separated
`SCENES` is parsed as a comma-separated list).
