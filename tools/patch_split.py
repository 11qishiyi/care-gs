# -*- coding: utf-8 -*-
"""Add an interleaved calibration/deployment split.

Diagnosis: with a chronological (block) split the deployment views are
systematically *easier* than the calibration views (mean residual ratio 0.45-0.91
across four scenes), so a pooled conformal quantile over-covers and hides edit
damage.  Exchangeability of calibration and deployment samples is the assumption
conformal prediction needs; a chronological block violates it.  An interleaved
split restores it.  This flag lets us test exactly that.
"""
import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()

old = '''        cal = list(sc["cal_idx"])[: args.max_views]
        dep = list(sc["dep_idx"])[: args.max_views]'''
new = '''        if args.split == "interleaved":
            allv = sorted(set(list(sc["cal_idx"]) + list(sc["dep_idx"])))
            cal = allv[0::2][: args.max_views]
            dep = allv[1::2][: args.max_views]
        else:
            cal = list(sc["cal_idx"])[: args.max_views]
            dep = list(sc["dep_idx"])[: args.max_views]'''
assert old in s
s = s.replace(old, new)
s = s.replace('ap.add_argument("--cal_mode", default="pooled"',
              'ap.add_argument("--split", default="interleaved", choices=["block", "interleaved"])\n'
              '    ap.add_argument("--cal_mode", default="pooled"')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added interleaved split")
