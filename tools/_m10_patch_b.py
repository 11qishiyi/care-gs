"""m1_analyse: mirror the two-stage (rvq) byte model and parser."""
import io

A = r"D:\3dsg_1\experiments\m1_analyse.py"
a = io.open(A, encoding="utf-8").read()

a = a.replace(
    '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None) -> float:''',
    '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None) -> float:''', 1)

a = a.replace(
    '''    cols = sh_cols(sh_degree)
    if sh_vq_bits is not None:''',
    '''    cols = sh_cols(sh_degree)
    if sh_rvq is not None:
        b1, b2 = int(sh_rvq[0]), int(sh_rvq[1])
        b_sh = (b1 + b2) / 8.0 + rvq_codebook_bytes(b1, b2, cols) / float(
            n_stored or VQ_NOMINAL_PRIMS)
    elif sh_vq_bits is not None:''', 1)

# parser: accept rvq and return a 7-tuple
a = a.replace(
    '''    if s == "clean":
        return 1.0, 32, {}, None, None, None''',
    '''    if s == "clean":
        return 1.0, 32, {}, None, None, None, None''', 1)
a = a.replace(
    '''                return 1.0, 32, {attr: int(body[len(alias):])}, None, None, None''',
    '''                return 1.0, 32, {attr: int(body[len(alias):])}, None, None, None, None''', 1)
a = a.replace(
    '''        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None, None''',
    '''        return 1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None, None, None, None''', 1)

a = a.replace(
    '''    if ((rest[:1] in ("m", "c") and rest[1:2].isdigit())
            or (rest.startswith("vq") and rest[2:3].isdigit())):
        geo_l, sh_l, cbits, vq_l = {}, 32, None, None''',
    '''    if ((rest[:1] in ("m", "c") and rest[1:2].isdigit())
            or (rest.startswith("vq") and rest[2:3].isdigit())
            or (rest.startswith("rvq") and rest[3:4].isdigit())):
        geo_l, sh_l, cbits, vq_l, rvq_l = {}, 32, None, None, None''', 1)

a = a.replace(
    '''            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_l = int(tok[2:])''',
    '''            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_l = int(tok[2:])
            elif tok.startswith("rvq") and "-" in tok:
                p, _, q = tok[3:].partition("-")
                rvq_l = (int(p), int(q))''', 1)

io.open(A, "w", encoding="utf-8", newline="\n").write(a)
print("wrote", len(a))
