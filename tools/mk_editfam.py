import io
src = io.open(r"D:\3dsg_1\research\code\scripts\unified_stats.py", encoding="utf-8").read()
# keep only the clean / shdeg1 / quant8 variants and free models as we go
s = src.replace('''        variants = {}
        variants["clean"] = base
        for r in (0.5, 0.3):
            k = max(1, int(round(r * base.n)))
            keep = torch.argsort(-base.opacities)[:k].sort().values
            variants[f"prune{int(r*100)}"] = base.subset(keep)
        variants["shdeg1"] = reduce_sh(load_splats(ply, device=args.device))
        variants["quant8"] = quant_sh(load_splats(ply, device=args.device))
        sens = sensitivity_scores(base, c2w, K, gt, views[:8], W, H, n_views=min(8, len(views)),
                                  device=args.device)
        k30 = max(1, int(round(0.3 * base.n)))
        keep_pup = torch.argsort(-sens)[:k30].sort().values
        variants["pup30"] = base.subset(keep_pup)

        res = {}
        for name, m in variants.items():
            res[name] = per_view_residuals(m, c2w, K, gt, views, W, H, args.device)
            print(f"  rendered {name}", flush=True)''',
'''        res = {}
        res["clean"] = per_view_residuals(base, c2w, K, gt, views, W, H, args.device)
        print("  rendered clean", flush=True)
        del base
        torch.cuda.empty_cache()
        for name in ("shdeg1", "quant8"):
            m = load_splats(ply, device=args.device)
            m = reduce_sh(m) if name == "shdeg1" else quant_sh(m)
            res[name] = per_view_residuals(m, c2w, K, gt, views, W, H, args.device)
            print(f"  rendered {name}", flush=True)
            del m
            torch.cuda.empty_cache()''')
s = s.replace('for name in ("prune50", "prune30", "shdeg1", "quant8", "pup30"):',
              'for name in ("shdeg1", "quant8"):')
s = s.replace('row = dict(scene=scene, n_views=int(n), n_primitives=int(base.n),',
              'row = dict(scene=scene, n_views=int(n),')
io.open(r"D:\3dsg_1\research\code\scripts\edit_families.py", "w", encoding="utf-8").write(s)
print("wrote edit_families.py")
