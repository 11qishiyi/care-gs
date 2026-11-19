# M35 — the rate-distortion map, two scenes, and the frame size measured where it was claimed

**Round 31. Pre-registered in `tools/m35_spec.md` (19:05, before any download of this round), amended
twice before any render existed (`tools/m35_amend.md`).** Node 2141179 (A100-PCIE-40GB, ¥2.80/h),
19:00–21:15, ≈2.3 h ≈ ¥6.4.

Three debts were outstanding. This round pays two and a half of them: the missing rate-distortion curve,
M34's unmeasured P3, and the model cache. Nothing here is a new idea; the point was to find out what the
*format* does across 45–90 MB, which the series had never measured because every round measured one point
and moved on.

## 1. The map

bicycle, 6,131,954 primitives, 25 held-out views, clean model 24.52 dB. Payload 1447.1 MB, so the ratio
column is the series' usual denominator (236 B/primitive, fp32).

| spec | file | B/prim | ratio | PSNR | vs clean | on the frontier |
|---|---|---|---|---|---|---|
| `gp6-6-6_c8_sh3` (shipping) | 76.56 MB | 12.49 | **18.90×** | **24.06** | −0.46 | yes |
| `gp5-5-5_c7_sh3` | 69.34 MB | 11.31 | 20.87× | 23.80 | −0.72 | yes |
| `gp5-5-5_c6_sh3` | 66.24 MB | 10.80 | 21.85× | 23.60 | −0.92 | yes |
| `gp4-4-4_c6_sh3` | 57.23 MB | 9.33 | 25.28× | 22.53 | −1.99 | yes |
| `gp4-4-4_c6_sh2` | 55.18 MB | 9.00 | 26.22× | 21.82 | −2.70 | yes |
| `gp6-6-6_c6_sh2` | 69.30 MB | 11.30 | 20.88× | 22.82 | −1.70 | **no — dominated** |

stump, 4,961,797 primitives, 16 views, clean 26.15 dB, payload 1171.0 MB:

| spec | file | B/prim | ratio | PSNR | vs clean | on the frontier |
|---|---|---|---|---|---|---|
| `gp6-6-6_c8_sh3` | 62.59 MB | 12.61 | 18.71× | 25.52 | −0.63 | yes |
| `gp5-5-5_c7_sh3` | 56.72 MB | 11.43 | 20.65× | 25.30 | −0.85 | yes |
| `gp5-5-5_c6_sh3` | 54.41 MB | 10.96 | 21.52× | 25.04 | −1.11 | yes |
| `gp4-4-4_c6_sh3` | 47.46 MB | 9.57 | 24.67× | 24.42 | −1.73 | yes |
| `gp4-4-4_c6_sh2` | 45.75 MB | 9.22 | 25.60× | 22.32 | −3.83 | yes |
| `gp6-6-6_c6_sh2` | 56.77 MB | 11.44 | 20.63× | 22.70 | −3.45 | **no — dominated** |

Fits over the four `sh3` points (all that the format actually sells):

| scene | slope | R² | crosses 23.0 dB | crosses 24.0 dB |
|---|---|---|---|---|
| bicycle | **+3.74 dB per doubling** | 0.942 | 61.1 MB | 73.5 MB |
| stump | **+2.83 dB per doubling** | 0.971 | 33.2 MB | 42.3 MB |

## 2. What the map says that a single point could not

**The floor of the format at fixed primitive count is ~45–55 MB, and it is not a bug.** Every point below
that needs fewer primitives, i.e. pruning (M26), not fewer bits. So the honest mid-rate story is: this
format cannot be *asked* for 27 MB while holding 6.1 M primitives — the last ladder point is already at
9.00 B/primitive, of which 7.97 B is geometry before a single colour byte. HAC's 27.54 MB and PCGS's
19.09 MB are budgets that require a different *model*, not a different *quantiser*.

**Cutting SH degree is the worst way to save bytes, in both scenes.** `gp6-6-6_c6_sh2` is within 0.06 % of
`gp5-5-5_c7_sh3`'s bytes on bicycle and 1.02 dB worse; on stump it is 0.09 % away and **2.60 dB worse**. The
same bytes bought by lowering the quaternion/scale/opacity widths cost 0.26 dB (bicycle) and 0.22 dB
(stump). A degree-2 model is not a rate-controlled degree-3 model; it is a different function class, and it
sits *below* the frontier at every budget measured. This is the first round where that could be seen,
because it is the first round that built two specs at the same bytes.

**The frontier is flat at the top and steep at the bottom.** bicycle gives up 0.46 dB for 18.9×, 0.72 dB for
20.9×, 0.92 for 21.9×, then 1.99 dB for 25.3×. The last step (57.23 → 55.18 MB, 3.6 % fewer bytes) costs
0.71 dB. Whatever else the paper claims, it should not claim a smooth trade-off: the format is comfortable
in 18.9–21.9× and then falls off a cliff.

## 3. M34's P3, finally measured — on bicycle, at the fractions that were pre-registered

M34 changed the frame size and measured it on bonsai only. This round built bicycle at both frame sizes
(same code, same run) and damaged both at **0.1 % and 1.0 % of the payload**, then rendered:

| frame size | file | lost at 0.1 % | PSNR | lost at 1.0 % | PSNR |
|---|---|---|---|---|---|
| 4 MB | 76,557,737 B | 4.19 MB | **23.45 (−0.61)** | 4.19 MB | **23.45 (−0.61)** |
| 256 KB | 76,598,203 B (+0.05 %) | 0.52 MB | **24.00 (−0.06)** | 1.57 MB | **23.73 (−0.33)** |

