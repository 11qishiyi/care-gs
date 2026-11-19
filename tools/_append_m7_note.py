"""Append the M7 metering addendum (perceptual metrics dropped) before any M7 data exists."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
### M7.4a 计量修订（2026-11-13 23:02，M7 数据落盘之前）

写此修订时节点 2139436 刚租到、`/workspace/data` 仍为空、`/workspace/res/m7` 不存在，
上一次 setup 在拉 LPIPS 骨干时卡死（`alexnet-owt-7be5be79.pth` 5 分钟只下了 3.1 MB，
≈10 kB/s，按此速率 233 MB 需要 6 小时以上），已 `pkill` 并重跑。

**修订**：M7 的 dump 关掉 `--fidelity`（`FIDELITY=0`），因此本轮**没有 SSIM/LPIPS**，
只有覆盖率与 PSNR。理由与影响：

- H1（覆盖率支配）只用 `drop_pp`；H2（前沿）只用 `drop_pp` 与 `dPSNR`；H3 是 E1 的
  覆盖率重放。三条判据都不读感知指标，**判据本身不需要修订**。
- 与 M1/M2/M3/M5 的对照因此只落在覆盖率与 PSNR 上；SSIM/LPIPS 的"不劣"证据请引用
  M5（那一轮的 dump 带了 `--fidelity`，`m5_rd.json` 里有 `min_dSSIM/max_dLPIPS`）。
- 禁止条款不变：不得因为缺感知指标而放宽或删除任何一条判据。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT), "chars")
