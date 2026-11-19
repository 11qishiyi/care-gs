import re

fixes = [
    ("10.80×", "10.58×"),
    ("10.80x", "10.58x"),
    ("14.48×", "14.51×"),
    ("14.48x", "14.51x"),
    ("13.46×", "13.49×"),
    ("13.46x", "13.49x"),
    ("9.84×", "9.85×"),
    ("9.84x", "9.85x"),
    ("13.34×", "13.35×"),
    ("13.34x", "13.35x"),
    ("14.48x at", "14.51x at"),
]
files = ["experiments/M22_RESULTS.md", "experiments/METHOD_PLAN.md", "experiments/FRONTIER_BOUND.md"]
for f in files:
    s = open(f, encoding="utf-8").read()
    n = 0
    for a, b in fixes:
        if a in s:
            n += s.count(a)
            s = s.replace(a, b)
    open(f, "w", encoding="utf-8").write(s)
    print(f, "->", n, "replacements")
