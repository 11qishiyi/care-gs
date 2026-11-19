import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("| α 鲁棒性 | `research/results_v28/cert_a0.05.json`、`cert_a0.2.json` |",
              "| α 鲁棒性 | `research/results_v28/cert_a0.05.json`、`cert_a0.2.json` |\n| 分辨率鲁棒性 | `research/results_v31/cert_f2.json` |")
io.open(p, "w", encoding="utf-8").write(s)
print("refs updated")
