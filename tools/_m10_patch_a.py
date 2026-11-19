"""M10: residual vector quantisation (two-stage dictionary) for the SH block.

M9 showed a single 48-dim dictionary beats scalar SH by ~1.5 pp at matched bytes but
misses the 1.0 pp near-lossless gate on 6/8 assets by 0.13-1.10 pp.  The reason is
granularity: one shared centre has to serve a primitive with a large directional
lobe and a primitive that is nearly constant.  Two stages buy the resolution back:
the second codebook is trained on the *residual* of the first, so it concentrates
its centres where the first stage is systematically wrong.
"""
import io
import os

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
A = r"D:\3dsg_1\experiments\m1_analyse.py"
B = r"D:\3dsg_1\experiments\m4_bytes.py"

# ---------------------------------------------------------------- qfp_rd.py ----
s = io.open(Q, encoding="utf-8").read()

s = s.replace(
    '''def vq_codebook_bytes(bits: int, cols: int) -> float:
    """Bytes of a codebook with ``2**bits`` centres of ``cols`` coefficients each."""
    return float((1 << int(bits)) * int(cols) * SH_VQ_CENTROID_BYTES)''',
    '''def vq_codebook_bytes(bits: int, cols: int) -> float:
    """Bytes of a codebook with ``2**bits`` centres of ``cols`` coefficients each."""
    return float((1 << int(bits)) * int(cols) * SH_VQ_CENTROID_BYTES)


def rvq_codebook_bytes(bits1: int, bits2: int, cols: int) -> float:
    """Bytes of a *two-stage* dictionary: the first codebook plus the residual one."""
    return vq_codebook_bytes(bits1, cols) + vq_codebook_bytes(bits2, cols)''', 1)

s = s.replace(
    '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None) -> float:''',
    '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None) -> float:''', 1)

s = s.replace(
    '''    cols = sh_cols(sh_degree)
    if sh_vq_bits is not None:''',
    '''    cols = sh_cols(sh_degree)
    if sh_rvq is not None:
        b1, b2 = int(sh_rvq[0]), int(sh_rvq[1])
        b_sh = (b1 + b2) / 8.0
        b_sh += (rvq_codebook_bytes(b1, b2, cols)
                 / float(n_stored or VQ_NOMINAL_PRIMS))
    elif sh_vq_bits is not None:''', 1)

s = s.replace(
    '''    sh_vq_bits: int = None

    def out_degree''',
    '''    sh_vq_bits: int = None
    #: two-stage dictionary: ``(b1, b2)`` index widths.  The second codebook is trained
    #: on the residual of the first, which is how the granularity problem M9 found is
    #: supposed to be attacked: the same total bits, split between a coarse centre and
    #: a local correction.
    sh_rvq_bits: tuple = None

    def out_degree''', 1)

s = s.replace(
    '''        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None''',
    '''        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None
                    or self.sh_rvq_bits is not None''', 1)

s = s.replace(
    '''        return bytes_per_prim(self.out_degree(sh_degree), self.sh_bits, self.geo,
                              means_cbits=self.means_cluster_bits,
                              sh_vq_bits=self.sh_vq_bits, n_stored=n_stored)''',
    '''        return bytes_per_prim(self.out_degree(sh_degree), self.sh_bits, self.geo,
                              means_cbits=self.means_cluster_bits,
                              sh_vq_bits=self.sh_vq_bits, n_stored=n_stored,
                              sh_rvq=self.sh_rvq_bits)''', 1)

s = s.replace(
    '''        if self.sh_vq_bits is None:
            return 0.0
        return vq_codebook_bytes(self.sh_vq_bits, sh_cols(self.out_degree(sh_degree)))''',
    '''        if self.sh_rvq_bits is not None:
            cols = sh_cols(self.out_degree(sh_degree))
            return rvq_codebook_bytes(int(self.sh_rvq_bits[0]),
                                      int(self.sh_rvq_bits[1]), cols)
        if self.sh_vq_bits is None:
            return 0.0
        return vq_codebook_bytes(self.sh_vq_bits, sh_cols(self.out_degree(sh_degree)))''', 1)

