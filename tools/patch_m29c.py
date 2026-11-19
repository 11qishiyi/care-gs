import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()

if "for name in _ordered_names(streams):" in s:
    print("already ordered")
    raise SystemExit(0)

old = """    for name in ORDER:
        if name not in streams:
            continue
        raw = streams[name]"""
new = """    for name in _ordered_names(streams):
        raw = streams[name]"""
assert old in s, "loop"
s = s.replace(old, new, 1)

anchor = "def write_container("
helper = '''def _ordered_names(streams: dict) -> list:
    """``ORDER`` first, then the M29 split buckets right after their base stream."""
    names = []
    for name in ORDER:
        if name in streams:
            names.append(name)
            parts = sorted((k for k in streams if k.startswith(name + "#")),
                           key=lambda s: int(s.split("#")[1]))
            names.extend(parts)
    for k in streams:                     # anything ORDER does not know is refused above
        if k not in names and k.split("#")[0] not in ORDER:
            names.append(k)
    return names


'''
s = s.replace(anchor, helper + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("write_container now emits split buckets after their base stream")
