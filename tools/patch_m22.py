import io

p = "experiments/m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s

s = s.replace('''    f = fit(rest, rank)
    q = quantise(f["coef"], f["comp"], bits)''',
'''    f = fit(rest, rank)
    q = quantise(f["coef"], f["comp"], bits, mode=mode)''')

s = s.replace('''    streams["sh_coef_lvl"] = q["lvl"].tobytes()
    streams["sh_coef_ref"] = np.asarray([q["ref"]], dtype=np.float32).tobytes()''',
'''    if mode == "prim":
        streams["sh_coef_lvl"] = q["lvl"].tobytes()
        streams["sh_coef_ref"] = np.asarray([q["ref"]], dtype=np.float32).tobytes()''')

s = s.replace('''            "sh_basis_rank": int(rank), "sh_basis_bits": int(bits), "sh_coef_layout": layout,''',
'''            "sh_basis_rank": int(rank), "sh_basis_bits": int(bits), "sh_coef_layout": layout,
            "sh_coef_mode": mode,''')

s = s.replace('''def encode_basis(splats, rank: int, bits: int = 3, level: int = 12, path: str = None,
                 layout: str = "bytes", spec_name: str = "c10_o8_sh3") -> dict:''',
'''def encode_basis(splats, rank: int, bits: int = 3, level: int = 12, path: str = None,
                 layout: str = "bytes", spec_name: str = "c10_o8_sh3",
                 mode: str = "component") -> dict:''')

s = s.replace('''    comp = np.frombuffer(streams["sh_basis_comp"], dtype=np.float32).astype(np.float64)
    lvl = np.frombuffer(streams["sh_coef_lvl"], dtype=np.uint8).astype(np.float64)
    ref = float(np.frombuffer(streams["sh_coef_ref"], dtype=np.float32)[0])
    u = lvl / 255.0 * ref
    if meta.get("sh_coef_layout") == "bits":''',
'''    comp = np.frombuffer(streams["sh_basis_comp"], dtype=np.float32).astype(np.float64)
    if meta.get("sh_coef_layout") == "bits":''')

s = s.replace('''    qmax = (1 << (bits - 1)) - 1
    coef = (codes - float(qmax + 1)) * u[:, None] * comp[None, :]
    return mean[None, :] + coef @ basis''',
'''    if meta.get("sh_coef_mode", "component") == "component":
        step = 2.0 / float(1 << bits)
        coef = ((codes.astype(np.float64) + 0.5) * step - 1.0) * comp[None, :]
    else:
        lvl = np.frombuffer(streams["sh_coef_lvl"], dtype=np.uint8).astype(np.float64)
        ref = float(np.frombuffer(streams["sh_coef_ref"], dtype=np.float32)[0])
        u = lvl / 255.0 * ref
        qmax = (1 << (bits - 1)) - 1
        coef = (codes - float(qmax + 1)) * u[:, None] * comp[None, :]
    return mean[None, :] + coef @ basis''')

# probe: report both quantisers side by side
s = s.replace('''    for r in ranks:
        f = fit(rest, r)
        q = quantise(f["coef"], f["comp"], 3)
        #: the quantised reconstruction, not the exact one: the file only ever ships codes
        u = q["lvl"].astype(np.float32) / 255.0 * q["ref"]
        coef_q = (q["codes"].astype(np.float32) - (q["qmax"] + 1)) * u[:, None] * f["comp"][None, :]
        rec = mean + coef_q @ f["basis"]
        err = float(np.sqrt(((rec - rest) ** 2).mean() / max(1e-12, (rest ** 2).mean())))
        bpp = 1.0 + r * 3 / 8.0 + (r * rest.shape[1] * 4 + rest.shape[1] * 4) / n
        out["rows"].append({"rank": r, "energy": f["energy"], "rel_rmse": err,
                            "bytes_per_prim": bpp, "coef_err": q["err"]})
        print(f"  r={r:3d}  energy {f['energy']*100:6.2f}%  rel RMSE {err*100:6.3f}%  "
              f"colour {bpp:5.2f} B/prim (was 20.61)", flush=True)''',
'''    for r in ranks:
        f = fit(rest, r)
        row = {"rank": r, "energy": f["energy"]}
        for mode in ("component", "prim"):
            q = quantise(f["coef"], f["comp"], 3, mode=mode)
            codes = q["codes"].astype(np.float32)
            if mode == "component":
                step = 2.0 / 8.0
                coef_q = ((codes + 0.5) * step - 1.0) * f["comp"][None, :]
            else:
                u = q["lvl"].astype(np.float32) / 255.0 * q["ref"]
                coef_q = (codes - (q["qmax"] + 1)) * u[:, None] * f["comp"][None, :]
            rec = mean + coef_q @ f["basis"]
            row[f"rel_rmse_{mode}"] = float(np.sqrt(((rec - rest) ** 2).mean()
                                                    / max(1e-12, (rest ** 2).mean())))
            row[f"bytes_{mode}"] = r * 3 / 8.0 + (1.0 if mode == "prim" else 0.0) \\
                + (r * rest.shape[1] * 4 + rest.shape[1] * 4) / n
        out["rows"].append(row)
        print(f"  r={r:3d}  energy {f['energy']*100:6.2f}%  "
              f"RMSE component {row['rel_rmse_component']*100:6.3f}% "
              f"({row['bytes_component']:5.2f} B)  "
              f"prim-scale {row['rel_rmse_prim']*100:6.3f}% ({row['bytes_prim']:5.2f} B)",
              flush=True)''')

# encode_all: pass mode
s = s.replace('''def encode_all(ply: str, ranks, out: str, bits: int = 3, level: int = 12,
               layouts=("bytes",)) -> list:''',
'''def encode_all(ply: str, ranks, out: str, bits: int = 3, level: int = 12,
               layouts=("bytes",), mode: str = "component") -> list:''')
s = s.replace('''            rec = encode_basis(mod, rank=r, bits=bits, level=level, path=p, layout=layout)''',
'''            rec = encode_basis(mod, rank=r, bits=bits, level=level, path=p, layout=layout,
                               mode=mode)''')
s = s.replace('''    ap.add_argument("--bits", type=int, default=3)''',
'''    ap.add_argument("--bits", type=int, default=3)
    ap.add_argument("--mode", default="component", choices=["component", "prim"])''')
s = s.replace('''        rows = encode_all(a.encode, ranks, a.out, bits=a.bits,
                          layouts=tuple(x for x in a.layouts.split(",") if x.strip()))''',
'''        rows = encode_all(a.encode, ranks, a.out, bits=a.bits, mode=a.mode,
                          layouts=tuple(x for x in a.layouts.split(",") if x.strip()))''')

assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched")
