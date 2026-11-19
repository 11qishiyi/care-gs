# M34 — the frame is the knob

**Round 30. Pre-registered in `tools/m34_spec.md` (15:35, before any build), amended three times before
the first measurement (`tools/m34_amend.md`, `m34_amend2.md`, `m34_amend3.md`).**

M33 measured what one lost frame costs and found that the number is set almost entirely by one format
constant: the 4 MB zstd frame. Every corruption from 0.1 % to 1 % of the payload destroys exactly one
frame, so the smallest *detectable* damage already costs 0.69 dB on bicycle and 3.64 dB on bonsai — whose
entire colour block is smaller than one frame. That was the one criterion M33 failed, and it is a
parameter, not a representation problem.

This round moves the parameter.

## What was measured

| | |
|---|---|
| Scene | **bonsai**, 1,244,819 primitives, 16 held-out views, delivered container 15.30 MB |
| Configuration | `gp6-6-6_c8_sh3`, rank-16 shared basis, 48-bit coefficients — the shipping configuration, unchanged |
| Sweep | `MIN_FRAME` ∈ {4 MB (shipping), 1 MB, 256 KB} |
| Per arm | file size, per-stream frame counts, decode time, peak RSS, and three burst conditions (0.10 %, 1.0 %, 5.0 %) decoded tolerantly and rendered |
| Node | 2141031, Tesla V100-16GB, ¥1.85/h |

The published bonsai model renders 28.09 dB on this node and our 15.30 MB container 27.06 dB, so the
container is 1.03 dB below its own source — consistent with M31's three-scene table on different hardware
(M31 measured 27.08 dB for the same container on an A4000, and cross-node PSNR carries ~0.3 dB of build
uncertainty, which is why every number below is a within-run comparison against that arm's own intact
render).

Scope was cut to one scene because the model downloads were the binding constraint this round — see
*Why one scene* below. The scene kept is the one whose criterion failed.

## Results

Every arm decodes to the **identical** model (`sha1 ebe2cdd08c2d` over all arrays), so nothing below is a
different model; the only difference is where the frame boundaries fall.

| `MIN_FRAME` | file | vs 4 MB | `sh_coef` frames | decode | peak RSS | intact |
|---|---|---|---|---|---|---|
| 4 MB (shipping) | 15,302,362 B | — | 2 | 1.63 s | 0.66 GB | 27.06 dB |
| 1 MB | 15,352,658 B | **+0.36 %** | 8 | 1.63 s | 0.66 GB | 27.06 dB |
| 256 KB | 15,297,691 B | **−0.03 %** | 29 | 1.66 s | 0.66 GB | 27.06 dB |

Damage, same node, same views, compared against that node's own intact render:

| `MIN_FRAME` | 0.10 % burst | 1.0 % | 5.0 % |
|---|---|---|---|
| 4 MB | 4.19 MB lost → **23.97 dB (−3.09)** | same (−3.09) | same (−3.09) |
| 1 MB | 1.05 MB → **25.78 (−1.28)** | same (−1.28) | 3.15 MB → 24.79 (−2.27) |
| 256 KB | 0.26 MB → **26.92 (−0.14)** | 0.79 MB → 25.62 (−1.44) | 1.84 MB → 25.43 (−1.63) |

Geometry is untouched in all nine conditions (`means_changed_frac = 0.0000`); only `sh_coef` loses frames.

**The smallest detectable damage goes from 3.09 dB to 0.14 dB — 22× smaller — for 0.03 % fewer bytes.**

## Criteria

| # | criterion | result |
|---|---|---|
| **P1** | 1 MB ≤ +2.0 %, 256 KB ≤ +4.0 % of the 4 MB container | **PASS** (+0.36 %, −0.03 %) |
| **P2** | bonsai, one lost frame ≥ 26.0 dB with a smaller setting | **PASS** (26.92 dB at 256 KB; 23.97 dB at 4 MB) |
| **P3** | bicycle / stump at 1.0 % burst ≥ 23.5 / 25.0 dB | **not measured** (scope cut, see amendments) |
| **P4** | decode time and peak RSS ≤ 1.10× the 4 MB container | **PASS** (1.02×, 1.00×) |

**Verdict: `smaller_frames_win`.** Three of four criteria measured and passed; P3 is explicitly not
measured rather than extrapolated.

## What the numbers say

* **The cost of a lost frame is set by the fraction of the colour block it covers, not by the byte count.**
  bonsai's `sh_coef` is 4.19 MB: at 4 MB one frame is ~96 % of it (−3.09 dB), at 1 MB ~24 % (−1.28 dB), at
  256 KB ~6 % (−0.14 dB). The same 4 MB of file is a rounding error in the position stream and the entire
  colour budget in a small scene — which is exactly why M33's criterion failed on bonsai and not on
  bicycle.
* **Smaller frames are free at this scale.** Bonsai's container is 0.03 % *smaller* with 29 frames than
  with 2: more zstd frames cost a 64-byte header each and buy a slightly better local match. The 1 MB arm
  pays +0.36 %, which is the honest price of the middle setting (it is also the least useful: 0.10 % and
  1.0 % both land on one frame, so its whole first row is the same measurement).
