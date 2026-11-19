# M19 — from a byte model to a file that decodes

**Round 15, 2026-11-15. Node 2140205 (A100-PCIE-40GB, ¥2.80/h).**

Every ratio this series has reported since M1 was a *model*: an arithmetic count of bits per
primitive, checked against the length of a bit-packed stream, never against a file that could be
read back. `m16_timing.py` records the consequence in one field: `decode_s = null`. The objective
asks for encoding and decoding speed, memory, and deployability; a container and a decoder are what
turn the curve into a format.

## 1. What was built

`experiments/m19_codec.py` (~560 lines) writes a single file `MAGIC=b"GS1\0"`, `VERSION=1`, with
fifteen named streams (`geo_hdr`, `cluster_hdr`, `cluster_off`, `sh_hdr`, `sh_scale`,
`geo_scales`, `geo_quats`, `geo_opacities`, `geo_quat_which`, `geo_quat_abc`, `sh_dc`, `sh_rest`,
`sh_index`, `sh_cb_hdr`, `sh_cb_centroids`) in a fixed order. Each stream is cut into zstd frames of
at most 4 MB (`CHUNK=256 KiB`, `MIN_FRAME=4 MB`, `MAX_FRAMES=64`), every frame carries its own
`crc32`, and the header is ~2 KB of lengths, offsets and the reconstruction constants.

* `decode(meta, streams)` rebuilds positions (cluster-relative or gridded), scales, quaternions
  (8-bit grid or smallest-three), opacities, and colour (VQ codebook or the 3-bit ladder). The
  multi-stage colour coder is *refused with a reason* rather than silently mis-decoded.
* `to_ply()` writes INRIA-format PLY, so the existing probe renders the decoded file.
* `damage_file(..., burst=True)` flips a contiguous run of bytes; `read_container(tolerant=True)`
  zero-fills a frame whose CRC fails and counts `damaged_bytes`.

`m4_bytes` gained the two pieces of side information the model had never charged: `geo_hdr`
(min/step of every grid-coded attribute) and `sh_hdr` (the two SH block scales). Both are now in
`qfp_rd.bytes_per_prim` as well, charged per primitive only when the caller supplies `n_stored`.

## 2. Measurement (bicycle, 6,131,954 primitives, fp32 file 1447 MB = 236.0 B/prim)

| variant | file | B/prim | × vs fp32 | encode | decode | decode + PLY | rendered PSNR | RD curve |
|---|---|---|---|---|---|---|---|---|
| `c10_o8_sh3` | 151.72 MB | 24.74 | **9.54×** | 37.4 s | **15.72 s** | 25.81 s | **24.33 dB** | 24.33 |
| `c8_o8_sh3` | 146.93 MB | 23.96 | **9.85×** | 36.1 s | **14.31 s** | 24.29 s | **24.30 dB** | 24.30 |
| `vq12_c8_o8` | 72.15 MB | 11.77 | **20.05×** | 245.6 s | **2.86 s** | 13.04 s | **23.85 dB** | 23.86 |

Clean reference on the same 25 views: 24.52 dB. So the near-lossless row is **−0.19 pp at 9.54×**,
and it is now a claim about a file, not about arithmetic.

* Framing cost: **+1.2 %** for `c10_o8_sh3` (25.36 → 24.74 B/prim after the fixed order; the pure
  stream model was 25.07), **+0.1 %** for the VQ row. Frames of 4 MB are what make damage local.
* Peak RSS 16.4–19.6 GB, dominated by the source model: the decoder holds codes and centroids.
* Decode throughput ≈ **390 k primitives/s** for the scalar rows, 1.9 M/s for the VQ row; PCGS
  reports 20.5 s for the same scene at 19.09 MB, so the format is faster than the published
  decoder and 7.9× larger.
