"""Append the M7 (cluster-relative positions) pre-registration to METHOD_PLAN.md."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
## M7 规格：位置相对局部簇编码（cluster-relative positions）

预注册时间 2026-11-13 22:55，**M7 数据落盘之前**（节点尚未租用，`/workspace/res/m7`
不存在，`m7_bytes.json` / `m7_rd.json` 均未生成）。

### M7.0 动机（全部来自已落盘数据）

1. M2 的 `iso_means*` 族证明：11 个几何标量里只有 3 个位置分量贵，且**贵的不是绝对
   精度而是相对精度**——16 bit 全局网格（10 m / 65535 = 0.15 mm）在 stump 上已经掉
   1.23 pp / 0.25 dB，而 15 bit 掉 4.04 pp / 0.83 dB。只有当量化步长与基元自身的
   尺度 σ（树叶 1–2 mm、stump 更小）可比时损失才消失。
2. M5 实测轴上，全保留量化最高只到 16.1×（`d0_m16_o8_sh8`，只留 DC），近无损
   （≤1.0 pp 且 ≤0.3 dB）前沿 8.97–16.10×，但 treehill / treehill_i7k 的成员靠归档
   GT 曝光失配"加分"，严格口径只剩 6/8 资产。
3. 因此剩下的杠杆是**把位置网格从「场景包围盒」搬到「局部簇」**：同样的位宽下误差
   按块尺度而不是场景尺度缩放，这正好是 M2 指出的物理量。

### M7.1 编码器（新增，确定性、无额外边信息）

- Morton 码由**解码后位置**可复算，解码器重建同一顺序，因此不需要存索引流。
- 按 Morton 序切成 `CLUSTER_SIZE = 256` 的块；每块存 3 分量 fp32 原点 + 3 分量 fp32
  步长（`CLUSTER_HEADER_BYTES = 24.0` B/块 = 0.09375 B/基元），块内偏移量化到
  `c ∈ {6..24}` bit/分量。
- 字节：`3c/8 + 24/256` 取代 `3b_m/8`。`c12_o8_sh3` = 32.59 B（7.24×），
  `c10_o8_sh3` = 31.84 B，`c8_o8_sh3` = 31.09 B，`c12_o8_sh2` = 26.59 B（8.87×）。
- 编码器进 `experiments/m4_bytes.py::_encode`（`cluster_hdr` + `cluster_off` 两条流），
  渲染侧量化器 `qfp_rd.quantize_cluster`，字节模型在 `qfp_rd.bytes_per_prim` 与
  `m1_analyse.bytes_per_prim` 两处镜像，由 `m1_check_bytes.py` 逐名比对
  （当前 `PASS: 0 mismatch(es) over 408 case(s)`）。

### M7.2 变体（18 个，`--variant-set m7`）

`clean`；剪枝基线 `p50 p30 p20 p10 p05`（2×–20×）；全局网格锚点 `m16_o8_sh3`
`m16_o8_sh4` `m16_o8_sh2`；簇编码 `c8/c10/c12/c14_o8_sh3`、`c12_o8_sh4`、
`c12/c10_o8_sh2`；混合 `p50_c12_o8_sh3`、`p30_c10_o8_sh3`。

### M7.3 指标

与 M5 完全一致：**实测字节轴**（位平面打包 + Morton 重排 + zstd level 12，`m4_bytes`
`--skip-flat`），覆盖率损失用 `audit_bound` 协议（400 splits、α=0.1、per-split 插值、
不外推）；次指标 PSNR/SSIM/LPIPS（`--fidelity --lpips-net alex`，25/22/16/18 视角）。

### M7.4 判据

- **H1 局部编码在同字节下更准**：每资产在实测字节 ±15% 匹配窗口内，取簇族最佳与全局
  网格族最佳的覆盖率损失差 `d = drop_cluster − drop_grid`（正 = 簇更好）；要求中位
  `d ≥ +2.0 pp`、`d > 0` 的资产 ≥ 6/8。
- **H2 近无损前沿推到 ≥12×**：每资产存在**合格**成员（码率 ≥12×、绝对覆盖率损失
  ≥ −1.0 pp、`dPSNR ≤ 0.3 dB`，且**要求 `dPSNR ≥ 0`**——即排除靠归档 GT 曝光失配
  "提升"PSNR 的成员）；要求合格资产 ≥ 6/8。
- **H3 支配性在新区间成立**：以符族（cluster + 混合）对剪枝族，在 `{5,7,9,12}×` 中
  ≥4 点上 QFP 少丢 ≥3.0 pp、区间不含 0、≥6/8 资产同向（沿用 E1 的阈值与聚合）。
- 结局表：
  | H1 | H2 | H3 | 结论 |
  |---|---|---|---|
  | ✔ | ✔ | ✔ | `local_coding_holds`：位置编码主张 + 码率前沿主张都成立 |
  | ✔ | ✘ | ✔ | `local_coding_only`：局部编码成立，但前沿没推过 12× |
  | ✘ | — | ✔ | `dominance_only`：支配性仍在，但局部编码没有可测优势（写 N16） |
  | ✘ | — | ✘ | `dead_write_N16` |
- 禁止条款：不得事后改 `CLUSTER_SIZE`、块头字节、c 的取值集合、±15% 匹配窗口、
  H2 的 `dPSNR ≥ 0` 条件或码率门；不得用 `covered=false` 的码率点比较；不得只报
  有利资产。

### M7.5 执行

S0 本机 `qfp_rd.py --selftest`（含 14 项簇编码检查）、`m1_analyse.py --selftest`、
`m1_check_bytes.py`、`m4_bytes.py --selftest` —— 全部已 ALL PASS。
S1 租 A40 → setup（下载 9587304864 B 归档）→ push → `run_m1.sh dump`（`VARIANT_SET=m7`）
→ `m4_bytes --skip-flat` 测 18 配置 → `m1_analyse --bytes-json` → `m7_report.py`
→ 回传 json → **释放节点**。
S2 预算：~1.5 h ≈ ¥5（含数据流量）。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT), "chars to", P)
