import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()

# 1. encode() takes the offset depth as a parameter
s = s.replace(
    "           bits_total: int = 48, level: int = 12, path: str = None, pos_bits: int = 10,\n"
    "           attr_bits: int = 8, dc_bits: int = 3) -> tuple:",
    "           bits_total: int = 48, level: int = 12, path: str = None, pos_bits: int = 10,\n"
    "           attr_bits: int = 8, dc_bits: int = 3, offset_bits: int = OFFSET_BITS) -> tuple:",
)
s = s.replace(
    '    quantum = voxel / float(1 << OFFSET_BITS)\n'
    '    ocode = np.clip(np.round((off + 0.5 * voxel) / quantum), 0, (1 << OFFSET_BITS) - 1).astype(np.int64)',
    '    quantum = voxel / float(1 << int(offset_bits))\n'
    '    ocode = np.clip(np.round((off + 0.5 * voxel) / quantum), 0,\n'
    '                    (1 << int(offset_bits)) - 1).astype(np.int64)',
)
s = s.replace('    st["a_off"] = M.pack_bits(ocode.reshape(-1), OFFSET_BITS)',
              '    st["a_off"] = M.pack_bits(ocode.reshape(-1), int(offset_bits))')
s = s.replace('"offset_bits": OFFSET_BITS,', '"offset_bits": int(offset_bits),')

# 2. the CLI exposes it
s = s.replace('    ap.add_argument("--dc-bits", type=int, default=3)',
              '    ap.add_argument("--dc-bits", type=int, default=3)\n'
              '    ap.add_argument("--offset-bits", type=int, default=OFFSET_BITS)')
s = s.replace('pos_bits=a.pos_bits, attr_bits=a.attr_bits, dc_bits=a.dc_bits, path=a.out)',
              'pos_bits=a.pos_bits, attr_bits=a.attr_bits, dc_bits=a.dc_bits,\n'
              '                         offset_bits=a.offset_bits, path=a.out)')
s = s.replace('"dc_bits": a.dc_bits,', '"dc_bits": a.dc_bits, "offset_bits": a.offset_bits,')

io.open(p, "w", encoding="utf-8").write(s)
print("patched offset-bits")
