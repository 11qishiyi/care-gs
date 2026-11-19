import io

s = io.open(r"D:\3dsg_1\experiments\run_m10.sh", encoding="utf-8").read()
s = s.replace("M10: does a two-stage (residual) dictionary clear the 12x near-lossless gate?",
              "M11: does per-primitive mode selection (dict / scalar / zero) clear 12x?")
s = s.replace("run_m10.sh", "run_m11.sh")
s = s.replace("/workspace/res/m10", "/workspace/res/m11")
s = s.replace("m10_bytes.json", "m11_bytes.json")
s = s.replace("m10_rd.json", "m11_rd.json")
s = s.replace("m10_report", "m11_report")
s = s.replace("${VARIANT_SET:-m10}", "${VARIANT_SET:-m11}")
s = s.replace("Q.M10_VARIANTS", "Q.M11_VARIANTS")
s = s.replace("8 assets x 16 variants (two-stage + anchors)",
              "8 assets x 15 variants (selector + anchors)")
s = s.replace("L1/L2/L3 on the measured axis", "P1/P2/P3 on the measured axis")
assert "m10" not in s, [ln for ln in s.splitlines() if "m10" in ln]
io.open(r"D:\3dsg_1\experiments\run_m11.sh", "w", encoding="utf-8", newline="\n").write(s)
print("written", len(s), "CR", s.count("\r"))
