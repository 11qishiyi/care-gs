import io

p = "APPENDIX_negative_results.md"
s = io.open(p, encoding="utf-8").read()
old = """| 4-bit offsets, 6-bit DC | 27.13 MB | 4.42 | **17.04 dB** | 5.36 s / 4.03 GB |
| 4-bit offsets, 6-bit DC→4 | 33.57 MB | 5.47 | 17.05 dB | — |"""
new = """| 4-bit offsets, 4-bit DC | 27.13 MB | 4.42 | **17.04 dB** | 5.36 s / 4.03 GB |
| 4-bit offsets, 6-bit DC | 33.57 MB | 5.47 | 17.05 dB | — |"""
assert old in s
io.open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
print("table fixed")