# parse: rvq<a>-<b> token
s = s.replace(
    '''    if ((_rest[:1] in ("m", "c") and _rest[1:2].isdigit())
            or (_rest.startswith("vq") and _rest[2:3].isdigit())):''',
    '''    if ((_rest[:1] in ("m", "c") and _rest[1:2].isdigit())
            or (_rest.startswith("vq") and _rest[2:3].isdigit())
            or (_rest.startswith("rvq") and _rest[3:4].isdigit())):''', 1)

s = s.replace(
    '''            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_bits = int(tok[2:])
                if not 4 <= vq_bits <= 16:
                    raise ValueError(f"codebook index width out of range in {name}")
                seen.add("sh")''',
    '''            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_bits = int(tok[2:])
                if not 4 <= vq_bits <= 16:
                    raise ValueError(f"codebook index width out of range in {name}")
                seen.add("sh")
            elif tok.startswith("rvq") and "-" in tok:
                a, _, b = tok[3:].partition("-")
                if not (a.isdigit() and b.isdigit()):
                    raise ValueError(f"bad residual-codebook token {tok!r} in {name}")
                rvq = (int(a), int(b))
                for x in rvq:
                    if not 2 <= x <= 14:
                        raise ValueError(f"rvq index width out of range in {name}")
                seen.add("sh")''', 1)

s = s.replace(
    '''        geo, sh_bits, seen = {}, FP32_BITS, set()
        cbits = None
        vq_bits = None''',
    '''        geo, sh_bits, seen = {}, FP32_BITS, set()
        cbits = None
        vq_bits = None
        rvq = None''', 1)

s = s.replace(
    '''        if vq_bits is not None and sh_bits < FP32_BITS:
            raise ValueError(f"vq and sh are exclusive in {name}")''',
    '''        if vq_bits is not None and sh_bits < FP32_BITS:
            raise ValueError(f"vq and sh are exclusive in {name}")
        if rvq is not None and (vq_bits is not None or sh_bits < FP32_BITS):
            raise ValueError(f"rvq excludes both vq and sh in {name}")''', 1)

s = s.replace(
    '''        return mk(keep=_keep, sh_bits=sh_bits, geo=geo, means_cluster_bits=cbits,
                  sh_vq_bits=vq_bits)''',
    '''        return mk(keep=_keep, sh_bits=sh_bits, geo=geo, means_cluster_bits=cbits,
                  sh_vq_bits=vq_bits, sh_rvq_bits=rvq)''', 1)

# quantiser
s = s.replace(
    '''def base_degree(sp) -> int:''',
    '''def build_codebook_pair(sp, b1: int, b2: int, deg_out: int, seed: int = 0, iters: int = 15):
    """Two-stage dictionary: the residual codebook is trained on stage-one errors."""
    import torch
    cols = sh_cols(int(deg_out))
    x = _sh_flat(sp)[:, :cols].contiguous()
    C1 = quantise_codebook(_kmeans(x, 1 << int(b1), iters=iters, seed=seed), 8)
    a1 = _vq_assign(x, C1)
    R = x - C1.index_select(0, a1)
    C2 = quantise_codebook(_kmeans(R, 1 << int(b2), iters=iters, seed=seed + 1), 8)
    return (C1, C2)


def quantize_rvq(sp, pair, deg_out: int):
    """Replace the SH block with ``centre1 + centre2``; bands above ``deg_out`` zeroed."""
    import torch
    C1, C2 = pair
    cols = sh_cols(int(deg_out))
    flat = _sh_flat(sp)
    x = flat[:, :cols].contiguous()
    a1 = _vq_assign(x, C1)
    r = x - C1.index_select(0, a1)
    a2 = _vq_assign(r, C2)
    out = flat.clone()
    out[:, :cols] = C1.index_select(0, a1) + C2.index_select(0, a2)
    if cols < int(out.shape[1]):
        out[:, cols:] = 0.0
    _set_sh_flat(sp, out)
    return a1, a2


def base_degree(sp) -> int:''', 1)

