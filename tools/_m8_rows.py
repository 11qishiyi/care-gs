"""Print the M8 high-rate rows (d* family) for every asset."""
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
KEEP = ["d1_c8_o8_sh4", "d1_c10_o8_sh4", "d1_c8_o8_sh5", "d1_c12_o8_sh4",
        "d2_c8_o8_sh4", "d2_c10_o8_sh3", "c12_o8_sh2", "c8_o8_sh3", "c10_o8_sh3",
        "p50_d1_c8_o8_sh4", "p10"]
for sc in d["scenes"]:
    print("== %s clean_psnr=%.3f" % (sc["scene"], sc.get("clean_psnr") or 0.0))
    by = {r["variant"]: r for r in sc["rows"]}
    for k in KEEP:
        r = by.get(k)
        if not r:
            continue
        dp = r.get("d_psnr")
        print("   %-16s bpp=%6.2f rate=%6.2fx drop=%7.2fpp [%6.2f,%6.2f] psnr=%7.2f d=%s" % (
            k, r["bytes_per_prim"], r["rate"], r["drop_pp"], r["drop_lo_pp"],
            r["drop_hi_pp"], r["psnr"], "-" if dp is None else "%+.3f" % dp))
