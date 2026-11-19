import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""### 三条自动检查（改动后必须全部重跑）

```bash
python research/code/tests/test_operators.py          # 13 项算子断言（CPU）
python research/code/tests/test_advise.py             # 19 项顾问逻辑断言（CPU）
python research/code/scripts/verify_paper_numbers.py  # 54 项：数字 + 摘要级 + 一致性
python research/code/scripts/make_figures.py          # 4 张图从数据重建
```""",
"""### 三条自动检查（改动后必须全部重跑）

```bash
python research/code/tests/test_operators.py          # 13 项算子断言（CPU）
python research/code/tests/test_advise.py             # 19 项顾问逻辑断言（CPU）
python research/code/scripts/verify_paper_numbers.py  # 104 项：数字 + 摘要级 + 一致性
                                                      #        + 图新鲜度 + 各节表格
python research/code/scripts/make_figures.py          # 4 张图从数据重建
```

`verify_paper_numbers.py` 至今抓出过六类真实错误：抄写错误（stump 0.885→0.778）、
措辞夸大（"2–4 倍"实为 1.45–2.72）、摘要残留已撤回数字、限制节与正文自相矛盾、
索引停在旧轮次、图比数据旧。""")
io.open(p, "w", encoding="utf-8").write(d)
print("index: verification section updated")
