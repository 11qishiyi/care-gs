import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()

old = "    for name, info in plan.items():"
new = (
    "    #: ``pos`` first: a ``scale`` split is bucketed by the scale codes, which may themselves be\n"
    "    #: a split stream.  JSON sorts the plan keys, so the stored order cannot be relied on.\n"
    '    order = sorted(plan.items(), key=lambda kv: (kv[1].get("kind") != "pos", kv[0]))\n'
    "    for name, info in order:"
)
assert old in s, "loop"
io.open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
print("two-phase rejoin installed")
