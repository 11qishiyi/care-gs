# M31 — the shipping configuration on three scenes: the rate model generalises, the fidelity cost does not

Pre-registered in `tools/m31_spec.md` before any multi-scene measurement, amended once in
`tools/m31_amend.md` at 08:15 (also before any measurement of the scenes it changes).  Node 2140682
(A100-PCIE-40GB, ¥2.80/h), rented 07:32, released 09:55.

## What was tested

Every number this project has quoted since M22 is a bicycle number.  The shipping container
(`gp6-6-6_c8_sh3`, rank-16 / 48-bit colour basis, one scale level, per-stream alphabet) had never been
built on a second scene.  The question was not "is it good" but "is it the same point": does one
configuration, chosen on bicycle, hold its **rate** (≥17×) and its **fidelity** (within 0.6 dB of the
scene's own clean model) on scenes it was never tuned on?

The pre-registered criterion set was H1 (per scene ≥17.0× and within 0.6 dB of that scene's clean PSNR),
H2 (encode ≤180 s on bicycle, other scenes scaled by primitive count), H3 (decode ≤12 s, peak RSS
≤2.5 GB — the M25 numbers, re-checked off-bicycle) and H4 (the table, plus per-stream sizes for at
least two scenes).

## The amendment: the release publishes three scenes, not four

The four-scene plan named bicycle, stump, flowers and treehill.  A URL probe
(`tools/m31_probe_urls.sh`, run before any scene measurement) found that
`https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/<scene>/point_cloud/iteration_30000/point_cloud.ply`
answers for exactly **bicycle, stump and bonsai** (302; every other name returns 404 —
garden, room, treehill, counter, kitchen, playroom).  `flowers` is not in the pretrained release at all
(`Entry not found`).  The table is therefore three scenes.  This is written down rather than papered
over: the fourth scene does not exist to measure, and inventing a different denominator or a
self-trained model for it would have broken the comparison the criterion is about.

## Measurements

One configuration, three scenes, nothing re-tuned.  25 / 16 / 167 held-out views, 1236×822.

| scene | primitives | file | B/prim | ratio (payload) | ratio (as-shipped PLY) | clean dB | ours dB | Δ | SSIM | enc s | dec s | RSS GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 76.56 MB | 12.49 | **18.90×** | 19.86× | 24.52 | **24.06** | **−0.46** | 0.7393 | 121 | 7.49 | 1.96 |
| stump | 4,961,797 | 62.59 MB | 12.61 | **18.71×** | 19.66× | 26.15 | **25.52** | **−0.63** | 0.7432 | 98 | 6.00 | 1.60 |
| bonsai | 1,244,819 | 15.30 MB | 12.29 | **19.20×** | 20.17× | 28.06 | **27.08** | **−0.98** | 0.8868 | 24 | 1.39 | 0.47 |

Two denominators are reported because the series has used one of them for nine rounds.  The ratio used
everywhere in this project is against the **payload** (236 B/primitive: 3×4 means, 4 opacity, 3×4
scales, 4×4 rotation, 45×4 SH); the fp32 PLY a user actually downloads also carries 12 B of normals,
i.e. 248 B/primitive.  Against the file it is 19.7–20.2×; against the payload 18.7–19.2×.  Both are
real, the paper will quote the payload number and footnote the file number.

**Encode time** above is the shipped file only.  The run stage that produced the run log does *two*
builds and two writes (the auto container and the legacy bytes-alphabet container, which M24 keeps for
comparison), so it reports 230 / 186 / 44 s — exactly the ~2× one would expect.  Measured on the one
file that ships: **121 / 98 / 24 s**.  The limits H2 implied are 180 / 146 / 37 s.

## Criterion by criterion

| | bicycle | stump | bonsai | verdict |
|---|---|---|---|---|
| H1 rate ≥17.0× | 18.90× | 18.71× | 19.20× | **PASS 3/3** |
| H1 fidelity ≤0.6 dB below clean | −0.46 ✓ | −0.63 ✗ | −0.98 ✗ | **FAIL 1/3** |
| H2 encode ≤180 s (scaled) | 121 s ≤180 | 98 s ≤146 | 24 s ≤37 | **PASS** |
| H3 decode ≤12 s / ≤2.5 GB | 7.49 s / 1.96 | 6.00 s / 1.60 | 1.39 s / 0.47 | **PASS** |
| H4 table + two per-stream tables | — | — | — | **PASS (three)** |

**Verdict: `the_config_is_scene_specific`.**  The rate half of the configuration transfers exactly —
three scenes, three B/primitive in 12.3–12.6, three ratios in 18.7–19.2×, two of them *better* than
bicycle.  The fidelity half does not: the same colour block costs 0.46 dB on bicycle, 0.63 dB on stump
and 0.98 dB on bonsai.

## Why: the gap is the colour block, and paying rate does not buy it back

The obvious reading of bonsai's −0.98 dB is "1.2 M primitives is a small file, so the rate is
effectively lower".  That reading is testable and wrong.  Re-encoding bonsai at the two *previous*
shipping points (the generous end of the M29 scan) costs 17 % more bytes and recovers 0.11 dB:

| bonsai config | file | B/prim | PSNR |
|---|---|---|---|
| `gp6-6-6_c8_sh3` (**shipping**) | 15.30 MB | 12.29 | 27.08 |
| `gp7-7-7_c9_sh3` | 17.21 MB | 13.83 | 27.18 |
| `gp8-8-8_c10_sh3` | 17.89 MB | 14.37 | 27.19 |

+16.9 % bytes buys +0.11 dB, i.e. the curve is already flat at the shipping point — the ship is on the
saturation shoulder, and the remaining 0.87 dB lives in the *representation* (rank-16 / 48-bit basis,
3-bit SH coefficients, 6-bit DC), not in the rate.  Bonsai is the worst case for this representation:
an indoor scene whose colour detail is high-frequency at the scale of a 1 M-primitive model.  This is
the same mechanism N31/N35 named for the mid-rate containers, seen here on the near-lossless one.

## What does transfer: the byte budget

Per-stream sizes, same configuration, three scenes:

| stream | bicycle | stump | bonsai | share |
|---|---|---|---|---|
| `sh_coef` (basis coefficients) | 18.58 MB | 15.29 MB | 3.74 MB | 24.3–24.5 % |
| `cluster_off` (positions) | 18.21 | 14.82 | 3.72 | 23.7–24.3 % |
| `geo_quat_abc` (rotation) | 13.74 | 11.16 | 2.76 | 17.8–18.1 % |
| `geo_scales` | 12.50 | 9.93 | 2.41 | 15.8–16.3 % |
| `geo_opacities` | 4.31 | 3.55 | 0.87 | 5.6–5.7 % |
| `sh_scale` (DC levels) | 4.36 | 3.48 | 0.83 | 5.5–5.7 % |
| `sh_dc` | 3.69 | 3.24 | 0.77 | 4.8–5.2 % |
| `geo_quat_which` | 0.63 | 0.67 | 0.07 | 0.5–1.1 % |
| `cluster_hdr` | 0.53 | 0.43 | 0.11 | 0.7 % |
| **total** | **76.55 MB** | **62.59 MB** | **15.30 MB** | |

The *shares* are stable to within a percentage point across a 5× range of primitive counts.  So the byte
model built in M23–M24 is scene-invariant, which is what makes the rate prediction 18.7–19.2× in the
first place; what varies by scene is how much distortion those bytes buy.  Reported this way, the two
halves of the configuration are separate claims and the paper can make the first one universally and
the second one per scene.

## What this changes

* `experiments/FRONTIER_BOUND.md` §10 records the three-scene point and retires the phrase
  "≤0.5 dB at 19×", which was true on bicycle only.
* `experiments/artifacts/a4/sota_table.md` gains the three-scene table; the near-lossless headline row
  stays bicycle (that is the comparable scene) and the other two are footnoted with their own Δ.
* The negative-results appendix gains **N38**: a configuration validated on one scene is a
  configuration whose fidelity cost has a scene-specific variance of 0.5 dB, and no amount of
  re-encoding the *same representation* recovers it.

## Reproduce

```
# node: image Pytorch 2.6.0_cuda_12.4, 40 GB GPU, PLY + COLMAP archives under /workspace/data
SCENES=bicycle bash experiments/m20_setup.sh          # downloads the published PLY
SCENE=bicycle bash experiments/run_m17.sh data        # COLMAP + held-out split
SCENE=bicycle bash experiments/run_m17.sh base        # the clean model's own PSNR
bash experiments/run_m31.sh all bicycle               # build | render | cost | streams
bash experiments/run_m31.sh all stump
bash experiments/run_m31.sh all bonsai
bash tools/m31_time.sh                                # the one-file encode wall clock
python tools/m31_table.py                             # the table above
```

## Cost and artefacts

Node 2140682, 07:32 → 09:55 ≈ 2.4 h ≈ ¥6.7.  Artifacts in `experiments/artifacts/a4/m31/`:
`enc_{bicycle,stump,bonsai}.txt` (dual-container encode), `single/`-run timings (121/98/24 s, from the
run console — the node was released before they were fetched), `cost_*.log`, `render_*.log`,
`render_bonsai_hi.log` (the crossover check), `streams_*.txt` (three per-stream tables),
`sizes.json`.  Gates: `pytest experiments/tests` **92 passed**; `m1_check_bytes.py` 881 cases 0
mismatches; `check_py311.py` 144/144.
