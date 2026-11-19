# -*- coding: utf-8 -*-
"""Let run_scene.py load released 3DGS checkpoints (cameras.json) as well as COLMAP scenes."""
import io
p = r"D:\3dsg_1\research\code\scripts\run_scene.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace(
    "from calib.colmap_io import load_colmap_scene, load_images, normalize_exposure",
    "from calib.colmap_io import load_colmap_scene, load_images, normalize_exposure\n"
    "from calib.scene3dgs import load_scene_from_3dgs")

s = s.replace('    ap.add_argument("--edits", default="prune70,prune50,sh_trunc,opa_quant,move10,move30")',
              '    ap.add_argument("--edits", default="prune70,prune50,sh_trunc,opa_quant,move10,move30")\n'
              '    ap.add_argument("--out3dgs", default="",\n'
              '                    help="dir with <scene>/cameras.json from a released 3DGS run")')

s = s.replace(
    '''    scene = load_colmap_scene(args.scene, factor=args.factor, test_every=args.test_every,
                              split=args.split, cal_frac=args.cal_frac, train_frac=args.train_frac)''',
    '''    if args.out3dgs:
        scene = load_scene_from_3dgs(
            os.path.join(args.out3dgs, os.path.basename(args.scene.rstrip("/")), "cameras.json"),
            args.scene, factor=args.factor, split=args.split,
            cal_frac=args.cal_frac, train_frac=args.train_frac)
    else:
        scene = load_colmap_scene(args.scene, factor=args.factor, test_every=args.test_every,
                                  split=args.split, cal_frac=args.cal_frac, train_frac=args.train_frac)''')

# exposure: multiply render by the per-view affine if available
s = s.replace(
    '''    out = render(splats, c2w[idx_t], K[idx_t], W, H, render_mode="RGB+ED")''',
    '''    out = render(splats, c2w[idx_t], K[idx_t], W, H, render_mode="RGB+ED")
    if EXPOSURE is not None and len(EXPOSURE):
        mats = []
        for i in idx:
            e = EXPOSURE.get(NAMES[int(i)])
            mats.append(np.eye(3, 4, dtype=np.float32) if e is None
                        else np.asarray(e, dtype=np.float32))
        E = torch.from_numpy(np.stack(mats)).to(out["colors"].device)
        out["colors"] = torch.einsum("cij,chwj->chwi", E[:, :, :3], out["colors"]) + \\
            E[:, None, None, :3, 3]''')

s = s.replace('''def fit_eval(''', '''EXPOSURE = {}
NAMES = []


def fit_eval(''')

s = s.replace(
    '''    splats = load_splats(args.ply, device=args.device)''',
    '''    global EXPOSURE, NAMES
    splats = load_splats(args.ply, device=args.device)
    NAMES = scene.get("names", [os.path.basename(p) for p in scene["image_paths"]])
    if args.out3dgs:
        import json as _json
        ep = os.path.join(args.out3dgs, os.path.basename(args.scene.rstrip("/")), "exposure.json")
        if os.path.isfile(ep):
            EXPOSURE = _json.load(open(ep, encoding="utf-8"))
            print(f"[scene] exposure entries: {len(EXPOSURE)}", flush=True)''')

io.open(p, "w", encoding="utf-8").write(s)
import ast
ast.parse(s)
print("patched run_scene for 3DGS checkpoints; syntax OK")
