import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()

if 'streams["cluster_bits"]' in s:
    print("decoder already adaptive")
    raise SystemExit(0)

old = '''        cbits = int(getattr(spec, "means_cluster_bits", 8))
        u = unpack_bits(streams["cluster_off"], cbits, nblk * M.CLUSTER_SIZE * 3, dtype=np.uint16)
        u = u.reshape(nblk * M.CLUSTER_SIZE, 3)[:n]'''
new = '''        cbits = int(getattr(spec, "means_cluster_bits", 8))
        if "cluster_bits" in streams:
            #: M30 -- every cluster carries its own width, chosen by the encoder from that cluster's
            #: extent.  The stream is a concatenation of per-cluster packs, so the decoder walks it;
            #: ``step`` is still stored per cluster, so nothing else about the path changes.
            bits_c = np.frombuffer(streams["cluster_bits"], dtype=np.uint8).astype(np.int64)
            block = int(M.CLUSTER_SIZE)
            buf = streams["cluster_off"]
            off = 0
            u = np.empty((nblk, block, 3), dtype=np.uint16)
            for i in range(nblk):
                nb = block * 3 * int(bits_c[i])
                nbytes = (nb + 7) // 8
                u[i] = unpack_bits(buf[off:off + nbytes], int(bits_c[i]), block * 3,
                                   dtype=np.uint16).reshape(block, 3)
                off += nbytes
            u = u.reshape(nblk * block, 3)[:n]
        else:
            u = unpack_bits(streams["cluster_off"], cbits, nblk * M.CLUSTER_SIZE * 3, dtype=np.uint16)
            u = u.reshape(nblk * M.CLUSTER_SIZE, 3)[:n]'''
assert old in s, "decode cluster block"
s = s.replace(old, new, 1)

if '"cluster_bits"' not in s.split("ORDER = (")[1].split(")")[0]:
    s = s.replace('"msc_modes", "sh_scalar_codes", "sh_scalar_scale",',
                  '"msc_modes", "sh_scalar_codes", "sh_scalar_scale", "cluster_bits",', 1)
io.open(p, "w", encoding="utf-8").write(s)
print("adaptive cluster decode installed")
