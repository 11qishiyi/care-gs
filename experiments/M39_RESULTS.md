# M39 — pushing the prune prefix down, where the headroom is largest

Round 22, 2026-11-17. Bicycle, published model (6,131,954 primitives, clean 24.52 dB on 25 held-out views).
Node 2141461 (A100-PCIE-40GB, ¥2.80/h), rented 01:20, released after the measurements.

## What was asked

M36 found the rate pressure Pareto-good on a model pruned to 25 % (+0.17 dB, −6.8 % bytes). M37 found it
repairs only part of the damage on the *converged* model. Those two points suggested the return grows with
the headroom a schedule has to recover, so this round tested the place where headroom is largest: 15 % and
10 % keep. Pre-registered in `tools/m39_spec.md` before any measurement.

## Measurement

Same source, same 12k steps, factor 4, same recipe, same shipping container spec (`gp6-6-6_c8_sh3`), same 25
held-out views. Arm **a** is the plain loss, arm **b** adds the log rate term on `shN, sh0, scales,
opacities`, λ calibrated at step 0 to a 5 % gradient share and frozen.

| prefix | primitives | arm | container | B/prim | ratio (payload 1447.1 MB) | PSNR | Δ vs clean | SSIM | wall |
|---|---|---|---|---|---|---|---|---|---|
| 15 % | 919,793 | a | 11,499,080 B | 12.50 | 125.85× | 20.02 | −4.50 | 0.4356 | 790 s |
| 15 % | 919,793 | **b** | **10,822,808 B** | **11.77** | **133.71×** | **20.12** | −4.40 | 0.4439 | 729 s |
| 10 % | 613,195 | a | 7,660,004 B | 12.49 | 188.92× | 19.00 | −5.52 | 0.3857 | 647 s |
| 10 % | 613,195 | **b** | **7,242,797 B** | **11.81** | **199.80×** | **19.02** | −5.50 | 0.3908 | 679 s |

## Verdict — `pressure_does_not_scale_with_headroom`

* **N1 PASS at both prefixes.** b/a = 0.9412× at 15 % (+0.100 dB) and 0.9455× at 10 % (+0.020 dB): the
  pressure still never hurts and still removes 5–6 % of the bytes.
* **N2 PASS under the Pareto reading.** `p15-b` and `p10-b` are Pareto-optimal against every point this
  project has measured — nothing has both fewer bytes and more dB. They extend the measured curve down to
  **7.24 MB = 199.80×** at 19.02 dB. The pre-registered *interpolation* clause is undefined below the
  smallest measured byte count (17.96 MB); the first draft of `tools/m39_table.py` clamped there and
  declared a 7.2 MB container "dominated" by an 18 MB one, which is a property of the clamp, not the data.
  The tool now reports interpolation only inside the measured range and judges outside it by dominance
  (`experiments/tests/test_m39_frontier.py` pins both readings).
* **N3 PASS.** Wall clock b/a = 0.923× (15 %) and 1.049× (10 %).
* **N4 PASS.** Same steps, factor, spec and views; λ printed; keep fraction in every file name.

## The hypothesis was wrong in an interesting way

| keep | the pressure's byte saving | its dB gain |
|---|---|---|
| 25 % (M36) | −6.8 % | +0.17 |
| 15 % (this round) | −5.9 % | +0.10 |
| 10 % (this round) | −5.5 % | +0.02 |

The byte saving is nearly constant and the **dB gain shrinks as the schedule gets deeper** — the opposite of
what "return grows with headroom" predicted. What the pressure actually does is the same thing at every
depth: it shrinks the magnitudes that the quantiser has to represent, worth about half a byte per
primitive. On a 25 % model that half byte buys +0.17 dB; on a 10 % model, where 613k primitives are already
carrying a 5.5 dB deficit, the same half byte buys nothing measurable. The lever is a **fixed-rate**
adjustment, not a quality-recovery mechanism.

## What this adds to the paper

* The format's rate-distortion curve now covers **7.24 MB → 76.56 MB** (199.80× → 18.90×) with six measured
  points on the Pareto front, all from one configuration and one code path.
* The pressure is confirmed as a *constant* ~5–7 % byte lever, prefix-independent — useful as a knob, not as
  a quality lever. That closes the "maybe deeper pruning plus rate awareness closes the mid-rate gap" idea:
  at 19 dB we are 5.5 dB below the clean model and still 12 B/primitive, i.e. the deficit is the primitive
  count, exactly as N25–N27/N36/N45 said.
* Cost per primitive is ~12.5 B at 25 %, 15 % and 10 % keep — the container has no economy of scale with
  fewer primitives.

## Cost and files

Node 2141461 (A100-PCIE-40GB ¥2.80/h) 01:20 → 02:45, ≈1.4 h ≈ ¥4.0. Four fine-tunes (647–790 s each),
four encodes, four renders. Setup was free (model from `/mnt/m35cache`, COLMAP 194 images, 10 min).

Measurements: `experiments/artifacts/a4/m39_{render.txt,m39_time.txt,run.log,table.json}`.
Scripts: `experiments/run_m39.sh` (setup|prune|arm|encode|render|all), `tools/m39_table.py`,
`tools/m39_spec.md`, `experiments/tests/test_m39_frontier.py`.

## Reproduce

```bash
bash experiments/run_m39.sh setup
bash experiments/run_m39.sh prune 0.15 && bash experiments/run_m39.sh prune 0.10
for F in 0.15 0.10; do for A in a b; do
  bash experiments/run_m39.sh arm "$F" "$A"
  bash experiments/run_m39.sh encode "$F" "$A"
  bash experiments/run_m39.sh render "$F" "$A"
done; done
python tools/m39_table.py --dir /workspace/res/m39
```
