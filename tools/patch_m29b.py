import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()

if "_split_rejoin" in s:
    print("already wired")
    raise SystemExit(0)

old_unknown = "    unknown = [k for k in streams if k not in ORDER]"
new_unknown = (
    '    #: M29: a context-split stream is ``<name>#<bucket>``; its base name has to be in ORDER\n'
    '    unknown = [k for k in streams if k not in ORDER and k.split("#")[0] not in ORDER]'
)
assert old_unknown in s, "guard"
s = s.replace(old_unknown, new_unknown, 1)

old_ret = '        meta["damaged_bytes"] = lost\n    return meta, streams'
assert old_ret in s, "return"
s = s.replace(old_ret, '        meta["damaged_bytes"] = lost\n    _split_rejoin(meta, streams)\n    return meta, streams', 1)

anchor = "def _decompress("
helper = '''def _split_rejoin(meta: dict, streams: dict) -> None:
    """Undo an M29 context split in place.

    Each bucket was packed and compressed on its own; the primitive order is rebuilt from the same
    context rule the encoder used, so the rejoined codes are bit-identical to the unsplit stream.  The
    loop runs in plan order, because the ``scale`` split reads the already-rejoined scale stream.
    """
    plan = meta.get("split_plan") or {}
    if not plan:
        return
    import m29_split
    import qfp_rd as _Q
    spec = _Q.parse_spec(str(meta["spec"]))
    n = int(meta["n"])
    for name, info in plan.items():
        keys = sorted((k for k in streams if k.startswith(name + "#")),
                      key=lambda s: int(s.split("#")[1]))
        if not keys:
            continue
        bits, dims = int(info["bits"]), int(info["dims"])
        k = len(keys)
        b = m29_split.buckets_for(info["kind"], n, k, streams, spec)
        codes = np.empty((n, dims), dtype=np.uint16)
        for j, key in enumerate(keys):
            sel = b == j
            cnt = int(sel.sum())
            arr = unpack_bits(streams[key], bits, cnt * dims, dtype=np.uint16).reshape(cnt, dims)
            codes[sel] = arr
            del streams[key]
        streams[name] = pack_bits(codes.reshape(-1), bits)


'''
s = s.replace(anchor, helper + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("m19_codec split rejoin installed")
