"""m1_analyse: finish the rvq plumbing (return tuples, spec_rate, call sites)."""
import io

A = r"D:\3dsg_1\experiments\m1_analyse.py"
a = io.open(A, encoding="utf-8").read()

a = a.replace(
    '''        if vq_l is not None and sh_l < 32:
            raise ValueError(f"vq and sh are exclusive in {name}")
        return keep_l, sh_l, geo_l, deg_out, cbits, vq_l''',
    '''        if vq_l is not None and sh_l < 32:
            raise ValueError(f"vq and sh are exclusive in {name}")
        if rvq_l is not None and (vq_l is not None or sh_l < 32):
            raise ValueError(f"rvq excludes both vq and sh in {name}")
        return keep_l, sh_l, geo_l, deg_out, cbits, vq_l, rvq_l''', 1)

a = a.replace(
    '''    if not rest:
        return keep, sh_bits, geo, deg_out, None, None''',
    '''    if not rest:
        return keep, sh_bits, geo, deg_out, None, None, None''', 1)
a = a.replace(
    '''    geo = {a: int(rest[2:]) for a in GEO_SCALARS}
    return keep, sh_bits, geo, deg_out, None, None''',
    '''    geo = {a: int(rest[2:]) for a in GEO_SCALARS}
    return keep, sh_bits, geo, deg_out, None, None, None''', 1)

a = a.replace(
    '''    keep, sh_bits, geo, deg_out, cbits, vq_bits = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits,
                         sh_vq_bits=vq_bits, n_stored=n_stored)''',
    '''    keep, sh_bits, geo, deg_out, cbits, vq_bits, rvq_bits = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits,
                         sh_vq_bits=vq_bits, n_stored=n_stored, sh_rvq=rvq_bits)''', 1)

a = a.replace(
    '''    keep, sh_bits, geo, deg_out, cbits, _vq = parse_spec(s)''',
    '''    keep, sh_bits, geo, deg_out, cbits, _vq, _rvq = parse_spec(s)''', 1)
a = a.replace(
    '''                    keep, sh_bits, _geo, _deg, _cb, _vq = parse_spec(spec)''',
    '''                    keep, sh_bits, _geo, _deg, _cb, _vq, _rvq = parse_spec(spec)''', 1)

io.open(A, "w", encoding="utf-8", newline="\n").write(a)
print("wrote", len(a))