* **Decode is unchanged** — 1.63 → 1.66 s, RSS 0.66 GB, because a frame is decompressed as it is needed
  and the decoder never holds more than one.
* **The knob has a second job.** M21's progressive file and M33's damage table are both frame-quantised;
  at 256 KB the same container would give a 29-step ladder instead of a 2-step one.
* **Interleaving the coefficient block is implemented and deliberately not measured.** A per-primitive
  layout would put one lost frame on 13 primitives instead of 100 (test) — but the error *energy* is
  conserved by that permutation: a frame then covers ~4 % of the primitives with all their components gone
  instead of ~68 % with one component gone (0.043 vs 0.045 of the residual energy), so the prediction is
  "PSNR unchanged, concentration worse". The frame size is the part of this that pays.

## Why one scene (and what it cost)

The model download, not the measurement, set this round's length. Measured on the node against both hosts:

| host | 16:05 | 16:12 | 16:25 | 17:05 | 17:25 |
|---|---|---|---|---|---|
| `hf-mirror.com`, one connection | 63 kB/s | 614 kB/s | 22 kB/s | — | — |
| `repo-sam.inria.fr` (INRIA archive), 8–12 connections | — | 230 kB/s (1 conn) | — | 315 kB/s | 87 kB/s |

The three scenes are 3.06 GB; at these rates that is four to eight hours of setup against ~20 minutes of
measurement.  bonsai's 309 MB completed; bicycle's 1.52 GB did not.

Two fixes came out of it, both kept:

* **`tools/zip_entry.py`** pulls a single entry out of the 14.66 GB INRIA `models.zip` by range request —
  the published PLYs are the same files (`bicycle/point_cloud/iteration_30000/point_cloud.ply` = 1520.73 MB,
  matching the HF copy used since M20) — with resumable per-worker part files. Small ranges, long fuses:
  a 1 MB range at 40 kB/s needs half a minute and a short retry budget turns a slow download into a failed
  one.
* **`/mnt/m34cache`** is the persistent network disk across MatPool nodes, so models are paid for once.

A third fix was a real bug in `experiments/fetch_m360_colmap.sh`: the three COLMAP sparse files were
downloaded with **no size check**. The mirror returned an `images.bin` of 19,902,317 B where the repository
says 68,376,564 B; the truncated file parses a valid header and then dies with
`struct.error: unpack requires a buffer of 4 bytes` 200 records in, and the archive stage reports only the
exception. The script now verifies every sparse file against the repository's own size and retries, and
the round's own bonsai model was rebuilt from a repaired file (292 images, `read_images_bin` clean).

## Reproduce

```bash
# model (one-time, into the persistent cache)
python3 tools/zip_entry.py --url https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/pretrained/models.zip \
  --entry bonsai/point_cloud/iteration_30000/point_cloud.ply --out /mnt/m34cache/bonsai.ply --workers 8
# ground truth + archive
SCENES=bonsai JOBS=6 bash experiments/fetch_m360_colmap.sh
SCENE=bonsai bash experiments/run_m17.sh base
# the sweep
bash tools/m34_drive1.sh bonsai          # build + damage + render for 4 MB / 1 MB / 256 KB
python3 tools/m34_check.py   --dir /workspace/res/m34/bonsai   # frames, decode, RSS, decode identity
python3 tools/m34_summary.py --dir /workspace/res/m34/bonsai   # lost bytes per condition
```

## Cost

Node 2141031 rented 15:29, released 18:55 (V100-16GB, ¥1.85/h) ≈ 3.4 h ≈ **¥6.3**, of which about 20
minutes was measurement and the rest was the download described above.

## Artifacts

`experiments/artifacts/a4/m34/` — `drive_bonsai.log` (build, damage and render lines for all nine
conditions), `m34_check` output (frames, decode, RSS, identical-decode hashes), the per-condition
`damage_*.json` files.

## Files

* `experiments/tests/test_m34_interleave.py` — interleaved coefficient layout round-trips exactly, decodes
  to the same model as component-major, and puts one lost frame on 13 primitives instead of 100.
* `experiments/tests/test_m34_frames.py` — the requested frame size is the one that binds, and the file
  reports the frame count it actually has.
* `experiments/m19_codec.py:50` — `MAX_FRAMES` 64 → 512 (without it, a 256 kB request on bicycle's 36.8 MB
  coefficient stream is silently rounded up to 574 kB).
* `experiments/m24_alpha.py` — `--min-frame`, `--coef-layout`, `--suffix`; the stream's own `min_frame` is
  written into `meta`.
* `experiments/m22_basis.py` — `pack_codes`/`unpack_codes`/`coef_windows` accept `"interleaved"`.
* `tools/m33_damage.py` — `--burst` (sweep a subset of conditions; skip truncation).
* `experiments/run_m34.sh`, `tools/m34_{drive1,check,summary,fetch,race,cache}.{sh,py}`.
