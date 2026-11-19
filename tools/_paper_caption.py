import io

P = r"D:\3dsg_1\submission\cviu\main.tex"
s = io.open(P, encoding="utf-8").read()
a = ("cheapest \\emph{measured} variant that stays within it, written as measured size~($\\times$)\n"
     "($\\times$ reduction against the fp32 checkpoint) and the variant that achieves it:")
b = ("cheapest \\emph{measured} variant that stays within it, written as the measured size\n"
     "(reduction against the fp32 checkpoint) and the variant that achieves it:")
assert a in s
s = s.replace(a, b, 1)

c = ("\\texttt{MSC} selects a coding mode per primitive. No value is interpolated or extrapolated; the\n"
     "$2\\times$ column falls back to pruning because the ladder has no measured point below $2.1\\times$.}")
d = ("\\texttt{MSC} selects a coding mode per primitive, and \\texttt{+fp32} leaves the geometry at full\n"
     "width, which is what an existing quantiser ships. No value is interpolated or extrapolated, and\n"
     "a dash means no measured variant of the ladder reaches that tolerance; every cell here is a\n"
     "point that exists, not a fit.")
assert c in s
s = s.replace(c, d, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("caption cleaned up")
