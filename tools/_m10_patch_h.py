"""The synthetic worlds need orthogonal knobs: gain (L2) and absolute level (L1)."""
import io

P = r"D:\3dsg_1\experiments\m10_report.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace(
    '''def _synth(gain_pp, n=8, dpsnr_ok=True):''',
    '''def _synth(gain_pp, n=8, dpsnr_ok=True, base_drop=-1.9):''', 1)
s = s.replace(
    '''        for bits in (12, 14):
            rows.append(dict(variant=f"rvq8-{bits - 8}_c8_o8", rate=18.2,
                             drop_pp=-2.0 + gain_pp,
                             d_psnr=(0.15 if dpsnr_ok else -0.4)))''',
    '''        for bits in (12, 14):
            rows.append(dict(variant=f"rvq8-{bits - 8}_c8_o8", rate=18.2,
                             drop_pp=base_drop + gain_pp,
                             d_psnr=(0.15 if dpsnr_ok else -0.4)))''', 1)
s = s.replace(
    '''    res = evaluate(_synth(0.1))
    check("a 0.1 pp residual gain fails L2", not res["L2_rvq_vs_single"]["verdict"],''',
    '''    res = evaluate(_synth(0.1, base_drop=-0.6))
    check("a 0.1 pp residual gain fails L2", not res["L2_rvq_vs_single"]["verdict"],''', 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
