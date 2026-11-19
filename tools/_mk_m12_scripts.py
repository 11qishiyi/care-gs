import io

src = io.open(r"D:\3dsg_1\experiments\run_m11.sh", encoding="utf-8").read()
s = src.replace("M11: does per-primitive mode selection (dict / scalar / zero) clear 12x?",
                "M12: does product quantisation of the SH block beat one 48-d codebook?")
s = s.replace("run_m11.sh", "run_m12.sh")
s = s.replace("/workspace/res/m11", "/workspace/res/m12")
s = s.replace("m11_bytes.json", "m12_bytes.json")
s = s.replace("m11_rd.json", "m12_rd.json")
s = s.replace("m11_report", "m12_report")
s = s.replace("${VARIANT_SET:-m11}", "${VARIANT_SET:-m12}")
s = s.replace("Q.M11_VARIANTS", "Q.M12_VARIANTS")
s = s.replace("8 assets x 15 variants (selector + anchors)", "8 assets x 18 variants (PQ + anchors)")
s = s.replace("P1/P2/P3 on the measured axis", "Q1/Q2 on the measured axis")
s = s.replace("FIDELITY=0 by default: L1/L2/L3 need coverage and PSNR",
              "FIDELITY=0 by default: Q1/Q2 need coverage and PSNR")
assert "m11" not in s, [ln for ln in s.splitlines() if "m11" in ln]
io.open(r"D:\3dsg_1\experiments\run_m12.sh", "w", encoding="utf-8", newline="\n").write(s)
print("run_m12.sh", len(s))

f = io.open(r"D:\3dsg_1\experiments\m11_finish.sh", encoding="utf-8").read()
f = f.replace("m11_finish.sh", "m12_finish.sh")
f = f.replace("/workspace/res/m11", "/workspace/res/m12")
f = f.replace("m11_bytes.json", "m12_bytes.json")
f = f.replace("m11_rd.json", "m12_rd.json")
f = f.replace("m11_report", "m12_report")
f = f.replace("m11_analyse.log", "m12_analyse.log")
f = f.replace("M11_FINISH_DONE", "M12_FINISH_DONE")
f = f.replace("# Wait for the four surviving byte measurements, merge, analyse, and score M11.",
              "# Wait for the byte measurements, merge, analyse, and score M12.")
assert "m11" not in f, [ln for ln in f.splitlines() if "m11" in ln]
io.open(r"D:\3dsg_1\experiments\m12_finish.sh", "w", encoding="utf-8", newline="\n").write(f)
print("m12_finish.sh", len(f))

p = io.open(r"D:\3dsg_1\tools\push_m11.ps1", encoding="utf-8").read()
p = p.replace("m11", "m12").replace("M11", "M12")
io.open(r"D:\3dsg_1\tools\push_m12.ps1", "w", encoding="utf-8", newline="\n").write(p)
print("push_m12.ps1")

q = io.open(r"D:\3dsg_1\tools\fetch_m11.ps1", encoding="utf-8").read()
q = q.replace("m11", "m12").replace("M11", "M12")
io.open(r"D:\3dsg_1\tools\fetch_m12.ps1", "w", encoding="utf-8", newline="\n").write(q)
print("fetch_m12.ps1")
