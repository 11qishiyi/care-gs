"""Add the cluster-relative position byte model to m1_analyse.py (idempotent)."""
import io

P = r"D:\3dsg_1\experiments\m1_analyse.py"
s = io.open(P, encoding="utf-8").read()
orig = s

CLUSTER_CONST = 'CLUSTER_SIZE = 256\nCLUSTER_HEADER_BYTES = 24.0\nCLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)'
if "CLUSTER_HEADER_PER_PRIM" not in s:
    s = s.replace(
        'GEO_SCALARS = {"means": 3, "scales": 3, "quats": 4, "opacities": 1}\nSH_SCALE_BYTES = 2',
        'GEO_SCALARS = {"means": 3, "scales": 3, "quats": 4, "opacities": 1}\n'
        'SH_SCALE_BYTES = 2\n'
        '#: cluster-relative position headers: mirror of ``qfp_rd.CLUSTER_*``\n'
        + CLUSTER_CONST,
        1,
    )

OLD_BPP = '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict) -> float:
    """Literal bytes per kept primitive: ``11*b_geo/8 + 3K*b_sh/8 (+2)``."""
    cols = sh_cols(sh_degree)
    b_sh = cols * 4.0 if sh_bits >= 32 else cols * sh_bits / 8.0 + SH_SCALE_BYTES
    b_geo = sum(n * int(geo.get(a, 32)) / 8.0 for a, n in GEO_SCALARS.items())
    return float(b_geo + b_sh)'''

NEW_BPP = '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None) -> float:
    """Literal bytes per kept primitive: ``11*b_geo/8 + 3K*b_sh/8 (+2)``.

    ``means_cbits`` replaces the three position components by cluster-relative
    offsets at that width, which also pays one 24-byte header per 256 primitives.
    """
    cols = sh_cols(sh_degree)
    b_sh = cols * 4.0 if sh_bits >= 32 else cols * sh_bits / 8.0 + SH_SCALE_BYTES
    b_geo = 0.0
    for a, n in GEO_SCALARS.items():
        if a == "means" and means_cbits is not None:
            b_geo += 3 * int(means_cbits) / 8.0 + CLUSTER_HEADER_PER_PRIM
            continue
        b_geo += n * int(geo.get(a, 32)) / 8.0
    return float(b_geo + b_sh)'''

if "means_cbits: int = None" not in s:
    assert OLD_BPP in s, "bytes_per_prim body not found"
    s = s.replace(OLD_BPP, NEW_BPP, 1)

# parse_spec: return a 5-tuple (keep, sh_bits, geo, deg_out, cbits) and accept c<bits>
if "def parse_spec(name: str):\n    \"\"\"``(keep, sh_bits, geo, sh_degree_out)``" in s:
    s = s.replace(
        '"""``(keep, sh_bits, geo, sh_degree_out)`` for one variant name.',
        '"""``(keep, sh_bits, geo, sh_degree_out, means_cbits)`` for one variant name.',
        1,
    )

s = s.replace("        return 1.0, 32, {}, None\n    deg_out = None",
              "        return 1.0, 32, {}, None, None\n    deg_out = None", 1)
s = s.replace('                return 1.0, 32, {attr: int(body[len(alias):])}, None',
              '                return 1.0, 32, {attr: int(body[len(alias):])}, None, None', 1)
s = s.replace('        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None',
              '        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None', 1)

OLD_LADDER = '''    if rest[:1] == "m" and rest[1:2].isdigit():
        geo_l, sh_l = {}, 32
        for tok in rest.split("_"):
            if not tok:
                continue
            if tok[0] == "m" and tok[1:].isdigit():
                geo_l["means"] = int(tok[1:])
            elif tok[0] == "o" and tok[1:].isdigit():
                for a in ("scales", "quats", "opacities"):
                    geo_l[a] = int(tok[1:])
            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_l = int(tok[2:])
            else:
                raise ValueError(f"cannot parse ladder token {tok!r} of {name}")
        return keep_l, sh_l, geo_l, deg_out'''

NEW_LADDER = '''    if rest[:1] in ("m", "c") and rest[1:2].isdigit():
        geo_l, sh_l, cbits = {}, 32, None
        for tok in rest.split("_"):
            if not tok:
                continue
            if tok[0] == "m" and tok[1:].isdigit():
                geo_l["means"] = int(tok[1:])
            elif tok[0] == "c" and tok[1:].isdigit():
                cbits = int(tok[1:])
                geo_l.pop("means", None)
            elif tok[0] == "o" and tok[1:].isdigit():
                for a in ("scales", "quats", "opacities"):
                    geo_l[a] = int(tok[1:])
            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_l = int(tok[2:])
            else:
                raise ValueError(f"cannot parse ladder token {tok!r} of {name}")
        return keep_l, sh_l, geo_l, deg_out, cbits'''

if "cbits = int(tok[1:])" not in s:
    assert OLD_LADDER in s, "ladder block not found"
    s = s.replace(OLD_LADDER, NEW_LADDER, 1)

s = s.replace("""    if not rest:
        return keep, sh_bits, geo, deg_out""",
              """    if not rest:
        return keep, sh_bits, geo, deg_out, None""", 1)
s = s.replace("""    geo = {a: int(rest[2:]) for a in GEO_SCALARS}
    return keep, sh_bits, geo, deg_out""",
              """    geo = {a: int(rest[2:]) for a in GEO_SCALARS}
    return keep, sh_bits, geo, deg_out, None""", 1)

s = s.replace('''    keep, sh_bits, geo, deg_out = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo)''',
              '''    keep, sh_bits, geo, deg_out, cbits = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits)''', 1)

s = s.replace("            keep, sh_bits, _geo, _deg = parse_spec(spec)",
              "            keep, sh_bits, _geo, _deg, _cb = parse_spec(spec)", 1)

if s == orig:
    print("nothing changed")
else:
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("patched")
