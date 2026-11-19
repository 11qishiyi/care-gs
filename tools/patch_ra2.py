import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    sc = load_scene_from_3dgs(os.path.join(args.out3dgs, name, "cameras.json"), args.scene,
                              factor=args.factor, split="chrono", cal_frac=0.15, train_frac=0.65)
    ep = os.path.join(args.out3dgs, name, "exposure.json")
    if os.path.isfile(ep):
        EXPOSURE = json.load(open(ep, encoding="utf-8"))''',
'''    if args.out3dgs:
        sc = load_scene_from_3dgs(os.path.join(args.out3dgs, name, "cameras.json"), args.scene,
                                  factor=args.factor, split="chrono", cal_frac=0.15, train_frac=0.65)
        ep = os.path.join(args.out3dgs, name, "exposure.json")
        if os.path.isfile(ep):
            EXPOSURE = json.load(open(ep, encoding="utf-8"))
    else:
        sc = load_colmap_scene(args.scene, factor=args.factor, split="chrono",
                               cal_frac=0.15, train_frac=0.65)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched: supports self-trained models (no exposure)")
