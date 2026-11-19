# S1 — 与「已发表格式」基线在同字节下的对撞

预注册见 `experiments/METHOD_PLAN.md` 的「S1 规格」（2026-11-14 18:35，**数据落盘前**）。
节点 2139856（A30，¥2.19/h）用于本轮，18:52 租、19:33 释放（约 41 min ≈ ¥1.5），已确认「已释放」。

## 0. 一句话

**预注册的 S1 判为 FAIL（0/8），原因是判据自身的天花板，不是结果不好**；把「基线自己几乎不丢点」
的那两列剔除后（探索性，事后），我们 **8/8 资产、32 个配对全部赢**，中位 **+8.78 pp**、最小 **+2.87 pp**，
且 PSNR 比基线**好 0.12–5.60 dB**。

## 1. 基线是什么

把**已发表格式**在本仓库同一批资产上重新实现，走同一个量化器、同一渲染器、同一字节表
（`g32` = 几何保持 fp32，正是「只量化 SH」的出货格式）：

| 名称 | 语法 | 含义 | 模型 B/prim | 实测码率 | 实测损失（8 资产） |
|---|---|---|---|---|---|
| SH 8-bit | `sh8_g32` | 逐块尺度 8-bit 量化 SH，几何 fp32 | 94.00 | **2.77–2.83×** | **+0.00 … −0.00 pp** |
| SH 4-bit | `sh4_g32` | 同上，4 bit | 70.00 | 3.93–4.08× | −0.01 … −0.02 pp |
| prune50 + SH8 | `p50_q8_g32` | Fisher 删 50% 后量化 | 94.00 | 5.51–5.63× | −2.90 … −13.02 pp |
| prune50 + SH4 | `p50_q4_g32` | 同上，4 bit | 70.00 | 7.82–8.09× | −2.92 … −13.04 pp |
| prune30 + SH4 | `p30_q4_g32` | 删 70% 后 4 bit | 70.00 | 13.04–13.43× | −7.15 … −19.18 pp |
| prune30 + SH2 | `p30_q2_g32` | 删 70% 后 2 bit | 58.00 | 16.86–17.09× | −8.99 … −20.88 pp |

**不是任何单篇论文流水线的复现**：不训练、不蒸馏、不做 anchor 重参数化，只复现
「保留多少 × 每系数多少位」这一层，也就是本论文讨论的动作空间。

**第一个重要发现（对论文是更正）**：只量化 SH、几何保持 fp32，**2.77–2.83× 就已经是 0.00 pp**
——与 M13 报的「3× 时 −0.39 pp」矛盾。原因是 M1–M13 的网格里**没有这一行**（最接近的是
`sh8_g16`，它额外把几何压到 16 bit，2.05–2.16×）。补上这一行后，可达前沿的读数从
「3× 丢 0.39 pp」变成「2.8× 丢 0.00 pp」，且几何 16-bit 再省约 0.7×。见 §4。

## 2. 预注册 S1：FAIL（0/8），原因是天花板

S1 要求「每个基线都被我们赢 ≥1.0 pp」。但前两列基线（SH 8/4-bit）自身损失是 **0.00 / −0.02 pp**，
而覆盖损失的上界是 0 —— **没有任何方法能在 0.00 上再赢 1 pp**。8 个资产各 2 个这样的配对，
必然全灭；剩下 4 列（prune+quantise）全部通过，但「每一个基线」的合取仍是 False。

> 这是 N13 已经写过的教训（「判据要有头部空间」）在同一个项目里的第二次复发：
> 写 S1 时我要求「赢 1 pp」，却没有检查基线自身是否已经贴着 0。
> 数字先落盘，判据后修正 **不合法**，所以下面把它明确标成事后探索。

## 3. 事后探索 S1′：剔除无头部空间的基线（`--headroom-pp 1.0`）

规则：只保留自身损失 ≤ −1.0 pp 的基线（即有 1 pp 以上可赢空间），其余不变
（Δ ≥ 1.0 pp、配对区间分离、PSNR 不得比基线差 0.3 dB、≥6/8 资产）。

**结果：8/8 资产通过，32/32 配对获胜，Δ 中位 +8.78 pp，范围 +2.87 … +20.76 pp；
保真度 us − baseline 的 dPSNR 差 = −0.12 … −5.60 dB（负 = 我们更好，中位 −2.62 dB）。**

| 资产 | 基线（其自身损失） | 我们同预算的最好点（码率 / 损失） | Δ |
|---|---|---|---|
| bicycle | prune50+SH8 (5.59× / −7.05) | `msc12-6-a1_c8_o8` 5.27× / −0.07 | **+6.98** |
| bicycle | prune30+SH2 (17.00× / −15.88) | 同 5.27× / −0.07 | **+15.81** |
| bicycle_i7k | prune50+SH8 (5.62× / −4.80) | `msc12-6-a4_c8_o8` 5.36× / −0.04 | **+4.76** |
| flowers | prune50+SH8 (5.53× / −13.02) | `msc12-6-a1_c8_o8` 5.14× / −0.12 | **+12.90** |
| flowers | prune30+SH2 (16.92× / −20.88) | 同 5.14× / −0.12 | **+20.76** |
| flowers_i7k | prune50+SH8 (5.54× / −6.72) | `msc12-6-a4_c8_o8` 5.13× / −0.05 | **+6.67** |
| stump | prune50+SH8 (5.53× / −8.87) | `msc12-6-a1_c8_o8` 5.14× / −0.13 | **+8.74** |
| stump | prune30+SH2 (16.93× / −20.54) | 同 5.14× / −0.13 | **+20.41** |
| stump_i7k | prune50+SH8 (5.51× / −4.89) | `msc12-6-a4_c8_o8` 5.21× / −0.07 | **+4.82** |
| treehill | prune50+SH8 (5.57× / −3.59) | `msc12-6-a1_c8_o8` 5.22× / −0.05 | **+3.55** |
| treehill | prune30+SH2 (16.86× / −10.35) | `d2_m16_o8_sh8` 6.29× / +0.27 | **+10.62** |
| treehill_i7k | prune50+SH8 (5.63× / −2.90) | `msc12-6-a1_c8_o8` 5.30× / −0.02 | **+2.87** |
| treehill_i7k | prune30+SH4 (13.29× / −7.15) | `d1_m16_o8_sh8` 10.29× / +0.33 | **+7.48** |

