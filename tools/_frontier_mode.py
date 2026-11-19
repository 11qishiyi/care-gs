import io

P = r"D:\3dsg_1\experiments\frontier.py"
s = io.open(P, encoding="utf-8").read()

a = '''def frontier(rows, budgets=BUDGETS, window=0.02):
    """``{scene: {budget: row}}`` -- the least-loss point *within* the budget.

    Compression results are always stated as "at a rate of at most R", so the candidate set
    for budget ``N`` is every measured point with ``rate <= N*(1+window)``; the ``window``
    only absorbs rounding in the rate arithmetic (it is 2%, not a tolerance for overspending).
    Returning a point that costs *fewer* bytes than the budget is conservative: it proves the
    quality is reachable without spending the budget.
    """
    out = {}
    for scene, rs in rows.items():
        best = {}
        for b in budgets:
            cand = [r for r in rs if r["rate"] <= b * (1.0 + window)]
            if cand:'''
b = '''def frontier(rows, budgets=BUDGETS, window=0.02, mode="at_most"):
    """``{scene: {budget: row}}`` -- the least-loss point that fits the budget.

    Two readings, and they answer different questions:

    ``mode="at_most"`` (default) -- "at a rate of at most R".  A point that costs fewer
    bytes than the budget can satisfy every larger budget too, so this table saturates:
    once a zero-loss point exists at 2.8x, every budget above it reports the same point.
    It is still the honest bound ("this quality is reachable without spending the budget").

    ``mode="at_least"`` -- "the asset must ship at least N times smaller".  The candidate
    set is ``rate >= N*(1-window)``, so the table traces the rate--distortion curve itself
    instead of the running minimum.  This is the reading to quote when the question is
    "what does this pipeline do at 20x".
    """
    out = {}
    for scene, rs in rows.items():
        best = {}
        for b in budgets:
            if mode == "at_least":
                cand = [r for r in rs if r["rate"] >= b * (1.0 - window)]
            else:
                cand = [r for r in rs if r["rate"] <= b * (1.0 + window)]
            if cand:'''
assert a in s
s = s.replace(a, b, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("frontier() learned the at_least reading")
