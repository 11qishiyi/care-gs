"""Print the compact M7 tables used by M7_RESULTS.md."""
import json
import sys

KEEP = ["clean", "m16_o8_sh3", "m16_o8_sh4", "m16_o8_sh2", "c8_o8_sh3", "c10_o8_sh3",
        "c12_o8_sh3", "c14_o8_sh3", "c12_o8_sh4", "c12_o8_sh2", "c10_o8_sh2",
        "p10", "p05", "p50_c12_o8_sh3", "p30_c10_o8_sh3"]

d = json.load(open(sys.argv[1], encoding="utf-8"))
for sc in d["scenes"]:
    print("== %s (n_views=%s, clean_psnr=%.3f)" % (
        sc["scene"], sc["n_views"], sc.get("clean_psnr") or 0.0))
    by = {r["variant"]: r for r in sc["rows"]}
    for k in KEEP:
        r = by.get(k)
        if not r:
            continue
        dp = r.get("d_psnr")
        print("   %-16s rate=%6.2fx drop=%7.2fpp [%6.2f,%6.2f] psnr=%7.2f d=%s" % (
            k, r["rate"], r["drop_pp"], r["drop_lo_pp"], r["drop_hi_pp"],
            r["psnr"], "-" if dp is None else "%+.3f" % dp))
c = d["summary"]["criteria"]
print("\n== criteria")
for k, v in c.items():
    if k == "E2_degree_vs_bits":
        print("   %s: verdict=%s winner=%s mean_pp=%s n_agree=%s" % (
            k, v.get("verdict"), v.get("winner"), v.get("mean_diff_pp"), v.get("n_agree")))
    elif k == "E3_frontier_above_8x":
        print("   %s: verdict=%s assets=%s" % (k, v.get("verdict"), v.get("assets_with_member")))
    elif k == "E1_universal_dominance":
        print("   %s: verdict=%s passing=%s" % (k, v.get("verdict"), v.get("passing_rates")))
        for r, val in (v.get("per_rate") or {}).items():
            if val.get("n_scenes"):
                print("      %sx mean=%+.2f min=%+.2f pos=%s/%s" % (
                    r, val["mean_pp"], val["min_scene_pp"], val["n_positive"], val["n_scenes"]))
    else:
        print("   %s: %s" % (k, v))
