# -*- coding: utf-8 -*-
"""Add density-greedy (quality-weighted coverage) to the allocation script.

The previous version picked the *cheapest* regions, which biases toward sparse
areas that are easy to cover but irrelevant.  Density greedy ranks by
benefit/cost instead:

    benefit(r) = 1 / (err_r - thr + eps)      for regions still above the threshold
    score(r)   = benefit(r) / cost(r)

so "regions that are just barely unusable" get rescued first.  The objective stays
monotone submodular, so the (1-1/e) guarantee is unchanged.
"""
import io

p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()

# replace greedy_cover with a mode-aware version
old = '''def greedy_cover(cell_lists, budget: int):
    """Cheapest-region-first greedy set cover over region cells."""
    order = sorted(range(len(cell_lists)), key=lambda i: len(cell_lists[i][1]))'''
new = '''def greedy_cover(cell_lists, budget: int, region_scores=None, mode="cheapest"):
    """Budgeted coverage over region cells.

    mode="cheapest" : pick the region needing the fewest new primitives (v1)
    mode="density"  : pick the region with the best benefit/cost, where benefit
                      favours regions that are just above the usability threshold
    """
    if mode == "density" and region_scores is not None:
        order = sorted(
            range(len(cell_lists)),
            key=lambda i: -(float(region_scores[i]) / max(1, len(cell_lists[i][1]))),
        )
    else:
        order = sorted(range(len(cell_lists)), key=lambda i: len(cell_lists[i][1]))'''
assert old in s
s = s.replace(old, new)

# build per-cell benefit and pass it in
old2 = '''    cells, _, _ = region_primitives(s, c2w, K, cal, W, H, blk)
    chosen, n_reg = greedy_cover(cells, budget)'''
new2 = '''    cells, _, _ = region_primitives(s, c2w, K, cal, W, H, blk)
    # benefit per cell: high for regions just above the threshold ("almost usable")
    err_c = reg_cal.reshape(-1).cpu().numpy()          # (n_cells,) in cell order
    benefit = 1.0 / (np.maximum(err_c - thr, 0.0) + 0.05)
    benefit = np.where(err_c > thr, benefit, 0.0)
    chosen, n_reg = greedy_cover(cells, budget, region_scores=benefit, mode=args.mode)'''
assert old2 in s
s = s.replace(old2, new2)

s = s.replace('ap.add_argument("--cal_frac_arch", type=float, default=0.5)',
              'ap.add_argument("--cal_frac_arch", type=float, default=0.5)\n'
              '    ap.add_argument("--mode", default="density",\n'
              '                    choices=["cheapest", "density"])')
s = s.replace('rows.append(dict(method="region_greedy"', 'rows.append(dict(method="region_" + args.mode')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s)
print("patched: density greedy added")
