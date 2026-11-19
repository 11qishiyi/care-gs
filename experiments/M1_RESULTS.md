# M1 (QFP) —— 先压精度，后减数量的等字节率失真结果

状态：**已完成，预注册判据通过（outcome `method_holds`）**。
预注册规格见 `experiments/METHOD_PLAN.md` 的「M1 规格：QFP」（2026-11-13 15:40），
本文只报告执行结果，不改判据、不改码率点、不改变体集。

- 数据：`experiments/artifacts/a4/m1_rd.json`（97 KB，含 400 split 的逐 split 配对）、
  `m1_rd_digest.json`（36 KB，摘要）、`m1_report.md`（本文表格的生成物）。
- 生成器：`experiments/m1_analyse.py`（CPU，12 分钟/4 场景）→ `experiments/m1_report.py`。
- 实验：节点 2139188（A40 40 GB），4 个 archive 场景 × 35 变体 × 25 held-out 视角，
  dump 28 分钟（含 SSIM/LPIPS），analyse 12 分钟，总计约 ¥2。

---

## 1. 结论

**在相同字节预算下，把比特花在精度上严格优于把比特花在删基元上，且差距随码率增大。**

| 码率 | QFP 覆盖损失（4 场景均值） | 剪枝基线（Fisher 对角） | Δ | QFP 的 PSNR 优势 |
|---|---|---|---|---|
| 2.0× | **−0.43 … −1.17 pp**（均值 −0.56） | −3.59 … −13.02 pp（均值 −8.13） | **+7.57 pp** [+3.50, +9.21] | **+1.82 dB**（最差场景 +0.10） |
| 3.0× | **−0.43 … −1.17 pp** | −7.38 … −17.91 pp（均值 −12.32） | **+11.76 pp** [+7.30, +14.19] | **+3.02 dB**（最差 +0.33） |
| 5.0× | **−0.09 … −5.38 pp** | −12.91 … −23.20 pp（均值 −19.53） | **+16.32 pp** [+11.77, +20.73] | **+3.59 dB**（最差 +0.65） |

判据（`m1_rd.json → summary.criteria`）：

- **D1 覆盖支配：PASS**（3/3 有对照的码率点，每点 4/4 场景同向、区间不含 0、最小场景 +3.50 pp）
- **D2 保真不劣：PASS**（3/3 点；PSNR/SSIM 均更好，LPIPS 均更低——不是「打平」，是全胜）
- **D3 近无损档存在：PASS**（2.0×/3.0×/5.0× 各有 ≥3 个场景存在成员满足 ≤1.0 pp 且 ≤0.3 dB）

> 注：7×/9×/12×/16×/24× 没有对照，因为剪枝族上限是 `p20 = 5.00×`。判据明令禁止外推，
> 所以 D1/D2/D3 的分母是 8 个码率点、分子是 3 个（`rates_passing: 3 / rates_total: 8`）。

## 2. 免费压缩的上限是 4.92×（`sh4_g16`）

四个场景在 4.92×（48 B/prim）上的代价：

| 场景 | clean PSNR | `sh4_g16` PSNR | ΔPSNR | 覆盖损失 | SSIM 变化 |
|---|---|---|---|---|---|
| bicycle | 22.24 | 22.11 | −0.12 dB | −0.46 pp | 0.7644 → 0.7541 |
| flowers | 16.77 | 16.68 | −0.09 dB | −0.60 pp | 0.6052 → 0.6039 |
| stump | 23.90 | 23.65 | −0.26 dB | −1.22 pp | 0.7501 → 0.7478 |
| treehill | 9.41 | 9.38 | −0.03 dB | −0.74 pp | 0.6335 → 0.6318 |

对照：剪枝要达到 5.00× 必须丢掉 80% 的基元，代价是 −5.30/−4.67/−5.91/−0.68 dB 与
−20.43/−23.20/−20.79/−12.91 pp。**同样的字节，一个几乎看不见，一个塌掉。**

## 3. 机制：11 个几何标量里只有 3 个（位置）贵

`iso_*` 族把单个属性组压到 8–12 bit、其余保持 fp32（覆盖率损失 pp / ΔPSNR dB）：

| 场景 | `iso_scales8` | `iso_quats8` | `iso_opac8` | `iso_means12` | `iso_means10` |
|---|---|---|---|---|---|
| bicycle | +0.02 / 0.00 | −0.01 / −0.01 | −0.01 / −0.00 | **−19.01 / −4.60** | **−40.32 / −7.99** |
| flowers | −0.00 / +0.01 | −0.00 / +0.00 | −0.00 / +0.01 | **−16.12 / −2.66** | **−27.44 / −4.63** |
| stump | −0.01 / +0.01 | −0.00 / −0.00 | −0.00 / −0.00 | **−33.04 / −6.28** | **−53.69 / −9.05** |
| treehill | −0.00 / +0.00 | −0.00 / +0.00 | −0.00 / +0.00 | **−14.20 / −0.52** | **−20.95 / −0.81** |

读法：尺度/旋转/不透明度在 8-bit 上**完全免费**（0.01 pp、0.01 dB 量级，且有的场景是正的），
位置在 12-bit 上就已经毁掉一半以上的覆盖率。全局 min–max 网格把 10 米尺度切成 4096 份
= 2.4 mm，而树叶基元的 σ 只有 1–2 mm——**位置的误差预算必须相对于基元自身的尺寸，
不能相对于场景尺寸**。这一条直接给出了 M2 的方向（属性级精度地板 / 位置相对编码）。

