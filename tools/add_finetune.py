# -*- coding: utf-8 -*-
"""Add a fine-tune mode to train_gs.py: optimise an existing PLY without densification.

Route (b) of the confound-breaking experiment needs "compact but converged" models:
take a released checkpoint (3.1M primitives, ~19 dB), prune it to ~200k, then
fine-tune so the surviving primitives re-converge.  Densification must be OFF,
otherwise the model simply grows back to its original size.
"""
import io

p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()

# 1) new CLI flags
s = s.replace('ap.add_argument("--refine_stop_frac", type=float, default=0.4)',
              'ap.add_argument("--refine_stop_frac", type=float, default=0.4)\n'
              '    ap.add_argument("--init_ply", default="",\n'
              '                    help="initialise from this PLY instead of the sparse cloud")\n'
              '    ap.add_argument("--no_densify", action="store_true",\n'
              '                    help="disable densification entirely (pure fine-tuning)")')

# 2) after params are built from the point cloud, optionally replace with the PLY
anchor = "    strategy = DefaultStrategy("
inject = '''    if args.init_ply:
        # fine-tune mode: load an existing model and keep the primitive set fixed
        from calib.gsrender import load_splats as _load
        _s = _load(args.init_ply, device=device)
        with torch.no_grad():
            params["means"] = _s.means.clone()
            params["scales"] = torch.log(_s.scales.clamp_min(1e-8))
            params["quats"] = _s.quats.clone()
            params["opacities"] = torch.logit(_s.opacities.clamp(1e-6, 1 - 1e-6))
            params["sh0"] = _s.sh0.clone()
            params["shN"] = _s.shN.clone()
        optimizers = {k: torch.optim.Adam([params[k]], lr=lrs[k], eps=1e-15) for k in params}
        print(f"[finetune] initialised from {args.init_ply} with {params['means'].shape[0]} primitives",
              flush=True)

'''
assert anchor in s
s = s.replace(anchor, inject + anchor, 1)

# 3) disable densification when asked
s = s.replace("    refine_start_iter=500,\n    refine_stop_iter=max(1500, int(args.refine_stop_frac * args.steps)),",
              "    refine_start_iter=500,\n"
              "    refine_stop_iter=(10**9 if args.no_densify\n"
              "                      else max(1500, int(args.refine_stop_frac * args.steps))),")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s)
print("train_gs.py: --init_ply and --no_densify added")
