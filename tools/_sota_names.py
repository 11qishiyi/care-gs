import sys

sys.path.insert(0, r"D:\3dsg_1\experiments")
import qfp_rd as Q

names = ["clean", "sh8_g32", "sh4_g32", "p50_q8_g32", "p50_q4_g32",
         "p30_q4_g32", "p30_q2_g32"]
for n in names:
    s = Q.parse_spec(n)
    print(f"{n:14s} keep={s.keep:.2f} sh={s.sh_bits:2d} geo={s.geo or 'fp32'} "
          f"B={s.bytes_per_prim(3):7.2f} rate={s.rate_vs_fp32(3):5.2f}x "
          f"fam={s.family}")
print("fp32 bytes/prim:", Q.fp32_bytes_per_prim(3))
