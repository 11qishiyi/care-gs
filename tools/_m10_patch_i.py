"""Shift every family with base_drop so the gain knob measures only the residual stage."""
import io

P = r"D:\3dsg_1\experiments\m10_report.py"
s = io.open(P, encoding="utf-8").read()

s = s.replace(
    '''        for b, bits in ((6, 12), (8, 14), (10, 16)):
            rows.append(dict(variant=f"vq{bits}_c8_o8", rate=18.0, drop_pp=-2.0,
                             d_psnr=0.15))
        rows.append(dict(variant="c8_o8_sh2", rate=17.0, drop_pp=-3.0, d_psnr=0.2))''',
    '''        for b, bits in ((6, 12), (8, 14), (10, 16)):
            rows.append(dict(variant=f"vq{bits}_c8_o8", rate=18.0,
                             drop_pp=base_drop - 0.1, d_psnr=0.15))
        rows.append(dict(variant="c8_o8_sh2", rate=17.0, drop_pp=base_drop - 1.1,
                         d_psnr=0.2))''', 1)

s = s.replace(
    '''    res = evaluate(_synth(0.1, base_drop=-0.6))''',
    '''    res = evaluate(_synth(0.1, base_drop=-0.6))''', 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
