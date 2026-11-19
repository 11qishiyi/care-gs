# -*- coding: utf-8 -*-
"""Fix evaluate(): GT lives on CPU now, move slices to device."""
import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
old = '''    for name, idx in groups.items():
        idx = torch.as_tensor(idx, device=device)
        out = render(splats, c2w_all[idx], K_all[idx], W, H)
        ps = [psnr(out["colors"][j], gt[idx[j]]) for j in range(out["colors"].shape[0])]
        scores[name] = float(np.mean(ps))'''
new = '''    for name, idx in groups.items():
        idx_cpu = torch.as_tensor(np.asarray(idx))
        idx = idx_cpu.to(device)
        out = render(splats, c2w_all[idx], K_all[idx], W, H)
        gt_gpu = gt[idx_cpu].to(device)
        ps = [psnr(out["colors"][j], gt_gpu[j]) for j in range(out["colors"].shape[0])]
        scores[name] = float(np.mean(ps))'''
assert old in s, "pattern not found"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("patched evaluate()")