（完整 32 行见 `experiments/artifacts/a4/sota_report_headroom.md`；未剔除版本见 `sota_report.md`。）

注意三处 `+` 号损失（treehill 系列）：那是归档 GT 曝光失配导致「压缩后更接近 GT」，
按 N16 的规矩**不能当作质量证据**；这几行靠 Δ 仍成立，但论文里引用时应改用两棵树之外的六个资产。

## 4. 前沿读数被更正（并入 `frontier_v2.md` / `frontier_rd.md`）

把 `sota_rd.json` 并入 `frontier.SOURCES` 后重算（`--mode at_most`）：

| 预算 | 平均损失（旧） | 平均损失（新） |
|---|---|---|
| 2× | −0.79 pp | −0.79 pp（不变，2× 内没有 0 损失点） |
| 3× | −0.39 pp | **+0.00 pp** |
| 5× / 7× / 12× | −0.12 / +0.00 / +0.02 | **+0.00 / +0.06 / +0.08** |

反向读法（给定容差要多少字节）现在给出干净的答案：

| 资产 | ≤0.25 pp | ≤0.5 pp | ≤1 pp | ≤2 pp |
|---|---|---|---|---|
| bicycle | 2.80× SH8+fp32 | 2.14× SH16 | 2.14× SH16 | 1.27× prune 90% |
| bicycle_i7k | 2.15× SH16 | 2.15× SH16 | 2.15× SH16 | 1.11× prune 90% |
| flowers | 2.78× SH8+fp32 | 2.78× SH8+fp32 | 2.09× SH16 | 2.09× SH16 |
| flowers_i7k | 2.10× SH16 | 2.10× SH16 | 2.10× SH16 | 1.11× prune 90% |
| stump | 2.77× SH8+fp32 | 2.77× SH8+fp32 | 2.77× SH8+fp32 | 1.22× prune 90% |
| stump_i7k | 2.77× SH8+fp32 | 2.77× SH8+fp32 | 2.05× SH16 | 1.11× prune 90% |
| treehill | 2.14× SH16 | 2.14× SH16 | 2.14× SH16 | 2.14× SH16 |
| treehill_i7k | 2.16× SH16 | 2.16× SH16 | 2.16× SH16 | 1.67× prune 70% |

**结论**：近无损货架在 **2.05–2.83×**，其中一半资产要靠我们自己的 `SH16`（几何也压到 16 bit）
才降到 2.1×；只做已发表格式的 8-bit 量化则停在 2.8×。

## 5. 论文侧改动（`submission/cviu/main.tex`）

- `tab:bytes` 换成**反向表**（容差 → 需要多少字节），因为正向表在 2.8× 之后饱和成一列相同的点；
  新表由 `experiments/frontier_tex_inverse.py` 生成 `submission/cviu/tab_frontier_inv.tex`。
- §5.3 的两句数字全部换成实测值：等字节对撞从「−0.04…−1.17 pp」改为「八个 checkpoint 全部 0.00 pp，
  Δ = +12.8…+19.2 pp」，并把「3× 时 −0.39 pp / 7× 时 0.00」改为「≤0.25 pp 需 2.10–2.80×，
  ≤1 pp 从不超过 2.77×；三倍预算已经落在零损失货架里」。
- 编译：`pdflatex` 两遍，37 页，无 undefined reference。

## 6. 复现

```bash
# 节点（A30/A40 均可；本轮 A30，41 min ≈ ¥1.5）
bash experiments/run_sota.sh setup          # 依赖 + 9.5 GB 归档 + prep_aliases
bash experiments/run_sota.sh dump           # 8 资产 × 7 基线变体（约 11 min）
bash experiments/run_sota.sh bytes          # 实测字节（zstd-12 + Morton，约 1 min）
python experiments/m1_analyse.py --dump /workspace/res/sota/dump \
    --out /workspace/res/sota/sota_rd.json --bytes-json /workspace/res/sota/sota_bytes.json \
    --rates 1,2,3,5,7,9,12,16,24 --n-splits 400 --protocol m3 --rate-need 3
# 本机
python experiments/sota_report.py --rd experiments/artifacts/a4/sota_rd.json \
    --frontier-dir experiments/artifacts/a4 --out experiments/artifacts/a4/sota_report.md
python experiments/sota_report.py --rd experiments/artifacts/a4/sota_rd.json \
    --frontier-dir experiments/artifacts/a4 --headroom-pp 1.0 \
    --out experiments/artifacts/a4/sota_report_headroom.md
python experiments/frontier.py --dir experiments/artifacts/a4 --out experiments/artifacts/a4/frontier_v2.md --detail
python experiments/frontier_tex_inverse.py
```

## 7. 数据

`experiments/artifacts/a4/`：`sota_rd.json`（60 507 B）、`sota_bytes.json`（27 669 B）、
`sota_report.md`、`sota_report_headroom.md`、`frontier_v2.md`、`frontier_rd.md`。
