import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()

# ---- 1. quaternion sign alignment + 2. opacity averaged in linear space -------------------------
old = '''    scales = np.log(np.maximum(np.asarray(_get(splats, "scales"), dtype=np.float64), 1e-12))
    opac = np.clip(np.asarray(_get(splats, "opacities"), dtype=np.float64).reshape(-1), 1e-6, 1 - 1e-6)
    opac = np.log(opac / (1 - opac))
    quats = np.asarray(_get(splats, "quats"), dtype=np.float64)

    a_scale, a_opac, a_quat = _mean(scales), _mean(opac), _mean(quats)
    a_quat /= np.maximum(np.linalg.norm(a_quat, axis=1, keepdims=True), 1e-12)
'''
new = '''    scales = np.log(np.maximum(np.asarray(_get(splats, "scales"), dtype=np.float64), 1e-12))
    #: opacity is averaged in *linear* space and turned back into a logit afterwards.  Averaging
    #: logits is an average of odds, which one opaque member drags to near-certainty: measured on
    #: bicycle it moved the median opacity of a voxel from 0.12 to 0.21 and cost most of a decibel.
    opac_lin = np.clip(np.asarray(_get(splats, "opacities"), dtype=np.float64).reshape(-1), 1e-6, 1 - 1e-6)
    quats = np.asarray(_get(splats, "quats"), dtype=np.float64)

    a_scale = _mean(scales)
    a_opac_lin = _mean(opac_lin)
    a_opac = np.log(a_opac_lin / (1 - a_opac_lin))

    #: quaternions have a double cover: ``q`` and ``-q`` are the same rotation, so a plain mean of a
    #: voxel whose members disagree about the sign lands near zero, and renormalising that is noise.
    #: Measured before the fix: mean |dot| 0.92, worst 0.00005 -- i.e. some anchors' rotations were
    #: simply random.  Align every member to the sign of the unnormalised mean first.
    q_o = quats[order]
    raw = np.add.reduceat(q_o, starts, axis=0)
    norm = np.linalg.norm(raw, axis=1, keepdims=True)
    ref = raw / np.maximum(norm, 1e-12)
    ref[norm[:, 0] < 1e-9] = np.array([1.0, 0.0, 0.0, 0.0])
    dot = (q_o * ref[ofa]).sum(axis=1)
    q_o = q_o * np.where(dot < 0.0, -1.0, 1.0)[:, None]
    a_quat = np.add.reduceat(q_o, starts, axis=0) / counts[:, None]
    a_quat /= np.maximum(np.linalg.norm(a_quat, axis=1, keepdims=True), 1e-12)
'''
assert old in s
s = s.replace(old, new)

# ofa must exist before the quaternion block
s = s.replace('''    def _mean(v):''', '''    ofa = np.repeat(np.arange(int(vox.shape[0])), counts)

    def _mean(v):''', 1)
s = s.replace("    ofa = np.repeat(np.arange(na), counts)\n    off = means[order] - a_means[ofa]",
              "    off = means[order] - a_means[ofa]")

# ---- 3. DC: finer codes against the per-anchor level -------------------------------------------
s = s.replace('''    qmax = (1 << (dc_bits - 1)) - 1
    lvl_prim = a_lvl[ofa][:, None]''', '''    qmax = (1 << (dc_bits - 1)) - 1
    lvl_prim = a_lvl[ofa][:, None]''')

# defaults: 6-bit DC
s = s.replace("attr_bits: int = 8, dc_bits: int = 3, offset_bits: int = OFFSET_BITS)",
              "attr_bits: int = 8, dc_bits: int = 6, offset_bits: int = OFFSET_BITS)")
s = s.replace('ap.add_argument("--dc-bits", type=int, default=3)',
              'ap.add_argument("--dc-bits", type=int, default=6)')
io.open(p, "w", encoding="utf-8").write(s)
print("patched attributes")