s = s.replace(
    '''    out = sp.clone()
    if spec.sh_vq_bits is not None:''',
    '''    out = sp.clone()
    if spec.sh_rvq_bits is not None:
        if state is None:
            raise RuntimeError("residual-quantised SH needs the scene state (codebooks)")
        deg_out = spec.out_degree(int(base_degree(sp)))
        b1, b2 = int(spec.sh_rvq_bits[0]), int(spec.sh_rvq_bits[1])
        quantize_rvq(out, state.codebook_pair(b1, b2, deg_out), deg_out)
    elif spec.sh_vq_bits is not None:''', 1)

s = s.replace(
    '''    def codebook(self, vq_bits: int, deg_out: int):''',
    '''    def codebook_pair(self, b1: int, b2: int, deg_out: int):
        """Two-stage SH dictionary, trained once per asset and reused."""
        key = ("rvq", int(b1), int(b2), int(deg_out))
        if key not in self.cache:
            self.cache[key] = build_codebook_pair(self.base, b1, b2, deg_out)
        return self.cache[key]

    def codebook(self, vq_bits: int, deg_out: int):''', 1)

# variant grid
s = s.replace(
    '''def _variants(args) -> list:''',
    '''#: M10 grid: two-stage dictionary.  M9 left the single-dictionary curve 0.13-1.10 pp
#: short of the 1 pp near-lossless gate at 18-20x; the diagnosis was granularity, not
#: representation, so the next lever is the *split* of the same bits between a coarse
#: centre and a residual centre.
M10_VARIANTS = ",".join([
    "clean",
    # scalar and single-stage anchors at the same bytes
    "c8_o8_sh2", "c8_o8_sh3", "vq10_c8_o8", "vq12_c8_o8",
    # residual ladder at 8, 10, 12 and 14 total index bits
    "rvq6-2_c8_o8", "rvq8-2_c8_o8", "rvq8-4_c8_o8", "rvq10-2_c8_o8",
    "rvq10-4_c8_o8", "rvq8-6_c8_o8", "rvq12-4_c8_o8", "rvq10-6_c8_o8",
    # is the residual codebook still worth it when positions get cheaper?
    "rvq8-4_c10_o8", "rvq10-4_c10_o8",
    # hybrid at the low-rate corner
    "p30_rvq10-4_c8_o8",
])


def _variants(args) -> list:''', 1)

s = s.replace(
    '''                                                  M7_VARIANTS, M8_VARIANTS,
                                                  M9_VARIANTS):''',
    '''                                                  M7_VARIANTS, M8_VARIANTS,
                                                  M9_VARIANTS, M10_VARIANTS):''', 1)

s = s.replace(
    '''                "m7": M7_VARIANTS, "m8": M8_VARIANTS, "m9": M9_VARIANTS}[preset]''',
    '''                "m7": M7_VARIANTS, "m8": M8_VARIANTS, "m9": M9_VARIANTS,
                "m10": M10_VARIANTS}[preset]''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("qfp_rd patched", len(s))

# ------------------------------------------------------------ m1_analyse.py ----
a = io.open(A, encoding="utf-8").read()

a = a.replace(
    '''def vq_codebook_bytes(bits: int, cols: int) -> float:''',
    '''def rvq_codebook_bytes(bits1: int, bits2: int, cols: int) -> float:
    """Two-stage dictionary: both codebooks are part of the file."""
    return vq_codebook_bytes(bits1, cols) + vq_codebook_bytes(bits2, cols)


def vq_codebook_bytes(bits: int, cols: int) -> float:''', 1)

io.open(A, "w", encoding="utf-8", newline="\n").write(a)
print("m1_analyse part 1", len(a))
