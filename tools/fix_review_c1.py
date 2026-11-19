import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("### 3.3 证书指标低估了实际损失 2–12 倍",
              "### 3.3 证书指标低估了实际损失 1.9–12.1 倍")
# C1: minimal reproduction commands
s = s.replace("""自动检查：`tests/test_operators.py`（13 项）、`tests/test_advise.py`（19 项）、
`tests/test_voxel_cert.py`（5 项）、`tests/test_downstream_task.py`（9 项）、
`scripts/verify_paper_numbers.py`（104 项数字/一致性/图新鲜度校验）。""",
"""**最小复现**（三条命令）：

```bash
python research/code/scripts/many_splits.py --out /tmp/main.json   # 主表（400 次划分）
python research/code/scripts/voxel_and_task.py --out /tmp/vt.json  # 3D 体素 + 下游任务
python research/code/scripts/verify_paper_numbers.py               # 104 项数字校验
```

自动检查：`tests/test_operators.py`（13 项）、`tests/test_advise.py`（19 项）、
`tests/test_voxel_cert.py`（5 项）、`tests/test_downstream_task.py`（9 项）、
`scripts/verify_paper_numbers.py`（104 项数字/一致性/图新鲜度校验）。""")
io.open(p, "w", encoding="utf-8").write(s)
print("C1 + section title fixed")
