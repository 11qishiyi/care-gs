"""qfp_rd stage 2: spec field, parser, selector, realise, variant grid."""
import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

# ---- QSpec field -----------------------------------------------------------
s = s.replace(
    """    sh_rvq_bits: tuple = None

    def out_degree""",
    """    sh_rvq_bits: tuple = None
    #: per-primitive mode selection ``{"b_dict", "b_scalar", "alpha"}``; ``frac`` is
    #: filled in at encode time because the mode mix is data dependent.
    sh_msc: dict = None
    msc_frac: tuple = None

    def out_degree""", 1)

s = s.replace(
    """        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None
                    or self.sh_rvq_bits is not None""",
    """        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None
                    or self.sh_rvq_bits is not None or self.sh_msc is not None""", 1)

s = s.replace(
    """                              sh_vq_bits=self.sh_vq_bits, n_stored=n_stored,
                              sh_rvq=self.sh_rvq_bits)""",
    """                              sh_vq_bits=self.sh_vq_bits, n_stored=n_stored,
                              sh_rvq=self.sh_rvq_bits,
                              sh_msc=(None if self.sh_msc is None else
                                      dict(self.sh_msc,
                                           frac=self.msc_frac or (0.0, 1.0, 0.0))))""", 1)

s = s.replace(
    """        if self.sh_rvq_bits is not None:
            cols = sh_cols(self.out_degree(sh_degree))""",
    """        if self.sh_msc is not None:
            cols = sh_cols(self.out_degree(sh_degree))
            return (vq_codebook_bytes(int(self.sh_msc["b_dict"]), cols)
                    if self.msc_frac is None else 0.0)
        if self.sh_rvq_bits is not None:
            cols = sh_cols(self.out_degree(sh_degree))""", 1)

# ---- parser ---------------------------------------------------------------
s = s.replace(
    """    if ((_rest[:1] in ("m", "c") and _rest[1:2].isdigit())
            or (_rest.startswith("vq") and _rest[2:3].isdigit())
            or (_rest.startswith("rvq") and _rest[3:4].isdigit())):""",
    """    if ((_rest[:1] in ("m", "c") and _rest[1:2].isdigit())
            or (_rest.startswith("vq") and _rest[2:3].isdigit())
            or (_rest.startswith("rvq") and _rest[3:4].isdigit())
            or (_rest.startswith("msc") and "-" in _rest)):""", 1)

s = s.replace(
    """        vq_bits = None
        rvq = None""",
    """        vq_bits = None
        rvq = None
        msc = None""", 1)

s = s.replace(
    """            elif tok.startswith("rvq") and "-" in tok:""",
    """            elif tok.startswith("msc") and "-" in tok:
                parts = tok[3:].split("-")
                if len(parts) != 3 or not all(p for p in parts):
                    raise ValueError(f"bad msc token {tok!r} in {name}")
                b_d, b_s, a = int(parts[0]), int(parts[1]), parts[2]
                if not (a[0] == "a" and a[1:].isdigit()):
                    raise ValueError(f"bad msc alpha {a!r} in {name}")
                if not 6 <= b_d <= 16 or not 2 <= b_s <= 8:
                    raise ValueError(f"msc widths out of range in {name}")
                msc = {"b_dict": b_d, "b_scalar": b_s, "alpha": int(a[1:])}
                seen.add("sh")
            elif tok.startswith("rvq") and "-" in tok:""", 1)

s = s.replace(
    """        if rvq is not None and (vq_bits is not None or sh_bits < FP32_BITS):
            raise ValueError(f"rvq excludes both vq and sh in {name}")""",
    """        if rvq is not None and (vq_bits is not None or sh_bits < FP32_BITS):
            raise ValueError(f"rvq excludes both vq and sh in {name}")
        if msc is not None and (vq_bits is not None or rvq is not None
                                or sh_bits < FP32_BITS):
            raise ValueError(f"msc excludes vq/rvq/sh in {name}")""", 1)

s = s.replace(
    """                  sh_vq_bits=vq_bits, sh_rvq_bits=rvq)""",
    """                  sh_vq_bits=vq_bits, sh_rvq_bits=rvq, sh_msc=msc)""", 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("stage 2", len(s))
