p = "experiments/METHOD_PLAN.md"
s = open(p, encoding="utf-8").read()
old = (
    "-0.24 dB (stump), against 10.01x / 9.85x before.  12x is reachable at about -0.05 dB, i.e. the "
    "M15-M21\nconclusion \"12x is unreachable for this family\" is corrected: it was unreachable while "
    "the 45\ncoefficients were coded as independent numbers."
)
new = (
    "-0.24 dB (stump), against 10.01x / 9.85x before.  12x (19.67 B/prim, of which geometry and DC\n"
    "take 8.58) leaves 89 colour bits, which sits between the measured 64-bit point (13.63x, -0.05 dB)\n"
    "and the 96-bit point (10.58x, -0.01 dB), i.e. about -0.03 dB -- so the M15-M21 conclusion \"12x is\n"
    "unreachable for this family\" is corrected: it was unreachable while the 45 coefficients were\n"
    "coded as independent numbers."
)
if old in s:
    s = s.replace(old, new)
    open(p, "w", encoding="utf-8").write(s)
    print("patched 12x paragraph")
else:
    i = s.find("-0.24 dB (stump), against 10.01x")
    print("anchor missing; nearby text:")
    print(repr(s[i:i + 420]))
