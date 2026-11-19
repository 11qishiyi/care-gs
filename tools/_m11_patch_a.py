"""qfp_rd: per-primitive mode selection (M11).

Every family so far forces one encoding on every primitive.  M9/M10 showed the best
choice depends on the primitive: most SH blocks are near zero (ZERO is free), a few are
well served by a dictionary centre, and the rest need explicit coefficients.  M11 lets
each primitive pick, with a 2-bit mode flag charged to the file:

    mode = argmin_m  D_m + lam * c_m        m in {ZERO, DICT, SCALAR}

``D_m`` is the exact squared error of the 48-coefficient block (not a render proxy) and
``c_m`` is the byte cost of that mode.  ``lam`` is normalised so that ``alpha = 1`` prices
one byte at the asset's mean scalar quantisation error.
"""
import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace(
    """def sh_cols(sh_degree: int) -> int:""",
    """#: mode flags for the per-primitive selector (M11): 2 bits, one code left spare.
MSC_FLAG_BITS = 2
MSC_ZERO, MSC_DICT, MSC_SCALAR = 0, 1, 2


def sh_cols(sh_degree: int) -> int:""", 1)

# byte model
s = s.replace(
    """    cols = sh_cols(sh_degree)
    if sh_rvq is not None:""",
    """    cols = sh_cols(sh_degree)
    if getattr(sh_degree, "msc", None) is not None:  # pragma: no cover - never a degree
        raise AssertionError("sh_degree is an int")
    if sh_rvq is not None:""", 1)

s = s.replace(
    """def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None) -> float:""",
    """def msc_bytes(sh_degree: int, b_dict: int, b_scalar: int, n_stored: int) -> tuple:
    \"\"\"``(c_dict, c_scalar, c_zero)`` in bytes per primitive, codebook included.\"\"\"
    cols = sh_cols(sh_degree)
    c_dict = b_dict / 8.0 + vq_codebook_bytes(b_dict, cols) / float(n_stored)
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    return float(c_dict), float(c_scalar), 0.0


def msc_bytes_per_prim(sh_degree: int, b_dict: int, b_scalar: int,
                       frac=(0.0, 1.0, 0.0), n_stored: int = None) -> float:
    \"\"\"Byte model for a mix: ``frac = (zero, dict, scalar)`` shares.\"\"\"
    total = sum(frac)
    if total <= 0:
        raise ValueError("empty mode mix")
    f = [float(x) / total for x in frac]
    c_dict, c_scalar, c_zero = msc_bytes(sh_degree, b_dict, b_scalar,
                                         n_stored or VQ_NOMINAL_PRIMS)
    return float(MSC_FLAG_BITS / 8.0 + f[0] * c_zero + f[1] * c_dict + f[2] * c_scalar)


def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None) -> float:""", 1)

s = s.replace(
    """    cols = sh_cols(sh_degree)
    if getattr(sh_degree, "msc", None) is not None:  # pragma: no cover - never a degree
        raise AssertionError("sh_degree is an int")
    if sh_rvq is not None:""",
    """    cols = sh_cols(sh_degree)
    if sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),
                                  int(sh_msc["b_scalar"]), sh_msc["frac"], n_stored)
    elif sh_rvq is not None:""", 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("stage 1", len(s))
