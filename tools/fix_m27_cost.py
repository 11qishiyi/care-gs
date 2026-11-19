import io

reps = [
    ("experiments/M27_RESULTS.md",
     "node 2140647, A100-PCIE-40GB, ¥2.80/h, rented 03:31, released 04:55 (≈1.4 h ≈ ¥3.9).",
     "node 2140647, A100-PCIE-40GB, ¥2.80/h, rented 03:31, released 05:05 (≈1.55 h ≈ ¥4.3)."),
    ("experiments/M27_RESULTS.md",
     "Node 2140647: 03:31 rent → 04:55 release, 1.4 h at ¥2.80/h ≈ **¥3.9**",
     "Node 2140647: 03:31 rent → 05:05 release, 1.55 h at ¥2.80/h ≈ **¥4.3**"),
    ("experiments/METHOD_PLAN.md",
     "**Cost:** node 2140647, 1.4 h ≈ ¥3.9.",
     "**Cost:** node 2140647, 1.55 h ≈ ¥4.3."),
    ("experiments/METHOD_PLAN.md",
     "### M27 round result (round 23, 2026-11-16 04:55, after the data)",
     "### M27 round result (round 23, 2026-11-16 05:05, after the data)"),
]
for path, old, new in reps:
    s = io.open(path, encoding="utf-8").read()
    if old in s:
        io.open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))
        print("ok", path, new[:40])
    else:
        print("MISS", path, old[:50])