`sh*_g16` 族进一步说明 SH 位宽也几乎免费：`sh16_g16`（1.97×）与 `sh4_g16`（4.92×）在
bicycle 上的覆盖率损失都是 −0.43/−0.46 pp、PSNR 22.14/22.11——**把 SH 从 16 bit 砍到
4 bit 只花 0.03 dB**。

## 4. 为什么 5.55× 以上的 QFP 点会崩（`q*_g12`）

`q6_g12 / q4_g12 / q3_g12 / q2_g12` 全部继承 `g12`（几何 12 bit）的伤害：bicycle −19.0 pp /
−4.60 dB，stump −33.0 pp / −6.28 dB。**它们不是「量化到 5.55× 崩了」，而是「位置在 12 bit
崩了」**——SH 部分从 6 bit 一路降到 2 bit 只额外加了 0.1–2.8 pp。这解释了 M1 网格里
QFP 曲线在 4.92× 之后突然下坠：那是几何网格的悬崖，不是量化的悬崖。

## 5. 变体表（bicycle，全部 35 个变体的字节模型与代价）

见 `experiments/artifacts/a4/m1_report.md` 第 3 张表（由 `m1_report.py` 生成，
两列都是相对 clean 的**损失**：覆盖率损失为负、PSNR 损失为正都表示更差）。

字节模型（预注册，逐字）：`bytes/prim = 11·b_geo/8 + 3K·b_sh/8 + 2`，
K=16、fp32 = 236 B/prim；`rate_vs_fp32 = 236 / (bpp · keep)`。

## 6. 注意事项（写论文时不能忽略）

1. **treehill 的 PSNR 不可引用**：clean 只有 9.41 dB，是归档 GT 的曝光失配（已知问题，
   见 `experiments/a4_exposure_check.py`）。它的覆盖率与 SSIM/LPIPS 可用，PSNR 只用来看
   *相对*差值。
2. **stump 是唯一「16-bit 几何也不完全免费」的场景**：`sh16_g16` 已经掉 −1.17 pp / −0.24 dB，
   而其它三个场景是 −0.09 … −0.57 pp / −0.00 … −0.07 dB。stump 的基元最密（4.29M）、
   σ 最小，正好落在「绝对网格精度不够」的那一侧，也是 M2 必须解决的场景。
3. **PSNR 符号**：`rows[].d_psnr = clean − variant`（正数=损失）；
   `comparisons[].psnr.diff = qfp − prune`（正数=QFP 更好）。两张表符号含义相反，别看错。
4. **`p*_q*` 混合族与同保留率剪枝的覆盖率差 0.00 pp**（bicycle `p50` 与 `p50_q4_g12` 的
   损失差 0.01 pp）：SH 量化在剪枝之后几乎不增加伤害，也就是说 **A4 的「量化免费」结论
   在 M1 的诚实字节模型下依然成立**，但**几何量化不是免费的**——A4 没测过几何。
5. 覆盖率协议与 `audit_bound.py` 完全一致（400 split 配对、alpha=0.1、q 只由 clean 的
   cal 半决定、dep 半评估），由 `m1_check_bytes.py` 与 `a4_verify_fast.py` 双重校验。

## 7. 复现

```bash
# 节点（A40，已装 gsplat 1.5.3 + plyfile + packaging + scikit-image + lpips）
cd /workspace/code
nohup bash experiments/run_m1.sh setup  > /workspace/res/m1_setup.log 2>&1 &
bash experiments/run_m1.sh smoke                 # bicycle, 4 views, 7 variants
nohup bash experiments/run_m1.sh dump > /workspace/res/m1_dump.log 2>&1 &   # 28 min
bash experiments/run_m1.sh analyse                # 12 min, CPU
python3 experiments/m1_report.py --json /workspace/res/m1/m1_rd.json --rates 2,3,5
```

本机（无 GPU）可复算的部分：

```powershell
python experiments\m1_check_bytes.py                     # 字节模型 CPU/GPU 两侧一致
python experiments\m1_analyse.py --selftest              # 合成世界 + 反向世界的判据自检
python experiments\m1_report.py --json experiments\artifacts\a4\m1_rd.json --rates 2,3,5
```

## 8. 对后续的意义

- **D1 成立 → 动作空间的选择（精度 vs 数量）比排序准则重要得多**，这是 M1 的方法论主张，
  也是论文里可从 N13 直接接上的叙事：A1–A3 在「排序」里失败了四轮，M1 换了动作空间，
  一次就拿到 +7.6/+11.8/+16.3 pp。
- **D2 与 D3 同时成立 → 「等字节下 QFP 不让画质」**，所以不需要在覆盖率与 PSNR 之间选边，
  也就不需要「用覆盖率换 PSNR」的辩解。
- **M2 的目标由第 3 节直接给出**：位置的误差预算必须相对基元尺寸。现状 `sh4_g16` 在
  4.92× 处已经几乎免费，但 B 里 8 个几何分量仍按 fp32 的 44 B 记账；M2 要把位置换成
  「每基元指数 + 尾数」的形式，把 44 B 压到 ~13 B，从而在 8–10× 上继续保持近无损。
