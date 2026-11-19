# 投稿后应对手册（TMLR 首轮意见回来时用）

> 目的：把"看到审稿意见 → 拿出证据 / 补什么实验"的路径提前固定下来，减少回合。
> 论文：`submission/final/main.pdf`（13 页）；证据：`results_v70/`（主战役）、`results_v80/`（合并、第三任务族）、
> `results_v90/`（三准则 × 四场景、四场景任务族、逐视角残差诊断）；
> 校验：`tools/verify_tex_v3.py`（405 条断言）。

---

## 一、提交前（如果还没提交）

1. OpenReview 建稿：Title / Abstract 从 `submission/final/OPENREVIEW_SUBMISSION.md` 粘贴（已同步 v4）。
2. 上传 `main.pdf`（主文件）+ `supplementary.zip`（附件，109 项）。
3. COI / 资助 / 无人类受试者：按实际填写。

## 二、最可能出现的六条意见，以及现在的证据在哪

| 审稿人可能说 | 已有证据（直接引用即可） | 若对方坚持要补 |
|---|---|---|
| "编辑破坏保形有效性是显然的" | §1 第三段与 §5：有效性只是设置；本文测的是幅度、口径依赖、以及"有效≠可用" | 无需补，改文案 |
| "工作点太低（9–24 dB），不像可部署资产" | §3.3 四种 GT 口径全表：one-sided 会人为压低 PSNR（23.9→13.9 dB）并低估失效 2.4×；归档自报 bicycle 25.2 dB | 需要新渲染：用 archive 自带 render 复核（约 20 分钟节点） |
| "treehill 9.4 dB 是不是坏数据" | §3.1：亮度比 0.96–1.77（6/18 >1.2），5/18 视角 >5% 像素饱和（最高 11.1%），p99 残差 3.4 vs 其它 <1.7；per-view gain 可抬到 16.5 dB 但用到标签 | 已有逐视角诊断（`results_v90/stage9/treehill.json:resid_diag`），无需再跑 |
| "只有一种剪枝准则" | §2 定义三种；表 3 四场景 × 三准则：Fisher 三场景减半（−12.7/−13.3/−6.6）、flowers 反向（−19.2 vs −10.8）；opacity×volume 每场景最差（−15.8…−61.8），q 膨胀最高 +328% | 第三条之外的准则（学习型重要性/逐视角敏感度）需节点 |
| "只有一类下游任务" | 表 6（四场景 × 两预算）+ 图 2：同一编辑下 coverage / local / registration / pose 差 4–11 倍；表 4 36 格阈值扫描 | 学习型检测器/稠密 SfM 需节点 |
| "4 个场景太少" | 附录 C：5 个自训场景无效应（−0.8…+3.2）；§5 明写数据可得性限制 | 扩场景需下载（每场景 ~10 分钟 + 25 分钟 battery） |

## 三、如果审稿人要补实验：按这个顺序（成本从低到高）

> 第 1–3 项**已完成**（stage-9，2026-11-11，节点 2137301，已释放，约 ¥0.6），数据在 `results_v90/`。

1. ~~第三族/第二族扩到 4 场景~~ —— 已完成：`results_v90/second_task_stump_treehill.json`、`third_task_stump_treehill.json`；表 6 已扩到八行。
2. ~~per-view residual 诊断（treehill）~~ —— 已完成：`results_v90/stage9/*.json:resid_diag`；§3.1 已用上（饱和比例、p99）。
3. ~~第三条剪枝准则（volume/importance）~~ —— 已完成：表 3 三准则 × 四场景。
4. **微调作为编辑**：需要训练循环（gsplat simple_trainer 或 `train_gs.py`），2 场景 2–5k 步，节点 2–3 小时，**¥2**。
5. **学习型匹配器**（LoFTR/SuperGlue）：权重下载 + 集成，节点 1–2 小时，**¥1–2**。
6. **独立重采集 / 第 5–6 个场景**：扩到 6 场景最直接的软肋补强，下载 + 两个 battery，节点 ~1 小时，**¥0.6**。

所有脚本都在 `experiments/`（本轮新增 `stage9_eval.py`），流程在 `_push/stage9_driver.sh`（含提取、逐场景评测、两族任务）；
数据获取用 `fetch_hf_data.py` 或 `_push/stage9_extract.sh`（ModelScope 归档；实测 8.5 MB/s，四场景约 17 分钟）。

## 四、写作层面的现成材料

- `review/RESPONSE_TO_REVIEWERS.md`：针对我们自己审出的 14 条意见的逐条答复（可改写成实际 rebuttal）。
- `submission/PATCH_stage8.md`：上一轮补测量的论文改法（占位符已填，可作模板）；本轮改动见 git 之外的手工清单：表 3、表 6、§3.1、§3.2、§3.5、摘要、贡献列表、图 2。
- `review/V4_CHANGE_SITES.md`：本轮改动前做的"落点图"（每个受影响的句子、行号、风险清单）。
- `SUBMISSION_CHECKLIST.md` 第四节：七个"最可能被追问"的问题与答法位置。

## 五、纪律（避免自我攻击）

- 只回应被问到的问题；不要主动展开"我们没做什么"。
- 新增结果若与原结论冲突，改结论的**范围**而不是加限定词堆叠（参照 `anti-defensive-writing` 技能）。
- 每次改完立刻 `python tools/verify_tex_v3.py`，并重新打包 `tools/make_supplement.py`。
