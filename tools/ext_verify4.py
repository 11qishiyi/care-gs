import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- deliverables index must not contradict the paper ----------
print("[consistency] deliverables index")
IDX = os.path.join(ROOT, "DELIVERABLES.md")
if os.path.isfile(IDX):
    idx = io.open(IDX, encoding="utf-8").read()
    checks += 1
    n_sections = len(re.findall(r"^### 3\\.", paper, flags=re.M))
    listed = len(re.findall(r"^\\| 3\\.", idx, flags=re.M))
    _ok = listed >= n_sections
    print(f"  {'OK ' if _ok else 'FAIL'} index lists {listed} result rows "
          f"(paper has {n_sections} subsections)")
    if not _ok:
        fails.append("index missing result rows")
    for stale in ("26 轮", "8 个方向", "44 项检查", "八个被否定"):
        checks += 1
        gone = stale not in idx
        print(f"  {'OK ' if gone else 'FAIL'} no stale phrase in index: {stale}")
        if not gone:
            fails.append(f"stale index phrase: {stale}")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: index consistency checks added")
