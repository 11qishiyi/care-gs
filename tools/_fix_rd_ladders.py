"""Families must be monotone ladders, and the curve is the ladder interpolated at each rate.

Grouping every quantised variant into one "scalar" family mixes good and bad operating
points at the same rate, so the resulting mean is meaningless.  A codec ships a *ladder*:
one knob sweeping from mild to aggressive.  Those ladders are what a matched-rate
comparison should interpolate.
"""
import io
import re

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace('''FAMILY_ORDER = ("prune", "scalar", "vq", "rvq")''',
'''FAMILY_ORDER = ("prune", "scalar", "vq", "rvq")

#: one ladder per family: the knob that the codec actually sweeps.  Variants outside
#: their ladder are still measured, they just are not part of the family curve (they
#: are corners and hybrids, which belong in the tables, not in an RD curve).
LADDERS = {
    "prune": re.compile(r"^p\\d+$"),
    "scalar": re.compile(r"^c\\d+_o8_sh\\d+$"),
    "vq": re.compile(r"^vq\\d+_c8_o8$"),
    "rvq": re.compile(r"^rvq\\d+-\\d+_c8_o8$"),
}''', 1)

s = s.replace('''                fam_map.setdefault(family_of(name), []).append(
                    (float(rate), float(drop), name))''',
'''                fam = family_of(name)
                pat = LADDERS.get(fam)
                if pat is not None and not pat.match(name):
                    continue
                fam_map.setdefault(fam, []).append(
                    (float(rate), float(drop), name))''', 1)

s = s.replace('''        for fam, rows in fam_map.items():
            env = envelope(rows)
            out[scene][fam] = {str(r): interp([(a, b) for a, b, _ in env], r)
                               for r in rates}''',
'''        for fam, rows in fam_map.items():
            out[scene][fam] = {str(r): interp([(a, b) for a, b, _ in rows], r)
                               for r in rates}''', 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
