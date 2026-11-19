"""Move `_group_grad_norm` out of `main()` and to module scope in train_gs.py.

It was written inline while wiring M36's rate term, which works (the def runs before the training loop)
but leaves a function definition in the middle of a 250-line body.  A script rather than `python -c`
because PowerShell eats the quoting, which is the trap that has cost this project several rounds already.
"""
import io

PATH = "research/code/scripts/train_gs.py"
s = io.open(PATH, encoding="utf-8").read()

helper = '''

def _group_grad_norm(params, groups) -> float:
    """L2 norm of the gradients of ``groups`` (used once, to calibrate lambda before it is frozen)."""
    total = 0.0
    for g in groups:
        if g in params and params[g].grad is not None:
            total += float((params[g].grad.detach() ** 2).sum())
    return total ** 0.5

'''
assert s.count("\n\ndef _group_grad_norm") == 1, f"helper found {s.count(chr(10)+chr(10)+'def _group_grad_norm')} times"
s = s.replace(helper, "\n")
anchor = "SH_C0 = 0.28209479177387814\n"
assert anchor in s
s = s.replace(anchor, anchor + helper)
io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)
print("moved _group_grad_norm to module scope")
