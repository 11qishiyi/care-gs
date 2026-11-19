# -*- coding: utf-8 -*-
"""Patch train_gs.py: keep GT on CPU, cap densification, add refine-stop fraction."""
import io, os

p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()

# 1) GT on CPU, moved per step
s = s.replace(
    "    gt = torch.from_numpy(imgs).to(device).float() / 255.0          # (N,H,W,3)",
    "    gt = torch.from_numpy(imgs).float() / 255.0                     # (N,H,W,3) stays on CPU")
s = s.replace("        gt_i = gt[i:i + 1]",
              "        gt_i = gt[i:i + 1].to(device)")

# 2) refine stop fraction + densification guard
s = s.replace('    ap.add_argument("--seed", type=int, default=0)',
              '    ap.add_argument("--seed", type=int, default=0)\n'
              '    ap.add_argument("--refine_stop_frac", type=float, default=0.4)\n'
              '    ap.add_argument("--grow_grad2d", type=float, default=0.0004)\n'
              '    ap.add_argument("--max_gaussians", type=int, default=0)')
s = s.replace(
    "        prune_opa=0.005, grow_grad2d=0.0002, grow_scale3d=0.01, grow_scale2d=0.05,\n"
    "        prune_scale3d=0.1, refine_start_iter=500, refine_stop_iter=max(2000, int(0.6 * args.steps)),",
    "        prune_opa=0.005, grow_grad2d=args.grow_grad2d, grow_scale3d=0.01, grow_scale2d=0.05,\n"
    "        prune_scale3d=0.1, refine_start_iter=500,\n"
    "        refine_stop_iter=max(1500, int(args.refine_stop_frac * args.steps)),")

# 3) guard: when the primitive count is already large, stop growing (raise threshold)
s = s.replace(
    "        strategy.step_post_backward(params, optimizers, state, step, info, packed=False)",
    "        if args.max_gaussians and params['means'].shape[0] > args.max_gaussians:\n"
    "            strategy.grow_grad2d = args.grow_grad2d * 1e6   # effectively disable growth\n"
    "        strategy.step_post_backward(params, optimizers, state, step, info, packed=False)")

io.open(p, "w", encoding="utf-8").write(s)
print("patched train_gs.py")
