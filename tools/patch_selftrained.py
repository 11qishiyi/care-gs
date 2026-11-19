# -*- coding: utf-8 -*-
"""Let the certificate audit run on self-trained scenes (COLMAP layouts)."""
import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("from calib.archive_all import load_archive_all_scene  # noqa: E402",
              "from calib.archive_all import load_archive_all_scene  # noqa: E402\n"
              "from calib.colmap_io import load_colmap_scene  # noqa: E402")
s = s.replace('''        if args.use_all_views:''',
'''        if args.self_trained:
            # a model we trained ourselves on a standard COLMAP scene: calibration and
            # deployment views are the held-out slice (never seen during training)
            raw = load_colmap_scene(args.scene_dir, factor=args.factor, split="chrono",
                                    cal_frac=0.15, train_frac=0.65)
            pool = sorted(set(list(raw["cal_idx"]) + list(raw["dep_idx"])))
            sc = dict(camtoworlds=raw["camtoworlds"], Ks=raw["Ks"],
                      image_paths=raw["image_paths"], width=raw["width"], height=raw["height"],
                      train_idx=raw["train_idx"], names=raw.get("names", []),
                      cal_idx=np.array(pool[0::2]), dep_idx=np.array(pool[1::2]))
        elif args.use_all_views:''')
s = s.replace('ap.add_argument("--use_all_views", action="store_true")',
              'ap.add_argument("--use_all_views", action="store_true")\n'
              '    ap.add_argument("--self_trained", action="store_true")\n'
              '    ap.add_argument("--scene_dir", default="")')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added self-trained scene mode")
