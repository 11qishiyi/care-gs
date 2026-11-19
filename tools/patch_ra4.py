import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    s = load_splats(args.ply, device=args.device)
    cal, dep = sc["cal_idx"], sc["dep_idx"]''',
'''    s = load_splats(args.ply, device=args.device)
    # self-trained checkpoints can contain a few pathologically large splats that
    # blow up the tile-intersection buffer; clamp to a sane quantile
    if args.clamp_scale > 0:
        q = torch.quantile(s.scales.reshape(-1).float(), args.clamp_scale)
        n_clamped = int((s.scales > q).sum())
        s.scales = s.scales.clamp(max=float(q))
        print(f"[clamp] scales > {float(q):.4f} clamped: {n_clamped} entries", flush=True)
    cal, dep = sc["cal_idx"], sc["dep_idx"]''')
s = s.replace('ap.add_argument("--ratio", type=float, default=0.3)',
              'ap.add_argument("--ratio", type=float, default=0.3)\n'
              '    ap.add_argument("--clamp_scale", type=float, default=0.995)')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added scale clamp")
