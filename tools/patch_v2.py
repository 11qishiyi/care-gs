# -*- coding: utf-8 -*-
import io
p = r"D:\3dsg_1\research\code\scripts\run_scene2.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
"        recal, _ = evaluate(s2, c2w, K, gt, cal_idx, dep_idx, W, H, args.block, args.alpha)",
"        recal, _ = evaluate(s2, c2w, K, gt, cal_idx, dep_idx, W, H, args.block, args.alpha,\n"
"                            taint_cal=tc)")
s = s.replace(
'''        print(f"[{e}] stale={cov_stale:.3f} recal={recal['naive']['cov']:.3f} "
              f"taint_masked={masked['cov']:.3f} (kept {masked['kept_frac']:.2f}) "
              f"taint_frac={out['states'][e]['taint_frac']}", flush=True)''',
'''        m_txt = (f"{masked['cov']:.3f} (kept {masked['kept_frac']:.2f})"
                 if masked else "-")
        print(f"[{e}] stale={cov_stale:.3f} recal={recal['naive']['cov']:.3f} "
              f"taint_masked={m_txt} taint_frac={out['states'][e]['taint_frac']}", flush=True)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched run_scene2")
