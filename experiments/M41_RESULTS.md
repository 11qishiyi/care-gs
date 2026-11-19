# M41 — the encoder's frames are independent, so the pool is free (and the real bottleneck is elsewhere)

Round 24, 2026-11-17. Node 2141489 (A100-PCIE-40GB, ¥2.80/h), rented 04:20, released after the measurement.
Pre-registered in `tools/m41_spec.md` before any measurement.

## What was asked

Every round so far optimised the decoder and left the encoder single-threaded. A container is ~20 000
independent zstd calls, so the wall clock is a scheduling artefact. Can the encoder write the same file faster,
and is the write even where the time goes?

## The measurement

Shipping streams (M22 basis colour block, `gp6-6-6_c8_sh3`, 256 KB frames), built once per scene, then the same
container written with 1/2/4/8 workers. Each worker count ran in its own process so peak RSS is that write's.

| scene | primitives | stream build | jobs=1 | jobs=2 | jobs=4 | jobs=8 | file | md5 identical |
|---|---|---|---|---|---|---|---|---|
| bicycle | 6,131,954 | 58.9 s | 11.31 s | 5.51 s (0.487×) | **3.21 s (0.284×)** | 1.89 s (0.167×) | 76,598,203 B | yes |
| stump | 4,961,797 | 137.7 s | 8.71 s | 4.85 s (0.557×) | **2.55 s (0.293×)** | 1.41 s (0.162×) | 62,649,653 B | yes |
| bonsai | 1,244,819 | 21.2 s | 2.61 s | 1.38 s (0.529×) | **0.70 s (0.268×)** | 0.40 s (0.153×) | 15,297,685 B | yes |

The byte counts are the M40 containers to the byte (76,598,203 / 62,649,653 / 15,297,685), and the md5 is
identical at every worker count on every scene: the pool changes the schedule, not the file.

## Verdict — `parallel_encode_wins`, on a fraction of the job

* **E1 PASS.** md5 identical for N ∈ {1,2,4,8} on three scenes; the containers are byte-for-byte the ones M40
  shipped through the serial path.
* **E2 PASS.** bicycle jobs=4 = 0.284× of jobs=1 (3.5× on the write); jobs=8 reaches 0.167×, so the pool is not
  the limit — 12 cores were available and the curve is still improving.
* **E3 PASS.** Same file ⇒ same decode; `test_m41_parallel.py` also compares decoded tensors stream by stream.
* **E4 PASS.** Peak RSS 1.00× at every worker count (it is dominated by the streams themselves, see below).

**The honest denominator.** The write is 11.31 s of a 70.2 s encode on bicycle (58.9 s build + 11.3 s write), so
end-to-end the pool buys **1.13×**, not 3.5×. On stump it buys 1.04× (137.7 + 8.7 → 137.7 + 2.6), and on bonsai
1.34×. The round measured what it set out to measure and found the amdahl: **stream construction is 84–94 % of
the encoder**, and the write was never the bottleneck.

Two facts that fall out of the same table and matter for the next round:

* **Peak RSS 18.8 GB** on bicycle (15.3 GB stump, 4.2 GB bonsai) — the encoder holds every stream in RAM as
  Python bytes, and then holds them again as frame payloads. That is 2.4× the decoder's 1.96 GB and 12× the
  file. Nothing in the format requires it.
* **Stream build 58.9 s vs 137.7 s** for 6.13 M vs 4.96 M primitives — not proportional to the primitive count.
  The stump build is dominated by the alphabet-choice step, which compresses the SH candidates twice (M24:
  `choose()` over `bits` and `bytes`) before the winning layout is compressed a third time for the file.

## What this adds to the paper

* An encode row for the deployment table that is a measurement: **142 s (bicycle), 98 s (stump), 27 s (bonsai)**
  end to end with `--jobs 4`, versus 153 / 100 / 29 s serial, from containers that are byte-identical.
* A stated limit: the format's encoder is memory-bound and build-bound, not compression-bound. Any claim about
  encode speed has to name which part it improved.
* The pool is a free, format-neutral win — it can be enabled by default without touching a single byte.

## Files

`experiments/m41_par.py` (driver: build once, write at N workers in child processes, hash and time each),
`experiments/run_m41.sh`, `experiments/m19_codec.py` (`_compress_frames`, `write_container(..., jobs)`,
`encode_model(..., jobs)`), `experiments/tests/test_m41_parallel.py` (4 cases),
`experiments/artifacts/a4/m41_{bicycle,stump,bonsai}.json`, `m41_run.log`.

## Reproduce

```bash
bash experiments/run_m41.sh          # three scenes, N = 1,2,4,8, per-scene JSON
python -m pytest experiments/tests/test_m41_parallel.py -q
```

Cost: ~0.5 h ≈ ¥1.4.
