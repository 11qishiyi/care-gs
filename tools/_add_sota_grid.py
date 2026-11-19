import io

P = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(P, encoding="utf-8").read()

GRID = '''
#: Published-format baselines, expressed in the same grammar so they go through the
#: same quantiser, the same renderer and the same byte meter as our own ladder.  The
#: point is a rate-matched comparison on these assets, not a reproduction of another
#: pipeline: ``g32`` keeps geometry at fp32, which is what a SH-only quantiser ships.
SOTA_VARIANTS = ",".join([
    "clean",
    # the published 8-bit SH quantiser: per-block scale, geometry untouched
    "sh8_g32", "sh4_g32",
    # prune-then-quantise, i.e. the usual compression recipe: delete by importance,
    # then round the surviving coefficients
    "p50_q8_g32", "p50_q4_g32", "p30_q4_g32", "p30_q2_g32",
])
'''

anchor = '''    "pq4-6_c8_o8", "pq4-8_c8_o8",
])
'''
assert anchor in s, "M12 grid tail not found"
s = s.replace(anchor, anchor + GRID, 1)

# register in the dispatch tuple
a2 = ("                                                  M9_VARIANTS, M10_VARIANTS,\n"
      "                                                  M11_VARIANTS, M12_VARIANTS):")
b2 = ("                                                  M9_VARIANTS, M10_VARIANTS,\n"
      "                                                  M11_VARIANTS, M12_VARIANTS,\n"
      "                                                  SOTA_VARIANTS):")
assert a2 in s
s = s.replace(a2, b2, 1)

a3 = ('                "m12": M12_VARIANTS}[preset]')
b3 = ('                "m12": M12_VARIANTS, "sota": SOTA_VARIANTS}[preset]')
assert a3 in s
s = s.replace(a3, b3, 1)

a4 = ('choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9", "m10", "m11", "m12"],')
b4 = ('choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9", "m10", "m11",\n'
      '                             "m12", "sota"],')
assert a4 in s
s = s.replace(a4, b4, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("registered SOTA_VARIANTS (variant-set 'sota')")
