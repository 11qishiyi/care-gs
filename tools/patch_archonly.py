# -*- coding: utf-8 -*-
"""Add archive-only scene support to risk_alloc.py."""
import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("from calib.llff import load_llff_scene  # noqa: E402",
              "from calib.llff import load_llff_scene  # noqa: E402\n"
              "from calib.archive_only import load_archive_only_scene  # noqa: E402")
s = s.replace('ap.add_argument("--out3dgs", default="")',
              'ap.add_argument("--out3dgs", default="")\n'
              '    ap.add_argument("--archive_scene", default="",\n'
              '                    help="scene name to load from --out3dgs archive alone")')
s = s.replace('''    if args.out3dgs:''',
'''    if args.archive_scene:
        sc = load_archive_only_scene(args.out3dgs, args.archive_scene,
                                     factor=args.factor, cal_frac=args.cal_frac_arch)
        ep = os.path.join(args.out3dgs, args.archive_scene, "exposure.json")
        if os.path.isfile(ep):
            EXPOSURE = json.load(open(ep, encoding="utf-8"))
    elif args.out3dgs:''')
s = s.replace('ap.add_argument("--clamp_frac", type=float, default=0.01,',
              'ap.add_argument("--cal_frac_arch", type=float, default=0.5)\n'
              '    ap.add_argument("--clamp_frac", type=float, default=0.01,')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched risk_alloc for archive-only scenes")
