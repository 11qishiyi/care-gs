import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
# the paper's main table reports the STALE certificate; the recalibrated one is a separate column
s = s.replace('''    p = by[(scene, "prune30")]
    check(f"{scene} prune30 cov", p["cov_pix"], prune)
    check(f"{scene} prune30 drop(pp)", 100 * (p["cov_pix"] - c["cov_pix"]),''',
'''    p = by[(scene, "prune30")]
    check(f"{scene} prune30 STALE cov", p["stale_cov_pix"], prune)
    check(f"{scene} prune30 STALE drop(pp)", 100 * (p["stale_cov_pix"] - c["cov_pix"]),''')
s = s.replace('''            d = 100 * (r["cov_pix"] - clean["cov_pix"])''',
              '''            d = 100 * (r["stale_cov_pix"] - clean["cov_pix"])''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed field: stale vs recalibrated")
