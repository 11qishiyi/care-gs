# -*- coding: utf-8 -*-
"""Add in-loop PSNR + --no_ssim switch for debugging."""
import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('    ap.add_argument("--max_gaussians", type=int, default=0)',
              '    ap.add_argument("--max_gaussians", type=int, default=0)\n'
              '    ap.add_argument("--no_ssim", action="store_true")\n'
              '    ap.add_argument("--lr_scale", type=float, default=1.0)')

s = s.replace('''        l1 = (rgb - gt_i).abs().mean()
        s = ssim(rgb.permute(0, 3, 1, 2), gt_i.permute(0, 3, 1, 2))
        loss = 0.8 * l1 + 0.2 * (1 - s)''',
'''        l1 = (rgb - gt_i).abs().mean()
        if args.no_ssim:
            loss = l1
        else:
            s = ssim(rgb.permute(0, 3, 1, 2), gt_i.permute(0, 3, 1, 2))
            loss = 0.8 * l1 + 0.2 * (1 - s)''')

s = s.replace('''        if step % 200 == 0:
            print(f"step {step:6d} n={params['means'].shape[0]:7d} "
                  f"loss={loss.item():.4f} l1={l1.item():.4f} "
                  f"{time.time()-t0:.0f}s", flush=True)''',
'''        if step % 200 == 0:
            with torch.no_grad():
                ps = psnr(rgb[0], gt_i[0])
            print(f"step {step:6d} n={params['means'].shape[0]:7d} "
                  f"loss={loss.item():.4f} l1={l1.item():.4f} psnr={ps:.2f} "
                  f"{time.time()-t0:.0f}s", flush=True)''')

s = s.replace('lrs = {"means": 1.6e-4 * scene_scale,',
              'lrs = {"means": args.lr_scale * 1.6e-4 * scene_scale,')
s = s.replace('"scales": 5e-3, "quats": 1e-3,',
              '"scales": args.lr_scale * 5e-3, "quats": args.lr_scale * 1e-3,')
s = s.replace('"opacities": 5e-2, "sh0": 2.5e-3, "shN": 2.5e-3 / 20}',
              '"opacities": args.lr_scale * 5e-2, "sh0": args.lr_scale * 2.5e-3,'
              ' "shN": args.lr_scale * 2.5e-3 / 20}')

io.open(p, "w", encoding="utf-8").write(s)
print("patched")
