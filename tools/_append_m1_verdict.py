"""One-shot: append the M1 verdict block to experiments/METHOD_PLAN.md.

Idempotent: refuses to append twice (checks for the M1.7 marker).  Written as a
script rather than an inline heredoc because this machine's PowerShell has no
bash-style heredocs.
"""
from __future__ import annotations

import io
import os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "experiments", "METHOD_PLAN.md")

BLOCK = """
## M1.7 执行结果与判定（2026-11-13 17:10，跑完写，不改判据）

**outcome: `method_holds`（D1 / D2 / D3 全部 PASS）**。数据
`experiments/artifacts/a4/m1_rd.json`（400 splits，4 场景），报告
`experiments/M1_RESULTS.md`。

| 码率 | D1 覆盖优势（QFP − prune） | 场景同向 | D2 PSNR（mean / min） | D3 近无损成员 |
|---|---|---|---|---|
| 2.0× | **+7.57 pp** [+3.50, +9.21] | 4/4 | +1.82 / +0.10 dB | `sh16_g16`（−0.09 … −0.57 pp） |
| 3.0× | **+11.76 pp** [+7.30, +14.19] | 4/4 | +3.02 / +0.33 dB | `sh8_g16`（−0.09 … −0.57 pp） |
| 5.0× | **+16.32 pp** [+11.77, +20.73] | 4/4 | +3.59 / +0.65 dB | `sh4_g16`（−0.46 … −1.22 pp） |

`rates_passing 3 / rates_total 8`：7× 以上没有剪枝对照（`p20 = 5.00×` 是剪枝上限），
按禁止条款不外推，所以分母是 8、分子是 3。

**实测变体数 35（规格表写的是 33）**：实现时 `sh` 行从 4 档扩到 5 档
（`sh{16,12,8,6,4}_g16`）、`q` 行从 5 档扩到 6 档（`q6_g12 q4_g12 q3_g12 q2_g12
q2_g10 q2_g6`）。这是**加入更多候选点**，不删点、不改判据、不改码率点，
不构成对预注册的偏离；反之若为了凑 33 而删点才是偏离。

**三条机制结论（比判据本身更重要）**：
1. 11 个几何标量里只有 3 个位置分量贵：`iso_scales8`/`iso_quats8`/`iso_opac8`
   在 4 场景全部 0.00–0.02 pp、0.00–0.01 dB；`iso_means12` 已经是 −14.2 … −33.0 pp。
2. 免费压缩的上限是 **4.92×**（`sh4_g16`，48 B/prim，SH 16→4 bit 只花 0.03 dB）。
3. `q*_g12` 族 5.55× 以上的崩塌来自 12-bit 全局网格对位置的伤害（−19.0 … −33.0 pp），
   不是量化本身；SH 从 6 bit 降到 2 bit 只再加 0.1–2.8 pp。**误差预算必须相对基元 σ，
   不能相对场景尺寸**（10 m / 4096 = 2.4 mm，而树叶 σ ≈ 1–2 mm）。

**对 M2 的直接约束**：M1 之后 44 B 的几何固定开销仍未动，而它现在被证明是唯一贵的部分。
M2 必须把位置换成相对形式（每基元指数 + 尾数），才能把 4.92× 的近无损边界推到 8× 以上。
"""


def main() -> int:
    text = io.open(PATH, encoding="utf-8").read()
    if "M1.7 执行结果与判定" in text:
        print("already present; nothing to do")
        return 0
    if "## M1.6" not in text:
        print("ERROR: M1.6 anchor missing; refusing to append blindly")
        return 1
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text.rstrip("\n") + "\n" + BLOCK)
    print("appended %d chars" % len(BLOCK))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
