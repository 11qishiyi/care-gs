import io

# --- encoder side: record the base stream's original byte length in the plan -------------------
p = "experiments/m29_split.py"
s = io.open(p, encoding="utf-8").read()
old = '''        rows.append({"stream": name, "split": kind, "k": len(parts),'''
new = '''        raw_len[name] = len(streams[name])
        rows.append({"stream": name, "split": kind, "k": len(parts),'''
assert old in s
s = s.replace(old, new, 1)

old = '''    new = {k: v for k, v in streams.items()}'''
new = '''    new = {k: v for k, v in streams.items()}
    raw_len = {}'''
assert old in s
s = s.replace(old, new, 1)

old = '''    meta["split_plan"] = {k: {"kind": v[0], "bits": int(v[1]), "dims": int(v[2])}
                          for k, v in plan.items()}'''
new = '''    meta["split_plan"] = {k: {"kind": v[0], "bits": int(v[1]), "dims": int(v[2]),
                              "raw": int(raw_len.get(k, 0))}
                          for k, v in plan.items()}'''
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)

# --- decoder side: pad back to the base stream's byte length -----------------------------------
p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()
old = '''            codes[sel] = arr
            del streams[key]
        streams[name] = M.pack_bits(codes.reshape(-1), bits)'''
new = '''            codes[sel] = arr
            del streams[key]
        #: the encoder pads a stream to whole blocks (the position stream pads to a 256-primitive
        #: cluster), so the rejoined array is extended with the last row to the original byte length
        want = int(info.get("raw") or 0)
        if want:
            n_codes = (want * 8) // bits
            if n_codes > codes.size:
                pad = codes.reshape(-1).shape[0]
                extra = n_codes - pad
                codes = np.concatenate([codes, np.repeat(codes[-1:], extra, axis=0)], axis=0)
        streams[name] = M.pack_bits(codes.reshape(-1), bits)'''
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("pad-to-original-length installed")
