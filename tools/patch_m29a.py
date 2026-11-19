import io

# --- m29_split: expose the bucket rule so the decoder can rebuild the same order ----------------
p = "experiments/m29_split.py"
s = io.open(p, encoding="utf-8").read()

old = "def _buckets(kind: str, n: int, meta: dict, streams: dict, spec) -> np.ndarray:"
new = '''def buckets_for(kind: str, n: int, k: int, streams: dict, spec) -> np.ndarray:
    """The bucket of every primitive, computed from data the decoder holds at that point.

    ``pos`` needs nothing (the stored order is Morton, so the 256-primitive block index is
    ``arange(n) // 256``), and ``scale`` needs only the scale stream, which the container decodes
    before rotation and opacity.
    """
    if kind == "pos":
        blk = np.repeat(np.arange((n + 255) // 256), 256)[:n]
        return (blk % int(k)).astype(np.int64)
    if kind == "scale":
        bits = int(spec.geo.get("scales", 8))
        codes = C.unpack_bits(streams["geo_scales"], bits, n * 3, dtype=np.uint16).reshape(n, 3)
        return np.clip((codes[:, 0].astype(np.int64) * int(k)) >> bits, 0, int(k) - 1)
    raise SystemExit(f"unknown split {kind}")


def _buckets(kind: str, n: int, meta: dict, streams: dict, spec) -> np.ndarray:'''
assert old in s
s = s.replace(old, new, 1)

old_b = '''    if kind == "pos":
        blk = np.repeat(np.arange((n + 255) // 256), 256)[:n]
        return (blk % SPLITS["pos"]).astype(np.int64)
    if kind == "scale":
        bits = int(spec.geo.get("scales", 8))
        codes = C.unpack_bits(streams["geo_scales"], bits, n * 3, dtype=np.uint16).reshape(n, 3)
        return np.clip((codes[:, 0].astype(np.int64) * SPLITS["scale"]) >> bits, 0, SPLITS["scale"] - 1)
    raise SystemExit(f"unknown split {kind}")'''
new_b = "    return buckets_for(kind, n, SPLITS[kind], streams, spec)"
assert old_b in s
s = s.replace(old_b, new_b, 1)
io.open(p, "w", encoding="utf-8").write(s)

# --- m19_codec: rejoin split streams on read, and let write_container see "<name>#<bucket>" -------
p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()

old_unknown = "    unknown = [k for k in streams if k not in ORDER]"
new_unknown = (
    '    #: M29: a context-split stream is ``<name>#<bucket>``; its base name has to be in ORDER\n'
    '    unknown = [k for k in streams if k not in ORDER and k.split("#")[0] not in ORDER]'
)
assert old_unknown in s
s = s.replace(old_unknown, new_unknown, 1)

old_read = "    meta = json.loads(hdr)"
assert old_read in s
s = s.replace(old_read, "    meta = json.loads(hdr)\n    _split_rejoin(meta, streams)", 1)

anchor = "def read_container("
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
print("split wiring installed")
