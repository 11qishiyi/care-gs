# -*- coding: utf-8 -*-
"""Patch train_gs.py / run_scene.py for the chronological split."""
import io, os, re

ROOT = r"D:\3dsg_1\research\code"

def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = io.open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            print(f"  !! not found in {path}: {old[:60]!r}")
            continue
        s = s.replace(old, new, 1)
    io.open(p, "w", encoding="utf-8").write(s)
    print(f"  patched {path}")

patch("scripts/train_gs.py", [
    ('ap.add_argument("--eval_every", type=int, default=2000)',
     'ap.add_argument("--eval_every", type=int, default=2000)\n'
     '    ap.add_argument("--split", default="chrono")\n'
     '    ap.add_argument("--cal_frac", type=float, default=0.12)\n'
     '    ap.add_argument("--train_frac", type=float, default=0.65)'),
    ('scene = load_colmap_scene(args.data, factor=args.factor)',
     'scene = load_colmap_scene(args.data, factor=args.factor, split=args.split,\n'
     '                              cal_frac=args.cal_frac, train_frac=args.train_frac)'),
    ('''                scene_scale=scene_scale, ply=ply_path, elapsed_s=time.time() - t0,
                train_idx=scene["train_idx"].tolist(), test_idx=scene["test_idx"].tolist())''',
     '''                scene_scale=scene_scale, ply=ply_path, elapsed_s=time.time() - t0,
                split=args.split, train_idx=scene["train_idx"].tolist(),
                cal_idx=scene["cal_idx"].tolist(), dep_idx=scene["dep_idx"].tolist())'''),
    ('''    for name, idx in (("train", scene["train_idx"][:8]), ("test", scene["test_idx"])):
        idx = torch.as_tensor(idx, device=device)
        out = render(splats, c2w_all[idx], K_all[idx], W, H)
        ps = [psnr(out["colors"][j], gt[idx[j]]) for j in range(out["colors"].shape[0])]
        scores[name] = float(np.mean(ps))''',
     '''    groups = {"train": scene["train_idx"][:8]}
    if len(scene.get("cal_idx", [])):
        groups["cal"] = scene["cal_idx"]
    if len(scene.get("dep_idx", [])):
        groups["dep"] = scene["dep_idx"]
    for name, idx in groups.items():
        idx = torch.as_tensor(idx, device=device)
        out = render(splats, c2w_all[idx], K_all[idx], W, H)
        ps = [psnr(out["colors"][j], gt[idx[j]]) for j in range(out["colors"].shape[0])]
        scores[name] = float(np.mean(ps))'''),
    ('''    print(f"[{tag}] PSNR train={scores['train']:.2f} test={scores['test']:.2f}", flush=True)''',
     '''    print(f"[{tag}] PSNR " + " ".join(f"{k}={v:.2f}" for k, v in scores.items()), flush=True)'''),
])

patch("scripts/run_scene.py", [
    ('ap.add_argument("--test_every", type=int, default=4)',
     'ap.add_argument("--test_every", type=int, default=4)\n'
     '    ap.add_argument("--split", default="chrono")\n'
     '    ap.add_argument("--cal_frac", type=float, default=0.12)\n'
     '    ap.add_argument("--train_frac", type=float, default=0.65)'),
    ('scene = load_colmap_scene(args.scene, factor=args.factor, test_every=args.test_every)',
     'scene = load_colmap_scene(args.scene, factor=args.factor, test_every=args.test_every,\n'
     '                              split=args.split, cal_frac=args.cal_frac, train_frac=args.train_frac)'),
    ('''    held = scene["test_idx"]
    cal_idx = held[: args.n_cal]
    dep_idx = held[args.n_cal:]''',
     '''    cal_idx = scene["cal_idx"] if len(scene["cal_idx"]) else scene["test_idx"][: args.n_cal]
    dep_idx = scene["dep_idx"] if len(scene["dep_idx"]) else scene["test_idx"][args.n_cal:]
    held = np.concatenate([cal_idx, dep_idx])'''),
])
print("done")