* **Q3 PASS** — 256 KB costs +0.05 % of the file on bicycle.
* **Q2 PASS** — bicycle at 1.0 % burst is 23.73 dB ≥ 23.5 dB. The 4 MB container is 23.45 dB at the same
  fraction, and it is 23.45 dB at *every* fraction up to about 5 %, because one frame is 4.19 MB and cannot
  be made smaller by asking for less damage.
* The burst probe across three offsets (`tools/m35_bursts.py`) agrees: 4 MB loses 4.19 MB at 0.1 % and
  4.19–8.39 MB at 1.0 %; 256 KB loses 0.26–0.52 MB and 1.05–1.57 MB. Same stream every time (`sh_coef`).
* **stump's P3 row is not measured.** Its COLMAP sparse set did not unpack to the layout the archive tool
  expects until 20:54, which left time for the RD renders but not for a second damage arm. Reported as not
  measured rather than inferred.

## 4. The cache (Q4)

`/mnt/m35cache` now holds all three published models, hashed into
`experiments/artifacts/a4/m35/m35_cache.json`:

| scene | bytes | sha256 (first 16) |
|---|---|---|
| bicycle | 1,520,726,124 | `64d357cb25bd85f7` |
| stump | 1,230,527,188 | `e9186b7ab8764680` |
| bonsai | 308,716,644 | `a16af6d8815498ff` |

`/mnt` survived the node, so the next round starts with the models instead of 40 minutes of downloads.
This is the single largest cost line the series has been paying every round.

**And the mirror itself was measured, badly:** `hf-mirror.com` whole-file GET runs at **~10 MB/s**
(1.52 GB in 150 s), while the INRIA zip by range request runs at **0.2 MB/s** with twelve workers, and
`hf-mirror.com` *range* requests return almost nothing (0.6 kB/s), which is what M34's `zip_entry.py` was
built around and what made this round's first race measurement look like a dead link. Whole-file GET is the
fast path for this host; the range-request tool remains right for hosts that throttle per connection.

## 5. Criteria

| | criterion | result |
|---|---|---|
| Q1 | ≥ 6 points on bicycle, ≥ 25 MB span, monotone, R² ≥ 0.90 | **partial** — 6 points, 21.4 MB span; monotone **no** (one dominated sh2 point); R² over all six 0.78, over the four sh3 points **0.94** |
| Q2 | bicycle ≥ 23.5 dB, stump ≥ 25.0 dB at 1 % burst, 256 KB | **bicycle PASS (23.73)**, stump not measured |
| Q3 | 256 KB ≤ +1.0 % bytes on bicycle and stump | **bicycle PASS (+0.05 %)**, stump not measured |
| Q4 | cache holds three models with sizes and sha256 | **PASS** |

Branch: **`rd_map_complete`** on the substance (the map exists, spans two scenes, and separates the specs),
with Q1's monotonicity clause recorded as failed rather than reinterpreted: the seventh and sixth points are
not "off-trend noise", they are a dominated representation, and calling that monotone would hide the finding.

## 6. Two documentation errors this round found in its own tools

1. **`_c<N>` is the cluster-position width, not the DC width** (`experiments/qfp_rd.py:489-490`, floor 6).
   Two ladder points were pre-registered as `gp…_c5` / `gp…_c4` and both are illegal; the round lost ~10
   minutes and one ladder rung. Recorded in `tools/m35_amend.md` — twice, because the first amendment
   described the rule correctly and then used it wrongly one line later.
2. **`m33_damage.py --burst` takes fractions, not percentages.** `--burst 0.10,1.0` means 10 % and 100 % of
   the payload, not 0.1 % and 1 %. The first damage arm therefore measured catastrophic cases (10 % of the
   file lost 16.78 MB and one render, 100 % lost 114 MB and every stream) before being re-run at the
   fractions the spec actually named. Nothing in the code was wrong — the caller was.

## Reproduce

```bash
bash experiments/run_m35.sh models bicycle      # /mnt cache, whole-file GET from hf-mirror
bash experiments/run_m35.sh setup bicycle       # COLMAP + GT archive
bash experiments/run_m35.sh ladder bicycle      # 6 containers, PLANS in the script
bash experiments/run_m35.sh render bicycle      # 6 renders, ~70 s each
bash tools/m35_bursts_render.sh bicycle         # both frame sizes at 0.1 % and 1.0 %
python tools/m35_table.py --dir experiments/artifacts/a4/m35 --json .../m35_map.json
```

## Files

* `experiments/run_m35.sh` — setup / models / ladder / render / damage / cache.
* `experiments/m24_alpha.py` — `--min-frame`, `--coef-layout`, `--suffix` (added in M34, used here).
* `tools/m35_table.py` — the map, the frontier test, the log-linear fit and its crossings.
* `tools/m35_bursts.py` — burst damage across offsets, no rendering (lost bytes per condition).
* `tools/m35_bursts_render.sh` — the same at the pre-registered fractions, with renders.
* `tools/m35_render_stump_bonsai.sh` — sparse-layout fix and the two late scenes.
* `tools/m35_race.sh` — the source race that was measuring the wrong thing (kept, with its lesson).
* `experiments/artifacts/a4/m35/` — `render_{bicycle,stump}.log`, `damage_pct_{262144,4194304}.log`,
  `bursts.json`, `m35_cache.json`, `m35_map.json`, `cache_report.txt`.

## Cost

Node 2141179: 19:00 rented, 21:15 released, ≈2.25 h × ¥2.80 = **≈ ¥6.3**. Of that, ~25 min was the ladder
builds (7 specs × 3.5 min on 6.1 M primitives), ~30 min renders, ~30 min setup, and the rest was the
download detour through the slow source.
