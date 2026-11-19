import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('print(f"\\n{checks} numeric checks, {len(fails)} failures")',
'''# ---------- internal consistency: limitations must not contradict results ----------
print("[consistency] limitations vs results")
_txt = paper
_checks_consistency = [
    ("未给出\\"修复所需标定集大小\\"的曲线", "§3.4 already provides the repair curve"),
    ("所有实验在 1/4 分辨率下完成", "§3.1d runs at 1/2 resolution"),
    ("外部补充来源（BungeeNeRF 原始数据集）只通过", "§3.1a shows the official bucket works"),
    ("归档只有 4 个有 test GT，需要新的检查点来源", "data is available; the trainer is the bottleneck"),
]
for _phrase, _why in _checks_consistency:
    checks += 1
    _gone = _phrase not in _txt
    print(f"  {'OK ' if _gone else 'FAIL'} removed outdated claim: {_phrase[:28]}... ({_why})")
    if not _gone:
        fails.append(f"stale limitation: {_phrase[:30]}")

print(f"\\n{checks} numeric checks, {len(fails)} failures")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("verifier: consistency checks added")
