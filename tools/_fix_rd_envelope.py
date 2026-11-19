"""A family's curve must be its *frontier*, not the mean over every point it contains.

Interpolating raw points lets a bad member (e.g. an aggressive 12-bit geometry grid)
define the curve at a rate where a better sibling exists; an encoder would ship the
better sibling.  So each family is reduced to its lower envelope first, then
interpolated.
"""
import io

P = r"D:\3dsg_1\experiments\rd_curves.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace('''def collect(docs):''',
'''def envelope(points):
    """Lower envelope: walk rates upwards, keep a point only when it improves the loss.

    ``points`` is ``[(rate, value, name), ...]``; the result is monotone in rate, which
    is what makes interpolation between its knots meaningful (a family's RD curve is
    the best member at each rate, not the average of all of them).
    """
    pts = sorted((float(r), float(v), n) for r, v, n in points
                 if r is not None and v is not None)
    kept, best = [], None
    for r, v, n in pts:
        if best is None or v < best - 1e-12:
            kept.append((r, v, n))
            best = v
    return kept


def collect(docs):''', 1)

s = s.replace('''        for fam, rows in fam_map.items():
            pts = [(r, d) for r, d, _ in rows]
            out[scene][fam] = {str(r): interp(pts, r) for r in rates}''',
'''        for fam, rows in fam_map.items():
            env = envelope(rows)
            out[scene][fam] = {str(r): interp([(a, b) for a, b, _ in env], r)
                               for r in rates}''', 1)

# selftest: an interior bad point must not define the curve
s = s.replace('''    tab = best_coding(means, [17.0, 18.7, 20.0], 3)''',
'''    bad = envelope([(9.0, -0.5, "good"), (12.0, -9.0, "bad"), (15.0, -0.9, "worse")])
    check("the envelope drops dominated points",
          [n for _, _, n in bad] == ["good"], str([n for _, _, n in bad]))

    tab = best_coding(means, [17.0, 18.7, 20.0], 3)''', 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
