import io
B = r"D:\3dsg_1\experiments\m4_bytes.py"
b = io.open(B, encoding="utf-8").read()

# scalar codes: offset into [0, 2**b - 1] so they cost exactly b bits, as the model says
b = b.replace("""            c0 = torch.round(sub[:, :3] / st0).clamp(-qmax - 1.0, qmax).numpy().astype(np.int64)
            c1 = torch.round(sub[:, 3:] / st1).clamp(-qmax - 1.0, qmax).numpy().astype(np.int64)""",
"""            off = int(qmax) + 1
            c0 = (torch.round(sub[:, :3] / st0).clamp(-qmax - 1.0, qmax)
                  .numpy().astype(np.int64) + off)
            c1 = (torch.round(sub[:, 3:] / st1).clamp(-qmax - 1.0, qmax)
                  .numpy().astype(np.int64) + off)""", 1)

b = b.replace("""            streams["sh_scalar_codes"] = (pack_bits(c0, b_s + 1)
                                          + pack_bits(c1, b_s + 1))
            per_prim += (float(ms.sum()) / n) * (cols * (b_s + 1) / 8.0 + 2.0)""",
"""            streams["sh_scalar_codes"] = pack_bits(c0, b_s) + pack_bits(c1, b_s)
            per_prim += (float(ms.sum()) / n) * (cols * b_s / 8.0 + 2.0)""", 1)

b = b.replace("""        streams["sh_cb_hdr"] = hdr
        streams["sh_cb_centroids"] = np.ascontiguousarray(c_u8).tobytes()
        _ = mz
        return streams, per_prim""",
"""        streams["sh_cb_hdr"] = hdr
        streams["sh_cb_centroids"] = np.ascontiguousarray(c_u8).tobytes()
        spec.msc_frac = (float(mz.sum()) / n, float(md.sum()) / n, float(ms.sum()) / n)
        return streams, per_prim""", 1)

io.open(B, "w", encoding="utf-8", newline="\n").write(b)
print("ok")
