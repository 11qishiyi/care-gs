# J5 — 定性渲染网格（预注册，2026-11-18 14:40 写于开跑前）

**为什么做这一轮。** 现有 5 张图全是定量的（框架图 / 率-覆盖率 / 审计判决 / dB≠coverage / 视角级）。
该刊压缩类论文的默认配图是一张"能直接看"的定性对比；`review/JVCIR_BEST_PRACTICE_2026-11-18.md` §6 把它列为
唯一还值得花算力的缺口（G2）。本轮只做这一件事，不改任何已有数字。

**节点。** MatPool，1 区（domain 0），NVIDIA **A30** ¥2.19/h（16 区 A100 当前可租量为 0，故改用 1 区 A30；
渲染 6M 高斯单视角不需要 A100 的 40 GB）。镜像 `Pytorch 2.8.0`（ID 634333，torch 2.8.0 / CUDA 12.8）。
PLY 走 `hf-mirror.com/datasets/alexmkwizu/gaussian_training_datasets`（只含 bicycle/bonsai/stump 的 INRIA 格式
PLY），COLMAP + `images_4` 同源；不依赖上次的 `/mnt/m35cache` 缓存。

## 协议（开跑前固定，跑完只允许按此判读）

| 项 | 取值 |
|---|---|
| 场景 | `bicycle`、`stump`（与跨论文对比同一对场景） |
| 视角 | **留出视角中 clean PSNR 的中位名次那一个**（median rank），脚本自选并把名次写进 `j5_render.json` |
| 分辨率/协议 | archive 为 `images_4` 归档，`--factor 1` → 1236×822；GT 用 archive 约定（/255，不做逐图归一） |
| 臂（4） | `clean`（1.00×）· `gp6-6-6_c8_sh6`（5.07×）· `gp6-6-6_c8_sh3`（8.25×）· `p50`（Fisher 剪 50%，2.00×） |
| 码率口径 | 与 Table 9（`tab_viewlevel`）同一口径：`spec.rate_vs_fp32(deg, n_stored)`，即模型字节 |
| 放大窗 | **在 GT 上**取 200×200、步长 20 的窗口，取梯度能量最大者；编码结果不参与选窗 |
| 面板顺序 | 左：整幅 GT + 红框；右：GT / clean / 5.07× / 8.25× / 剪 50% 的裁剪块 |
| 标注 | 每块下方两行：臂名 + 码率 · 该视角 PSNR；全部从 `j5_render.json` 读，不手写 |

## 判据（写在这里，跑完照判）

| | 判据 | 通过条件 |
|---|---|---|
| **J5-C1** | 各臂的该视角 PSNR 与 Table 9 的整景 PSNR 不冲突 | 每个臂的视角 PSNR 与 Table 9 的整景值相差 ≤ 1.5 dB（单视角本就与整景不同，只查量级） |
| **J5-C2** | 定性图支持 §5.3 的主张 | 在放大窗里，8.25× 的量化臂的 PSNR **高于** 2.00× 的剪枝臂（若相反，图**不进正文**，因为它会反驳 §5.3） |
| **J5-C3** | 放大窗不是天空/纯色 | GT 窗内像素标准差 ≥ 0.02；否则按同一规则退到能量次高且 σ≥0.02 的窗，并在 JSON 里记 `fallback=true` |

三条任一不成立的处理方式：C1 不成立 → 检查是不是口径写错（先修脚本再跑，不算结果）；C2 不成立 → 图不进正文，
把该结果写进 `J5_RESULTS.md` 并在 Limitations 说明"定性上也看不出优势"（诚实优先）；C3 不成立 → 用退窗，不改判据。

## 交付物

1. `figures_j/fig6_qualitative.pdf/.png` —— 2 行 × 6 列（`tools/jvcir_fig_qual.py` 本地合成）。
2. `experiments/artifacts/a4/j5_fig_qual.json` —— 裁剪框坐标、GT 梯度能量、每臂 rate/PSNR/SSIM/LPIPS。
3. `_pull_j5/j5_render.json` + 每臂 PNG（原始渲染，作为沉积的一部分）。
4. `experiments/J5_RESULTS.md` —— 三条判据的判定 + 成本账。
5. 正文 §5.7 一段 + 图注；闸门新增一项：图 6 的标注数字必须等于 `j5_fig_qual.json`。

## 成本预估

| 阶段 | 预计 |
|---|---|
| 开机 → 镜像就绪 | 5–10 min（镜像未缓存） |
| 依赖（gsplat 1.5.3 等）+ 代码推送 | 10 min |
| PLY + COLMAP + images_4 下载（约 3 GB） | 10–20 min |
| 渲染（2 场景 × 4 臂 + clean 全留出视角） | 5–10 min |
| 拉取 + 释放 | 5 min |
| **合计** | **≈45–60 min ≈ ¥1.7–2.2** |

## 复现

```bash
# 节点上
python experiments/j5_render.py --archive /root/m360std --scenes bicycle,stump \
    --variants clean,gp6-6-6_c8_sh6,gp6-6-6_c8_sh3,p50 --out /root/res/j5 --factor 1 --device cuda
# 本地
python tools/jvcir_fig_qual.py      # 读 _pull_j5/，出 fig6 + j5_fig_qual.json
```
