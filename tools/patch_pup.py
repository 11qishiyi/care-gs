# -*- coding: utf-8 -*-
"""Add the PUP-style sensitivity baseline to the allocation benchmark."""
import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace("from calib.archive_only import load_archive_only_scene  # noqa: E402",
              "from calib.archive_only import load_archive_only_scene  # noqa: E402\n"
              "from calib.sensitivity import sensitivity_scores  # noqa: E402")

s = s.replace('''    for m, sc_ in base_scores.items():''',
'''    # PUP-style sensitivity (gradient^2 / Fisher diagonal proxy) -- the strong baseline
    try:
        sens = sensitivity_scores(s, c2w, K, gt, cal, W, H, n_views=6, device=args.device)
        base_scores["pup_sens"] = sens.cpu().numpy()
        print("  [pup] sensitivity computed", flush=True)
    except Exception as e:
        print("  [pup] failed:", repr(e)[:120], flush=True)

    for m, sc_ in base_scores.items():''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched: PUP sensitivity baseline")
