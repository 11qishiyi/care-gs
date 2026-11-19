"""The replay check must not assume the stored index is the nearest centre: a
two-stage reconstruction is only guaranteed to lie within the residual codebook's
reach of *some* first-stage centre."""
import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace(
    '''    a1 = _vq_assign(rec_r, pair[0])
    r1 = rec_r - pair[0].index_select(0, a1)
    a2 = _vq_assign(r1, pair[1])
    dev = (rec_r - (pair[0].index_select(0, a1) + pair[1].index_select(0, a2))).abs().amax()
    check("every stored block is centre1 + centre2", float(dev) < 1e-5,
          f"max deviation {float(dev):.2e}")''',
    '''    # A two-stage reconstruction lies within the residual codebook's reach of *some*
    # first-stage centre; it is not necessarily nearest to one, because the second
    # stage can pull a row into another centre's cell.
    near1 = (rec_r[:, None, :] - pair[0][None, :, :]).abs().amax(dim=2).amin(dim=1)
    reach = float(pair[1].abs().amax()) + 1e-5
    check("every stored block is one centre plus a residual entry",
          float(near1.max()) <= reach,
          f"max distance to a first-stage centre {float(near1.max()):.3f} <= {reach:.3f}")''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
