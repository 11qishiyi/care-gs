# -*- coding: utf-8 -*-
"""Conceptual fix: model edits (prune/quantise/truncate) do NOT stale the ground
truth -- only *content* edits do.  Add a content-deletion edit."""
import io
p = r"D:\3dsg_1\research\code\scripts\run_scene2.py"
s = io.open(p, encoding="utf-8").read()

# 1) pruning is a model edit: the images still depict the scene
s = s.replace('''    sub = splats.subset(torch.nonzero(removed).flatten())   # what disappeared
    return splats.subset(keep), dict(kind="prune", keep_frac=keep_frac, kept=int(k),
                                     total=splats.n, taint_splats=sub)''',
'''    return splats.subset(keep), dict(kind="prune", keep_frac=keep_frac, kept=int(k),
                                     total=splats.n, taint_splats=None)''')
s = s.replace('''    sub = splats.subset(torch.nonzero(removed).flatten())
    return splats.subset(keep), dict(kind="prune_importance", keep_frac=keep_frac,
                                     kept=int(k), total=splats.n, taint_splats=sub)''',
'''    return splats.subset(keep), dict(kind="prune_importance", keep_frac=keep_frac,
                                     kept=int(k), total=splats.n, taint_splats=None)''')

# 2) content deletion: an object disappears -> GT is stale where it was visible
s = s.replace('''def edit_translate_box(''', '''def edit_delete_box(splats: Splats, frac: float):
    """Remove a spatial box of primitives (simulates an object being removed)."""
    m = splats.means
    lo = torch.quantile(m, 0.5 - frac / 2, dim=0)
    hi = torch.quantile(m, 0.5 + frac / 2, dim=0)
    sel = ((m >= lo) & (m <= hi)).all(dim=1)
    ids = torch.nonzero(sel).flatten()
    keep = torch.nonzero(~sel).flatten()
    sub = splats.subset(ids)
    return splats.subset(keep), dict(kind="delete_box", frac_sel=float(frac),
                                     moved=int(ids.numel()), total=splats.n,
                                     taint_splats=sub)


def edit_translate_box(''')

s = s.replace('''        "move10": lambda s: edit_translate_box(s, 0.1),
        "move30": lambda s: edit_translate_box(s, 0.3),''',
'''        "move10": lambda s: edit_translate_box(s, 0.1),
        "move30": lambda s: edit_translate_box(s, 0.3),
        "delete10": lambda s: edit_delete_box(s, 0.1),
        "delete20": lambda s: edit_delete_box(s, 0.2),''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched run_scene2 v2.1")
