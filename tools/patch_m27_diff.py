import io

p = "tools/m27_diff.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''    splats = m20_model.load_model(a.ply)
    n = int(splats.means.shape[0])
    meta, streams = C.read_container(a.gs1)
    out = A.decode(meta, streams)''', '''    splats = m20_model.load_model(a.ply)
    n = int(splats.means.shape[0])
    meta, streams = C.read_container(a.gs1)
    #: dispatch through the codec so the same audit serves M27 (constant anchors) and M28 (predicted)
    out = C.decode(meta, streams)''')

s = s.replace('print(f"n={n:,} anchors={int(meta[\'n_anchor\']):,} ppa={meta[\'ppa_measured\']:.2f} voxel={voxel:.4f}")',
              'print(f"n={n:,} anchors={int(meta[\'n_anchor\']):,} ppa={meta[\'ppa_measured\']:.2f} '
              'voxel={voxel:.4f} predicted={bool(meta.get(\'predicted\'))}")')
io.open(p, "w", encoding="utf-8").write(s)
print("patched m27_diff to dispatch through the codec")
