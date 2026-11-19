# -*- coding: utf-8 -*-
"""Fix the allocation experiment:
   1. threshold at the MEDIAN of calibration region error (clean ~50%, leaves room to degrade)
   2. clamp pathological splats to a fraction of the scene extent (memory safety)
   3. chunk calibration rendering to bound memory
"""
import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace("        q = torch.quantile(s.scales.reshape(-1).float(), args.clamp_scale)",
              "        ext = float((s.means.max(0).values - s.means.min(0).values).norm())\n"
              "        q = torch.tensor(args.clamp_frac * ext, device=s.scales.device)")

s = s.replace('ap.add_argument("--clamp_scale", type=float, default=0.995)',
              'ap.add_argument("--clamp_frac", type=float, default=0.01,\n'
              '                    help="clamp splat scale to this fraction of the scene extent")')

s = s.replace('''    thr = float(np.quantile(reg_cal.reshape(-1).cpu().numpy(), 1 - args.alpha))''',
              '''    # threshold at the median calibration region error: the clean model then
    # certifies ~50% of calibration regions, leaving room to degrade monotonically.
    thr = float(np.quantile(reg_cal.reshape(-1).cpu().numpy(), args.thr_q))''')

s = s.replace('ap.add_argument("--ratio", type=float, default=0.3)',
              'ap.add_argument("--ratio", type=float, default=0.3)\n'
              '    ap.add_argument("--thr_q", type=float, default=0.5)')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched risk_alloc v2")
