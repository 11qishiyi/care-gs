# -*- coding: utf-8 -*-
"""Give the trainer a proper 3DGS schedule: means LR decay + separate lr for means."""
import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('    ap.add_argument("--lr_scale", type=float, default=1.0)',
              '    ap.add_argument("--lr_scale", type=float, default=1.0)\n'
              '    ap.add_argument("--means_lr_fix", type=float, default=1.6e-4,\n'
              '                    help="absolute means LR (3DGS default 1.6e-4 * scene_extent)")\n'
              '    ap.add_argument("--no_scene_scale", action="store_true",\n'
              '                    help="do NOT multiply the means LR by the scene radius")\n'
              '    ap.add_argument("--means_lr_final", type=float, default=1.6e-6)')

s = s.replace(
'    lrs = {"means": args.lr_scale * 1.6e-4 * scene_scale, "scales": args.lr_scale * 5e-3, "quats": args.lr_scale * 1e-3,',
'    means_lr = args.means_lr_fix * scene_scale\n'
'    if args.no_scene_scale:\n'
'        means_lr = args.means_lr_fix\n'
'    lrs = {"means": args.lr_scale * means_lr, "scales": args.lr_scale * 5e-3, "quats": args.lr_scale * 1e-3,')

# exponential decay of the means LR, as in the original 3DGS
s = s.replace(
'''        for opt in optimizers.values():
            opt.step()''',
'''        frac = min(1.0, step / max(1, args.steps))
        lr_now = means_lr * (args.means_lr_final / 1.6e-6) if False else \\
            means_lr * (args.means_lr_final / args.means_lr_fix) ** frac
        for g in optimizers["means"].param_groups:
            g["lr"] = args.lr_scale * lr_now
        for opt in optimizers.values():
            opt.step()''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched trainer: means LR decay + no_scene_scale option")
