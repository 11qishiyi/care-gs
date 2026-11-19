# -*- coding: utf-8 -*-
"""Use all views (train+test) in the audit, with a robust filter for mis-mapped ones."""
import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace("from calib.archive_only import load_archive_only_scene  # noqa: E402",
              "from calib.archive_only import load_archive_only_scene  # noqa: E402\n"
              "from calib.archive_all import load_archive_all_scene  # noqa: E402")

old = '''        if args.split == "interleaved":'''
new = '''        if args.use_all_views:
            allv = np.arange(len(sc["image_paths"]))
            cal = list(allv[0::2])
            dep = list(allv[1::2])
        elif args.split == "interleaved":'''
assert old in s
s = s.replace(old, new)

# robust filter: drop views whose median residual is far above the pack (mis-mapped GT)
s = s.replace('''        print(f"\\n=== {scene}: {splats.n} primitives, cal={len(cal)} dep={len(dep)} ===", flush=True)''',
'''        cal = list(cal)[: args.max_views]
        dep = list(dep)[: args.max_views]
        if args.use_all_views:
            r_chk = residuals(splats, c2w, K, gt, list(cal) + list(dep), W, H, args.device)
            med = r_chk.reshape(r_chk.shape[0], -1).mean(1).cpu().numpy()
            thr_med = 3.0 * float(np.median(med))
            good = med <= thr_med
            allv_l = list(cal) + list(dep)
            cal = [allv_l[i] for i in range(len(cal)) if good[i]]
            dep = [allv_l[i] for i in range(len(cal), len(allv_l)) if good[i]]
            print(f"  [filter] dropped {int((~good).sum())} outlier views "
                  f"(>{thr_med:.3f})", flush=True)
        print(f"\\n=== {scene}: {splats.n} primitives, cal={len(cal)} dep={len(dep)} ===", flush=True)''')

s = s.replace('ap.add_argument("--split", default="interleaved", choices=["block", "interleaved"])',
              'ap.add_argument("--split", default="interleaved", choices=["block", "interleaved"])\n'
              '    ap.add_argument("--use_all_views", action="store_true")')
s = s.replace('''        sc = load_archive_only_scene(args.archive, scene, factor=args.factor,
                                     cal_frac=args.cal_frac)''',
'''        if args.use_all_views:
            sc = load_archive_all_scene(args.archive, scene, factor=args.factor,
                                        cal_frac=args.cal_frac)
        else:
            sc = load_archive_only_scene(args.archive, scene, factor=args.factor,
                                         cal_frac=args.cal_frac)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added all-views mode with outlier filter")