* Tensor round trip (`c10_o8_sh3`, compared per attribute in the encoder's own order): positions
  mean 2.11e-4 / max 8.2e-2, scales (log) 2.03e-2, quaternions 1.94e-3, opacities (logit) 2.12e-2,
  SH mean 1.41e-2 / max 1.25 (the 3-bit ladder's own grid).
* Damage (burst flips inside `sh_rest`, 25 frames over 103.5 MB): 0.1 %, 0.5 %, 1 % and 2 % all
  destroy exactly **one frame = 4.05 %** of that stream, which moves the colour of **18.92 %** of
  primitives and **0.00 %** of the positions. Damage cost is bounded by the frame size and does not
  cross attributes. Scattered (one bit per frame) damage is the wrong experiment: it kills every
  frame and measures the frame *count*.

## 3. Two defects the format exposed, and what they cost

The first container decoded to **20.04 dB** where the curve promised 24.33. The control chain
located it in one afternoon: identity PLY round trip 24.52 (= clean), reference quantiser written
straight to PLY 24.33 (= curve), the same in Morton order 24.33, decoded geometry with reference
colour 20.14, and swapping *only* positions back 24.33. Everything else — colour, scales,
quaternions, opacities — was innocent.

**Defect 1: the Morton code was a lexicographic sort.** `m4_bytes.morton_order` packed the three
axis codes as three consecutive 21-bit fields (`dim * bits + b`) instead of interleaving them
(`b * 3 + dim`). Sorting that is sorting by `x`; a 256-primitive block then spans the whole scene in
`y` and `z`, the per-block grid is as coarse as the scene, and the decoded cloud is off by
decimetres. Measured: mean position error **5.2e-3 vs 2.1e-4** for `qfp_rd.quantize_cluster` — 25×
worse at the same nominal 10 bits — and **4.3 dB** of PSNR. The byte count never moved, because bits
are bits; that is why eighteen months of curves could not see it. After the fix the two
implementations produce identical blocks and the container lands on the curve to two decimals
(24.33 / 24.30 / 23.85).

**Defect 2: the model did not charge the side information it needs.** A decoder cannot invert
`codes_grid` without the min/step of each attribute, and cannot rescale the SH ladder without its
two block scales; neither was written and neither was charged. Now `geo_hdr` is 8 B per coded
component (0 for a clean model, 32 B for the geometry-only rows, 64 B for the 3-bit SH rows) and
`sh_hdr` is 8 B. At six million primitives this is 1.2e-5 B/primitive — invisible in every ratio,
and the difference between a byte model and a format — but it is why the model and the encoder now
agree byte for byte on all 881 cases of `m1_check_bytes`.

## 4. What this changes for the objective

* **Decode exists and is fast**: 15.7 s for 6.13 M primitives (24.74 B/prim), 2.9 s for the 20× row.
  Encoding is 37 s scalar / 246 s VQ (the k-means is 95 % of it).
* **Deployability**: one file, no side-car streams, deterministic decode, CRC per frame.
* **Robustness is now measurable** and is a dimension the published methods do not report: a
  truncated or corrupted file loses at most one 4 MB frame, and loses it inside one attribute.
* **Nothing moved on rate–distortion.** 9.54× at −0.19 pp is the same operating point M15 measured;
  the format confirms it rather than improving it. The 4–5× representation gap of N25 stands.
* The regression tests pin both defects: `test_the_morton_order_makes_compact_blocks` compares block
  extents against `qfp_rd`, and `test_the_side_information_is_charged_once_the_file_size_is_known`
  pins payload + 72 B = file on a synthetic model.

## 5. Reproduction

```bash
bash experiments/run_m19.sh deps data base      # archive + clean reference
bash experiments/run_m19.sh encode              # container, timings, decoded PLY
bash experiments/run_m19.sh render              # probe the decoded PLY
bash experiments/run_m19.sh damage              # burst damage table
python experiments/m19_codec.py --archive /workspace/data/m360std --scenes bicycle \
    --specs c10_o8_sh3 --verify                 # per-attribute round trip
```
Costs: encode 37 s + decode 16 s + PLY write 10 s per scalar row; render 10.8 s per variant.

## 6. Tool defects found while measuring

1. `matcli node exec` drops the exit status of a `nohup`-detached job and times out near 120 s, so
   every long step must be launched detached and polled through a log.
2. `make_m360_archive` hard-links the source PLY: re-encoding without deleting
   `output/<scene>_<spec>_dec` renders the *previous* model and reproduces its PSNR to two decimals.
3. The damage table was initially stitched from the *stream* offsets, so at 0.1 % it flipped
   ~104 k bytes — a burst — while at 2 % it flipped 2 M scattered bytes across all 25 frames. Both
   rows printed the same "lost 4.05 %", which is what a scattered experiment must do: it measures
   frame count, not resilience.
4. `python -c` with quotes, heredocs, and PowerShell's `<` redirection all fail on this host; shell
   logic has to live in a `.sh` file pushed as bytes.
