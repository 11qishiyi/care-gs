import io
p = r"D:\3dsg_1\research\code\scripts\voxel_and_task.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''        rng = np.random.default_rng(0)
        n = len(views)
        n_C = max(2, n // 2)
        splits = [rng.permutation(n) for _ in range(args.n_splits)]

        def merge(vt, idx):
            out = {}
            for i in idx:
                for k, v in vt[i].items():
                    if k not in out or v > out[k]:
                        out[k] = v
            return out

        row = dict(scene=scene, n_views=int(n), n_primitives=int(base.n))''',
'''        # pack the per-view dicts into a (n_views, n_voxels) matrix, NaN where unseen
        all_ids = sorted({k for name in tabs for t in tabs[name] for k in t})
        col = {k: i for i, k in enumerate(all_ids)}
        mats = {}
        for name, vt in tabs.items():
            E = np.full((len(views), len(all_ids)), np.nan, dtype=np.float32)
            for vi, t in enumerate(vt):
                for k, v in t.items():
                    E[vi, col[k]] = v
            mats[name] = E
        print(f"  voxel matrix {mats['clean'].shape} "
              f"({100*np.isfinite(mats['clean']).mean():.1f}% observed)", flush=True)

        rng = np.random.default_rng(0)
        n = len(views)
        n_C = max(2, n // 2)
        splits = [rng.permutation(n) for _ in range(args.n_splits)]

        def pooled(E, idx):
            with np.errstate(invalid="ignore"):
                return np.nanmax(E[idx], axis=0)

        row = dict(scene=scene, n_views=int(n), n_primitives=int(base.n))''')

s = s.replace('''        clean_cov = []
        for perm in splits:
            Ci, Vi = perm[:n_C], perm[n_C:]
            cal = merge(tabs["clean"], Ci)
            q = conformal_q(list(cal.values()), args.alpha)
            dep = merge(tabs["clean"], Vi)
            if dep:
                clean_cov.append(np.mean([v <= q for v in dep.values()]))''',
'''        clean_cov = []
        for perm in splits:
            Ci, Vi = perm[:n_C].tolist(), perm[n_C:].tolist()
            cal = pooled(mats["clean"], Ci)
            cal = cal[np.isfinite(cal)]
            if cal.size == 0:
                continue
            q = conformal_q(cal, args.alpha)
            dep = pooled(mats["clean"], Vi)
            ok = np.isfinite(dep)
            if ok.any():
                clean_cov.append(float(np.mean(dep[ok] <= q)))''')

s = s.replace('''            drops = []
            for perm in splits:
                Ci, Vi = perm[:n_C], perm[n_C:]
                cal = merge(tabs["clean"], Ci)
                q = conformal_q(list(cal.values()), args.alpha)
                dep = merge(tabs[name], Vi)
                cl = merge(tabs["clean"], Vi)
                if not dep or not cl:
                    continue
                base_cov = np.mean([v <= q for v in cl.values()])
                new_cov = np.mean([v <= q for v in dep.values()])
                drops.append(base_cov - new_cov)''',
'''            drops = []
            for perm in splits:
                Ci, Vi = perm[:n_C].tolist(), perm[n_C:].tolist()
                cal = pooled(mats["clean"], Ci)
                cal = cal[np.isfinite(cal)]
                if cal.size == 0:
                    continue
                q = conformal_q(cal, args.alpha)
                cl = pooled(mats["clean"], Vi)
                dep = pooled(mats[name], Vi)
                ok = np.isfinite(cl) & np.isfinite(dep)
                if not ok.any():
                    continue
                drops.append(float(np.mean(cl[ok] <= q) - np.mean(dep[ok] <= q)))''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("runner vectorised")
