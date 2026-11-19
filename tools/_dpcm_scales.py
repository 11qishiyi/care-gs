import io

P = r"D:\3dsg_1\experiments\dpcm.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace('SCALE_BYTES = 8.0          # two float32 scales per block (DC trio, rest)',
              'SCALE_BYTES = 16.0         # four float32 scales per block: anchor/residual x (DC, rest)')

old = '''    qmax = float((1 << (bits - 1)) - 1)

    def _scale(t):
        return (t.abs().amax(dim=(1, 2), keepdim=True) / qmax).clamp_min(1e-12)

    s_dc = _scale(r[:, :, :3])
    s_rest = _scale(r[:, :, 3:]) if cols > 3 else s_dc
    q = torch.empty_like(r)
    q[:, :, :3] = (r[:, :, :3] / s_dc).round().clamp(-qmax - 1, qmax)
    if cols > 3:
        q[:, :, 3:] = (r[:, :, 3:] / s_rest).round().clamp(-qmax - 1, qmax)
    r_hat = torch.empty_like(r)
    r_hat[:, :, :3] = q[:, :, :3] * s_dc
    if cols > 3:
        r_hat[:, :, 3:] = q[:, :, 3:] * s_rest
'''
new = '''    qmax = float((1 << (bits - 1)) - 1)

    def _scale(t):
        return (t.abs().amax(dim=2, keepdim=True) / qmax).clamp_min(1e-12)

    # The anchor is two orders of magnitude larger than the residual, so they cannot share a
    # scale: with one scale the 2-bit step would be set by the anchor and every residual would
    # quantise to zero.  Four float32 scales per block (16 B / 64 primitives) buys them apart.
    s_a_dc = _scale(r[:, 0:1, :3])
    s_a_rest = _scale(r[:, 0:1, 3:]) if cols > 3 else s_a_dc
    s_r_dc = _scale(r[:, 1:, :3]) if block > 1 else s_a_dc
    s_r_rest = _scale(r[:, 1:, 3:]) if (cols > 3 and block > 1) else s_a_rest
    q = torch.empty_like(r)
    q[:, 0:1, :3] = (r[:, 0:1, :3] / s_a_dc).round().clamp(-qmax - 1, qmax)
    if cols > 3:
        q[:, 0:1, 3:] = (r[:, 0:1, 3:] / s_a_rest).round().clamp(-qmax - 1, qmax)
    if block > 1:
        q[:, 1:, :3] = (r[:, 1:, :3] / s_r_dc).round().clamp(-qmax - 1, qmax)
        if cols > 3:
            q[:, 1:, 3:] = (r[:, 1:, 3:] / s_r_rest).round().clamp(-qmax - 1, qmax)
    r_hat = torch.empty_like(r)
    r_hat[:, 0:1, :3] = q[:, 0:1, :3] * s_a_dc
    if cols > 3:
        r_hat[:, 0:1, 3:] = q[:, 0:1, 3:] * s_a_rest
    if block > 1:
        r_hat[:, 1:, :3] = q[:, 1:, :3] * s_r_dc
        if cols > 3:
            r_hat[:, 1:, 3:] = q[:, 1:, 3:] * s_r_rest
'''
assert old in s
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("separated anchor and residual scales")
