"""Mirror the vector-quantised SH byte model in m1_analyse.py."""
import io

P = r"D:\3dsg_1\experiments\m1_analyse.py"
s = io.open(P, encoding="utf-8").read()

A = 'CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)\n'
ADD = A + '''#: vector-quantised SH: one dictionary index per primitive, 8-bit centroids
SH_VQ_CENTROID_BYTES = 1
VQ_NOMINAL_PRIMS = 4_000_000


def vq_codebook_bytes(bits: int, cols: int) -> float:
    return float((1 << int(bits)) * int(cols) * SH_VQ_CENTROID_BYTES)
'''
if "SH_VQ_CENTROID_BYTES" not in s:
    s = s.replace(A, ADD, 1)

OLD = '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None) -> float:'''
NEW = '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None) -> float:'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)

OLD = '''    cols = sh_cols(sh_degree)
    b_sh = cols * 4.0 if sh_bits >= 32 else cols * sh_bits / 8.0 + SH_SCALE_BYTES'''
NEW = '''    cols = sh_cols(sh_degree)
    if sh_vq_bits is not None:
        b_sh = int(sh_vq_bits) / 8.0 + vq_codebook_bytes(sh_vq_bits, cols) / float(
            n_stored or VQ_NOMINAL_PRIMS)
    elif sh_bits >= 32:
        b_sh = cols * 4.0
    else:
        b_sh = cols * sh_bits / 8.0 + SH_SCALE_BYTES'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)

# parse_spec -> 6-tuple with the codebook width
OLD = '''        return 1.0, 32, {}, None, None
    deg_out = None'''
NEW = '''        return 1.0, 32, {}, None, None, None
    deg_out = None'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)
OLD = '                return 1.0, 32, {attr: int(body[len(alias):])}, None, None'
NEW = '                return 1.0, 32, {attr: int(body[len(alias):])}, None, None, None'
if OLD in s:
    s = s.replace(OLD, NEW, 1)
OLD = '        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None'
NEW = '        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None, None'
if OLD in s:
    s = s.replace(OLD, NEW, 1)

OLD = '''    if rest[:1] in ("m", "c") and rest[1:2].isdigit():
        geo_l, sh_l, cbits = {}, 32, None'''
NEW = '''    if ((rest[:1] in ("m", "c") and rest[1:2].isdigit())
            or (rest.startswith("vq") and rest[2:3].isdigit())):
        geo_l, sh_l, cbits, vq_l = {}, 32, None, None'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)

OLD = '''            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_l = int(tok[2:])
            else:
                raise ValueError(f"cannot parse ladder token {tok!r} of {name}")
        return keep_l, sh_l, geo_l, deg_out, cbits'''
NEW = '''            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_l = int(tok[2:])
            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_l = int(tok[2:])
            else:
                raise ValueError(f"cannot parse ladder token {tok!r} of {name}")
        if vq_l is not None and sh_l < 32:
            raise ValueError(f"vq and sh are exclusive in {name}")
        return keep_l, sh_l, geo_l, deg_out, cbits, vq_l'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)

OLD = '''    if not rest:
        return keep, sh_bits, geo, deg_out, None'''
NEW = '''    if not rest:
        return keep, sh_bits, geo, deg_out, None, None'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)
OLD = '''    geo = {a: int(rest[2:]) for a in GEO_SCALARS}
    return keep, sh_bits, geo, deg_out, None'''
NEW = '''    geo = {a: int(rest[2:]) for a in GEO_SCALARS}
    return keep, sh_bits, geo, deg_out, None, None'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)

OLD = '''def spec_rate(name: str, sh_degree: int = 3):'''
NEW = '''def spec_rate(name: str, sh_degree: int = 3, n_stored: int = None):'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)
OLD = '''    keep, sh_bits, geo, deg_out, cbits = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits)'''
NEW = '''    keep, sh_bits, geo, deg_out, cbits, vq_bits = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits,
                         sh_vq_bits=vq_bits, n_stored=n_stored)'''
if OLD in s:
    s = s.replace(OLD, NEW, 1)

# remaining 5-tuple unpackers
s = s.replace("    keep, sh_bits, geo, deg_out, cbits = parse_spec(s)",
              "    keep, sh_bits, geo, deg_out, cbits, _vq = parse_spec(s)")
s = s.replace("                    keep, sh_bits, _geo, _deg, _cb = parse_spec(spec)",
              "                    keep, sh_bits, _geo, _deg, _cb, _vq = parse_spec(spec)")

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok", len(s))
