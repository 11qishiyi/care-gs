import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()

old = """    names = []
    for name in ORDER:
        if name in streams:
            names.append(name)
            parts = sorted((k for k in streams if k.startswith(name + "#")),
                           key=lambda s: int(s.split("#")[1]))
            names.extend(parts)"""
new = """    names = []
    for name in ORDER:
        if name in streams:
            names.append(name)
        #: the split buckets stand in for the base stream, so they are emitted even when the base
        #: name itself is absent from the dict (that is the normal case)
        parts = sorted((k for k in streams if k.startswith(name + "#")),
                       key=lambda s: int(s.split("#")[1]))
        names.extend(parts)"""
assert old in s
io.open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
print("bucket emission fixed")
