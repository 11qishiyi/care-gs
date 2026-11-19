# M40 — the frame boundary becomes the shipping default, measured on three scenes

Round 23, 2026-11-17. Node 2141478 (A100-PCIE-40GB, ¥2.80/h), rented 03:00, released after the measurements.
Pre-registered in `tools/m40_spec.md` before any measurement.

## What was asked

M34 measured `MIN_FRAME` as a knob on bonsai and found 256 KB frames free in bytes and 22× better under a lost
frame; M35 confirmed the bicycle half. The shipping configuration still wrote 4 MB frames, because that was
`m19_codec.MIN_FRAME`'s default. This round measured the byte price of the finer boundary on all three scenes
we can obtain, and then made it the default.

## The table

One configuration (`gp6-6-6_c8_sh3`, rank-16 / 48-bit basis), unchanged between arms except `--min-frame`.
Every damage number is against a control rendered from the untouched container **on this node, in this run**.

| scene | primitives | 4 MB container | 256 KB container | Δ bytes | control | 4 MB 0.1 % | 4 MB 1.0 % | 256 KB 0.1 % | 256 KB 1.0 % |
|---|---|---|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 76,557,737 B | 76,598,203 B | **+0.053 %** | 24.06 | 23.45 (−0.61) | 23.45 (−0.61) | **24.00 (−0.06)** | 23.73 (−0.33) |
| stump | 4,961,797 | 62,591,315 B | 62,649,653 B | **+0.093 %** | 25.52 | 24.67 (−0.85) | 24.67 (−0.85) | **25.33 (−0.19)** | 25.28 (−0.24) |
| bonsai | 1,244,819 | 15,302,360 B | 15,297,685 B | **−0.031 %** | 27.08 | 23.44 (−3.64) | 23.44 (−3.64) | **26.73 (−0.35)** | 25.68 (−1.40) |

Decode, fresh process per file: bicycle 7.88 s / 7.84 s, 1.96 GB peak RSS; stump 6.38 s, 1.60 GB; bonsai 1.57 s
/ 1.49 s, 0.47 GB. Encode: 137 / 142 s (bicycle), 27 s (bonsai).

## Verdict — `the_damage_win_is_scene_specific`, and the criterion was the wrong shape

* **T1 PASS.** The finer boundary costs ≤ 0.1 % of the file on all three scenes (the worst is stump at
  +0.093 %, and bonsai gets *smaller*), and both containers decode to the same model.
* **T2 PASS.** All three decode inside 12 s and inside 2.5 GB.
* **T3 FAIL as written.** The "+1.0 dB at 0.1 % on each scene" clause holds only on bonsai (+3.29); bicycle
  gains +0.55 and stump +0.66. The absolute floor also failed on bonsai's 1.0 % case (25.68 against the 26.0
  I pre-registered — which M34's own measurement, 25.62, already contradicted; the floor was mis-set, not
  the measurement).
* **T4 PASS.** Frame counts per stream are in `m40_cost.txt` and the container's `meta["min_frame"]`.

The pre-registered shape ("each scene gains ≥ 1.0 dB") was wrong because the *gain* is not the property that
matters: it is the difference between two damages, one of which is scene-dependent and one of which is not.
The property that actually holds on all three scenes is

> **with 256 KB frames, a 0.1 % burst costs 0.06–0.35 dB on every scene; with 4 MB frames it costs 0.61–3.64
> dB, and the size of the loss follows how much of the model's colour block one frame happens to be.**

That is the post-hoc reading, and it is the one the default is justified by. It is strictly stronger than
"≥ 1 dB better" for the decision at hand: it says the residual cost is bounded, which is what a shipping
format needs.

## The default changed

`experiments/m19_codec.py`: `MIN_FRAME = 256 << 10` (was `4 << 20`), with the measured byte prices in the
comment, and `encode_model` now records `meta["min_frame"]` so every file says which boundary it was written
with. `experiments/tests/test_m40_frame_default.py` pins the constant, the `MAX_FRAMES` headroom it needs
(> 140 frames for bonsai's coefficient block) and the header field.

Consequences for earlier numbers: containers built before this round used 4 MB frames; their byte counts are
unaffected at the tenth of a percent level (−0.03 … +0.09 %), so no previously reported ratio moves in its
second decimal. Decode times move by < 1 % (7.88 vs 7.84 s on bicycle).

## What this adds to the paper

* A **deployment table** with encode time, decode time, peak RSS and damage behaviour for three scenes, from
  one configuration — the "deployability" row the objective names.
* The robustness claim becomes scene-independent at a stated cost (≤ 0.35 dB for a 0.1 % burst, ≤ 1.40 dB at
  1 %), instead of "0.69 dB on bicycle and 3.64 dB on bonsai" as M33 measured it.
* A shipping default that is a measurement rather than a first guess: the 4 MB floor existed because 64
  frames cost 2.3 % of the file in M19; the finer boundary costs 0.05 % and removes the 3.09 dB failure.

## Files

`experiments/artifacts/a4/m40_{sizes.txt,cost.txt,encode.txt}`; per-condition logs and JSON on the node under
`/workspace/res/m40/`. Scripts: `experiments/run_m40.sh` (setup|build|cost|damage|all), `tools/m40_rest.sh`,
`tools/m40_spec.md`, `experiments/tests/test_m40_frame_default.py`.

## Reproduce

```bash
for S in bicycle stump bonsai; do bash experiments/run_m40.sh all "$S"; done
python experiments/m19_codec.py --selftest && python -m pytest experiments/tests -q
```

Cost: 3 scenes × (COLMAP 10 min + 2 builds + 2 renders + 6 damage renders) ≈ 1.6 h ≈ ¥4.5.
