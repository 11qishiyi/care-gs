import io

p = "experiments/artifacts/a4/sota_table.md"
s = io.open(p, encoding="utf-8").read()

frag = """

---

# M24 / M25 / M29: the near-lossless point, and what moved it

Same scene (bicycle, 6,131,954 primitives), same 25 held-out views, same container path.  `ratio` is
1447 MB (the fp32 model as the renderer loads it) over the file.  The uncompressed model renders
**24.52 dB**; that number is the ceiling of this table, not a baseline to beat.

| point | spec | file | B/prim | ratio | PSNR | decoder |
|---|---|---|---|---|---|---|
| M22 basis (r16/48) | `c10_o8_sh3` | 98.53 MB | 16.07 | 14.69x | 24.12 | 7.7 s / 2.0 GB |
| M24 shipping | `gp8-8-8_c10_sh3` + o6 + c9 | 83.41 MB | 13.60 | 17.35x | 24.08 | 7.69 s / 1.97 GB |
| **M29 shipping** | **`gp6-6-6_c8_sh3`** | **76.56 MB** | **12.49** | **18.90x** | **24.06** | **7.51 s / 1.96 GB** |

The M29 sweep (registered as an amendment after the entropy probe, before any number existed):

| spec | file | B/prim | ratio | PSNR | SSIM |
|---|---|---|---|---|---|
| `gp8-8-8_c9` | 87.43 MB | 14.26 | 16.55x | 24.11 | 0.7439 |
| `gp7-7-7_c9` | 85.64 MB | 13.97 | 16.90x | 24.10 | 0.7433 |
| `gp6-6-7_c8` | 77.43 MB | 12.63 | 18.69x | 24.06 | 0.7395 |
| `gp6-6-6_c8` | 76.56 MB | 12.49 | 18.90x | 24.06 | 0.7393 |

Why the curve is shallow where it is: the attribute streams are already at their entropy
(`experiments/m29_entropy.py`), so a nominal bit removed is not a bit saved — zstd spends 6.67 bits on
8-bit scale codes, so dropping to 7 bits recovers ~0.6.  The one number that was pure choice is the
10-bit position offset, which codes at exactly 10.00 bits; 10 -> 8 bits is 1.5 B/primitive on its own.
"""
io.open(p, "w", encoding="utf-8").write(s.rstrip() + frag)
print("sota table: near-lossless section replaced/added")
