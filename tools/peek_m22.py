p = "experiments/METHOD_PLAN.md"
s = open(p, encoding="utf-8").read()
old = """- **The near-lossless shelf moves to 14.69x at -0.21 dB** (was 10.01x)"""
assert old in s
i = s.find("**What this changes.**  The near-lossless shelf")
print(s[i:i + 700] if i >= 0 else "anchor not found")
