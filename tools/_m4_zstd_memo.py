import io

P = r"D:\3dsg_1\experiments\m4_bytes.py"
s = io.open(P, encoding="utf-8").read()

helper = '''

def _zstd_memoed(buf, level: int, memo: dict) -> bytes:
    """``_zstd`` with a content-keyed memo.

    Streams are compressed independently, and several specs in one grid share
    byte-identical geometry streams (everything that keeps geometry at fp32 with the
    same retained set).  Hashing is milliseconds against seconds of zstd-12, and the
    key includes the length, so a hit is always the same blob.
    """
    import hashlib

    key = (int(level), len(buf), hashlib.blake2b(buf, digest_size=16).digest())
    hit = memo.get(key)
    if hit is None:
        hit = _zstd(buf, level)
        memo[key] = hit
    return hit
'''

anchor = "\ndef measure_scene("
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)

a1 = """    cache = {}
    rows = []"""
b1 = """    cache = {}
    zmemo = {}
    rows = []"""
assert a1 in s
s = s.replace(a1, b1, 1)

a2 = """        zstd_flat = None if skip_flat else \\
            sum(len(_zstd(v, level)) for v in streams.values()) / stored
        zstd_morton = sum(len(_zstd(v, level)) for v in stream_m.values()) / stored"""
b2 = """        zstd_flat = None if skip_flat else \\
            sum(len(_zstd_memoed(v, level, zmemo)) for v in streams.values()) / stored
        zstd_morton = sum(len(_zstd_memoed(v, level, zmemo))
                          for v in stream_m.values()) / stored"""
assert a2 in s
s = s.replace(a2, b2, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("added a content-keyed zstd memo to measure_scene")
