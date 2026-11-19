import io
src = io.open(r"D:\3dsg_1\research\code\scripts\edit_families.py", encoding="utf-8").read()
s = src.replace('''        res = {}
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
            torch.cuda.empty_cache()''',
'''        # sensitivity first (needs gradients on the full model), then free it
        sens = sensitivity_scores(base, c2w, K, gt, views[:8], W, H,
                                  n_views=min(8, len(views)), device=args.device)
        print("  sensitivity computed", flush=True)
        res = {}
        res["clean"] = per_view_residuals(base, c2w, K, gt, views, W, H, args.device)
        print("  rendered clean", flush=True)
        k30 = max(1, int(round(0.3 * base.n)))
        keep_op = torch.argsort(-base.opacities)[:k30].sort().values.to(args.device)
        keep_pup = torch.argsort(-sens)[:k30].sort().values.to(args.device)
        op30 = base.subset(keep_op)
        pup30 = base.subset(keep_pup)
        del base
        torch.cuda.empty_cache()
        for name, m in (("opacity30", op30), ("pup30", pup30)):
            res[name] = per_view_residuals(m, c2w, K, gt, views, W, H, args.device)
            print(f"  rendered {name}", flush=True)
            del m
            torch.cuda.empty_cache()''')
s = s.replace('for name in ("shdeg1", "quant8"):', 'for name in ("opacity30", "pup30"):')
io.open(r"D:\3dsg_1\research\code\scripts\criteria_stats.py", "w", encoding="utf-8").write(s)
print("wrote criteria_stats.py")
