# -*- coding: utf-8 -*-
"""Add the decisive downstream check: which variance actually predicts the error?"""
import io
p = r"D:\3dsg_1\research\code\scripts\variance_object_test.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''    return dict(V_mm=V_mm.cpu().numpy(), V_ind=V_ind.cpu().numpy(),
                V_cpl=V_cpl.cpu().numpy(), C=C.cpu().numpy(), n=int(n))''',
'''    return dict(V_mm=V_mm.cpu().numpy(), V_ind=V_ind.cpu().numpy(),
                V_cpl=V_cpl.cpu().numpy(), C=C.cpu().numpy(), n=int(n),
                u0=u0, v0=v0)''')

s = s.replace('''    name = os.path.basename(args.scene.rstrip("/"))''',
'''    global EXPOSURE, NAMES
    name = os.path.basename(args.scene.rstrip("/"))''')

s = s.replace('''    W, H = sc["width"], sc["height"]
    c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)''',
'''    W, H = sc["width"], sc["height"]
    EXPOSURE = json.load(open(os.path.join(args.out3dgs, name, "exposure.json"), encoding="utf-8")) \\
        if os.path.isfile(os.path.join(args.out3dgs, name, "exposure.json")) else {}
    NAMES = sc.get("names", [])
    gt_all = torch.from_numpy(normalize_exposure(
        load_images(sc["image_paths"], args.factor, (W, H)))).float().to(args.device)
    c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)''')

s = s.replace('''            for k in acc:
                acc[k].append(out[k].ravel())
            done += 1''',
'''            # ground-truth error at the same pixels
            C = out["C"]
            if EXPOSURE:
                e = EXPOSURE.get(NAMES[vi])
                E = torch.from_numpy(np.eye(3, 4, dtype=np.float32) if e is None
                                     else np.asarray(e, dtype=np.float32)).to(args.device)
                Cin = C[..., None].expand(P, P, 3)
                Cc = torch.einsum("ij,hwj->hwi", E[:, :3], Cin) + E[None, None, :3, 3]
            else:
                Cc = C[..., None].expand(P, P, 3)
            g = gt_all[vi, out["v0"]:out["v0"] + P, out["u0"]:out["u0"] + P]
            err = (Cc - g).abs().mean(-1).cpu().numpy()
            for k in acc:
                acc[k].append(out[k].ravel())
            acc["err"].append(err.ravel())
            done += 1''')

s = s.replace("acc = dict(V_mm=[], V_ind=[], V_cpl=[])",
              "acc = dict(V_mm=[], V_ind=[], V_cpl=[], err=[])")

s = s.replace('''    json.dump(dict(scene=name, n_pixels=int(mm.size), spearman_mm=r_mm, spearman_ind=r_ind,
                   median_ratio_mm=float(ratio),
                   median_ratio_ind=float(np.median(cpl / np.maximum(ind, 1e-12)))),
              open(args.out, "w", encoding="utf-8"), indent=1)''',
'''    e = D["err"][ok]
    def sp(a, b):
        return float(spearmanr(a, b).statistic)
    res = dict(scene=name, n_pixels=int(mm.size),
               spearman_mm_vs_cpl=r_mm, spearman_ind_vs_cpl=r_ind,
               median_ratio_mm=float(ratio),
               median_ratio_ind=float(np.median(cpl / np.maximum(ind, 1e-12))),
               err_corr_mm=sp(mm, e), err_corr_ind=sp(ind, e), err_corr_cpl=sp(cpl, e))
    print(f"  Spearman(V_mm , |error|) = {res['err_corr_mm']:+.3f}")
    print(f"  Spearman(V_ind, |error|) = {res['err_corr_ind']:+.3f}")
    print(f"  Spearman(V_cpl, |error|) = {res['err_corr_cpl']:+.3f}")
    json.dump(res, open(args.out, "w", encoding="utf-8"), indent=1)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched: error-correlation check added")
