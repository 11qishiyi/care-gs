# RUNBOOK 2026-11 — 变体剂量扩展实验（GPU 渲染一次 → CPU 复算全部数字）

给 Lead 在节点 **2138004** 上照着抄的逐条命令。每一步都写了**预期产物**和**失败时的排查点**。
分工：§1 在本机推代码，**Lead 在节点上执行 §2–§7**，产物传回后 §8 在本机纯 CPU 复算。

代码版本（本次交付，已在本机 CPU 验证过）：

| 文件 | 作用 | 本地验证状态 |
|---|---|---|
| `experiments/dump_artifacts.py` | **GPU**：每场景 × 每变体渲染每张留出视角 → `<scene>.npz`；本次新增 `quant4` / `quant6` / `shdeg2`（opt-in） | `--dry-run` 通过；默认 6 变体输出**逐字节不变**；`quant8` 与新实现**逐位相同**（`tests/test_extend_eval.py` 断言） |
| `experiments/extend_eval.py` | **CPU**：`<scene>.npz` → `extend_eval.json` + 附录 markdown 表（部署侧覆盖率 / 配对降幅 / q 增长 × pixel 与 64×64 block） | `--dry-run` 通过；pixel/block 数字与 `region_coverage.py` 逐行一致到 1e-9（7 变体 28 行，`max |drop diff| = 0.00e+00`） |
| `experiments/tests/test_extend_eval.py` | CPU 测试（9 个用例 / 67 条断言） | `python -m pytest experiments/tests/test_pipeline_cpu.py experiments/tests/test_extend_eval.py -q` → **19 passed** |

> 本机 `pytest experiments/tests` 会顺带收到 `test_new_tools.py`，它 import `plyfile`（本机未装）→ **1 failed 是既有环境问题**，与本次改动无关；只跑上面两个文件即可 19 passed。

---

## 0. 节点事实卡（已核实，不要再探测）

| 项 | 值 |
|---|---|
| 节点 id | `2138004` |
| GPU | A40 **49 GB** 显存 |
| 系统 | Ubuntu；`python` = `/root/miniconda3/envs/myconda/bin/python`（**3.11.13**） |
| 框架 | torch **2.6.0+cu124**，**gsplat 已装** |
| 磁盘 | `/` 空闲 **344 GB** |
| 归档 | 正在下载到 `/data/output-3dgs.tar.gz`（ModelScope `Jackie137/3dgs-Output`，**9.59 GB**，tar.gz） |
| 归档内容（预期） | `output/<scene>/{cameras.json, point_cloud/iteration_40000/point_cloud.ply, test/ours_40000/gt}` |
| 传文件 | 本地→节点 `tools/push_to_node.ps1`；节点→本地 `tools/fetch_results9.ps1` 的模式（见 §6，**本次有大文件警告**） |

工具名缩写（下文统一用）：

```bash
PY=/root/miniconda3/envs/myconda/bin/python
REPO=/workspace/code          # 节点上的代码根，必须同时含 experiments/ 与 research/code/
ARCH=/workspace/data          # 归档根：ARCH/output/<scene>/...  ← 契约
RES=/workspace/res            # 产物根
VARS=clean,prune50,prune30,shdeg1,quant8,quant4,quant6
```

> `matcli node exec` 每次都是**独立 shell**：`export` 不跨调用，`cd` 也不跨调用。
> 所以下面每段命令都是**自包含**的；用 `matcli node exec` 时把整段用 `&&` 或 `;` 串成一条命令，
> 或者写成 `--command "bash -lc '...'"`。超过 ~90 s 的步骤（解包、pip）必须提高 `--idle-timeout` 或放后台。

---

## 1. 前置：把代码推上去（本机执行）

`dump_artifacts.py` 用 `common.add_code_root()` 定位 `research/code`，**目录相对位置必须保持**：
`<根>/experiments/*.py` 与 `<根>/research/code/calib/*.py`。
而 `push_to_node.ps1` 只保留**一层**子目录（取父目录的 leaf），所以要分两批、用不同的 `-RemoteRoot`：

```powershell
cd D:\3dsg_1
$node = 2138004

# 批 1：experiments/  →  /workspace/code/experiments/
pwsh -File tools\push_to_node.ps1 -NodeId $node -RemoteRoot /workspace/code `
  -FileList 'experiments\common.py;experiments\dump_artifacts.py;experiments\extend_eval.py;experiments\region_coverage.py;experiments\build_archive.py'

# 批 2：calib/        →  /workspace/code/research/code/calib/
pwsh -File tools\push_to_node.ps1 -NodeId $node -RemoteRoot /workspace/code/research/code `
  -FileList 'research\code\calib\__init__.py;research\code\calib\archive_only.py;research\code\calib\gsrender.py;research\code\calib\colmap_io.py;research\code\calib\plyio.py'
```

预期产物：每个文件一行 `PUSHED <name> -> <remote>  local=<n>B remote=<n>B`（两边字节数必须相等）。
排查：`SKIP missing <f>` = 本地路径错了（必须从 `D:\3dsg_1` 下发起）；`remote=0B` = 分块没写进去，重推该文件。

推完在节点上验证**布局 + 语法 + 依赖**（一次 exec，纯 CPU）：

```bash
/root/miniconda3/envs/myconda/bin/python -c "
import sys; sys.path.insert(0,'/workspace/code/experiments')
import common, dump_artifacts as D, extend_eval as E, region_coverage as R
print('imports ok | VARIANTS', D.VARIANTS, '| opt-in', D.DOSE_VARIANTS)"
```

预期：`imports ok | VARIANTS ['clean', 'prune50', 'prune30', 'pup30', 'shdeg1', 'quant8'] | opt-in ['quant6', 'quant4', 'shdeg2']`

依赖预检（**必须做**：`calib/plyio.py` 用 `plyfile`，`colmap_io.load_images` 用 `PIL`，gsplat 也可能回落到这条路径）：

```bash
/root/miniconda3/envs/myconda/bin/python -c "
import importlib, gsplat
print('gsplat.load_ply_to_splats:', hasattr(gsplat, 'load_ply_to_splats'))
for m in ('numpy','torch','gsplat','plyfile','PIL'):
    try:
        mod=importlib.import_module(m); print(m,'OK',getattr(mod,'__version__','?'))
    except Exception as e:
        print(m,'MISSING',e)"
```

预期：五行 `OK`。如果 `plyfile` 缺 → `PY -m pip install plyfile`（纯 python，秒级）；`PIL` 缺 → `PY -m pip install pillow`。
若 `gsplat.load_ply_to_splats: False`，`load_splats` 会回落到 `plyio`，**这时 `plyfile` 是硬依赖**。

---

## 2. 解包 → 建 archive 布局（`build_archive.py` 的契约）

所有 `calib` 加载器（`archive_only.load_archive_only_scene`）只认这一种布局：

```
ARCH/output/<scene>/cameras.json
ARCH/output/<scene>/point_cloud/iteration_40000/point_cloud.ply
ARCH/output/<scene>/test/ours_40000/gt/<j:05d>.png     ← j 是「按 img_name 排序后 i%8==0」的第 j 个相机
ARCH/output/<scene>/test/ours_40000/renders/...        ← 可选，不读
```

`test/.../gt` 与 `cameras.json` 的对应关系是**本仓库全部数字的地基**：`llffhold=8`，相机按 `img_name`
排序，第 `j` 个留出相机的 GT 必须叫 `<j:05d>.png`。`build_archive.py` 就是照这个契约拼的（`sel=[i for i in
range(len(cams)) if i%8==0]`，再按顺序写 `f"{j:05d}.png"`）。

### 2.1 确认归档下载完成 + 看目录结构

```bash
ls -l /data/output-3dgs.tar.gz && df -h / /data /workspace
tar -tzf /data/output-3dgs.tar.gz | head -6
```

预期：`9.59 GB` 左右；`head` 打出 `output/flowers/cameras.json`、`output/flowers/point_cloud/iteration_40000/point_cloud.ply`、`output/flowers/test/ours_40000/gt/00000.png` 一类路径。

- 如果第一条不是 `output/` 而是 `output-3dgs/output/...`（多一层壳）→ 解包时加 `--strip-components=1`。
- 如果 `ls` 还在变大（下载没结束）→ **等**，别解包半个文件。

### 2.2 解包

```bash
mkdir -p /workspace/data
tar -xzf /data/output-3dgs.tar.gz -C /workspace/data
ls /workspace/data/output
```

预期：`bicycle  flowers  stump  treehill`（顺序无关）。
排查：`tar: Unexpected EOF` = 下载没完成；只有 2–3 个场景 = 归档本身不全（记录缺哪些，后面 `--scenes` 用实际有的）。

### 2.3 判断要不要 `build_archive.py`（**先检查，别急着拼**）

```bash
/root/miniconda3/envs/myconda/bin/python - <<'PY'
import json, os
ARCH="/workspace/data"
for sc in "flowers,bicycle,treehill,stump".split(","):
    base=os.path.join(ARCH,"output",sc)
    camsp=os.path.join(base,"cameras.json")
    ply=os.path.join(base,"point_cloud","iteration_40000","point_cloud.ply")
    gtd=os.path.join(base,"test","ours_40000","gt")
    if not (os.path.isfile(camsp) and os.path.isfile(ply)):
        print(f"{sc:9s} MISSING cameras.json / point_cloud.ply  <-- 归档不全"); continue
    cams=json.load(open(camsp)); cams.sort(key=lambda c: c["img_name"])
    n_test=len([i for i in range(len(cams)) if i%8==0])
    gt=sorted(os.listdir(gtd)) if os.path.isdir(gtd) else []
    flag="OK" if len(gt)==n_test else f"** gt={len(gt)} != test={n_test} **"
    print(f"{sc:9s} cams={len(cams):4d} test={n_test:3d} gt={len(gt):3d} "
          f"ply={os.path.getsize(ply)/2**30:.2f}GiB {flag}")
PY
```

预期（4 行，每行末尾 `OK`）：`gt == test == 相机数中 i%8==0 的个数`（Mip-NeRF360 上每场景 16–25）。

- **全部 `OK`** → 归档自带 GT，**跳过 2.4**，`ARCH=/workspace/data` 直接用。
- `gt=0` 或缺文件 → 需要拼 GT：走 2.4（要另外有 Mip-NeRF360 原图）。
- `gt` 与 `test` 数量不等但都 >0 → 加载器会打 `[warn] N gt files vs M test cameras` 并取 `min(n_gt, n_sel)`；
  这会让视图数偏离论文口径。**别硬跑**，先回报 Lead（这是数据问题，不是代码问题）。

### 2.4 （仅在 2.3 报缺 GT 时）拼 GT

`build_archive.py` 需要两样东西：`--models`（有 `output/<scene>/cameras.json` + ply，就是刚解包的 `/workspace/data`）
和 `--images`（Mip-NeRF360 原图，含 `<images>/<scene>/images_4`）。节点上没有原图就得先下载数据集；
**这一支是备用路径**，优先确认 2.3 是否真的缺。

```bash
PY=/root/miniconda3/envs/myconda/bin/python
$PY /workspace/code/experiments/build_archive.py \
  --models /workspace/data --images /workspace/data/mip360 \
  --archive /workspace/data/official --scenes flowers,bicycle,treehill,stump \
  --llffhold 8 --report /workspace/res/archive_build.json
```

预期：每场景 `[scene] cameras=N test=M matched=M missing=0`，最后打印 report；产物在 `/workspace/data/official/output/<scene>/...`。
此时把 `ARCH` 改成 `/workspace/data/official`（**两种布局不能混用**）。
排查：`missing>0` = 原图文件名与 `cameras.json.img_name` 不匹配（Mip-NeRF360 的 `_4` 后缀）；
`no point_cloud.ply` = `--models` 指错了层级（要指到含 `output/` 的那一层）。

---

## 3. 逐场景 dry-run 自检（纯 CPU：布局 + SH 阶数 + 视图数）

**不要**直接跑正式 dump。先做两个 30 秒检查——它们对应两个真实的坑（视图数错、SH 阶数不是 3）。

### 3.1 视图数 / 图像尺寸（走真正的 loader，不碰 GPU）

```bash
/root/miniconda3/envs/myconda/bin/python - <<'PY'
import sys; sys.path.insert(0,"/workspace/code/research/code")
from calib.archive_only import load_archive_only_scene
for sc in "flowers,bicycle,treehill,stump".split(","):
    s=load_archive_only_scene("/workspace/data", sc, factor=4, cal_frac=0.5)
    print(f"{sc:9s} W,H={s['width']}x{s['height']} n_views={len(s['image_paths'])} "
          f"cal={len(s['cal_idx'])} dep={len(s['dep_idx'])} first={s['names'][0]}")
PY
```

预期：`W,H=259x389`（Mip-NeRF360 factor 4 的典型值，不同场景可能 259x389 / 194x259 等），
`n_views` = §2.3 的 `gt` 数，`cal = max(2, n//2)`。
排查：出现 `[warn] ... gt files vs test cameras` → 回 §2.3；`n_views < 4` → 协议跑不了（`extend_eval` 会直接拒绝）。

### 3.2 SH 阶数（`shdeg1`/`shdeg2` 是否真的有剂量）

只读 PLY 头部（1.5 GB 的 PLY 也只要毫秒级）：

```bash
/root/miniconda3/envs/myconda/bin/python - <<'PY'
for sc in "flowers,bicycle,treehill,stump".split(","):
    p=f"/workspace/data/output/{sc}/point_cloud/iteration_40000/point_cloud.ply"
    head=[]
    with open(p,"rb") as f:
        while True:
            ln=f.readline().decode("ascii","replace").strip(); head.append(ln)
            if ln=="end_header" or not ln: break
    n=int([h for h in head if h.startswith("element vertex")][0].split()[-1])
    k=len([h for h in head if h.startswith("property float f_rest_")])//3
    deg=round((k+1)**0.5)-1
    print(f"{sc:9s} n_prims={n:9,d} shN={k:2d} SH_degree={deg} "
          f"{'OK' if deg==3 else '** shdeg2 在这个场景是 no-op **'}")
PY
```

预期：`shN=15 SH_degree=3`。若某场景是 2 阶（`shN=3`），该场景的 `shdeg2` 会是 no-op
（`render` 里 `min(sh_degree, splats.sh_degree)`）；**现在的代码会直接拒绝**而不是静默出重复行：
`SystemExit: <scene>/shdeg2: the checkpoint already has SH degree 2 ...`。
遇到就从这个场景/这次 `--variants` 里去掉 `shdeg2`，并在报告里注明该场景没有 SH 剂量点。

### 3.3 一张图走完整条 GPU 路径（每场景 2 个视图 × 2 个变体）

```bash
cd /workspace/code
/root/miniconda3/envs/myconda/bin/python experiments/dump_artifacts.py \
  --archive /workspace/data --scenes flowers,bicycle,treehill,stump \
  --variants clean,quant4 --max-views 2 --out /workspace/res/smoke --device cuda \
  2>&1 | tee /workspace/res/smoke.log
```

预期（每场景 4 行 + 1 行写盘）：
`=== flowers: <N> primitives, 2 held-out views, 259x389 (factor 4)` → `clean PSNR=16~20 dB resid mean=0.05~0.15`
→ `quant4 ...` → `wrote /workspace/res/smoke/flowers.npz ~2MB ... V=2`。

- PSNR **< 12 dB** 或 `resid mean > 0.3` → GT 口径不对（`normalize_exposure` 之后 GT 均值应为 0.40），
  **停下来回报**，不要继续烧正式 run。
- `CUDA out of memory` → 该场景 primitive 数太大：加 `--max-views 1` 重试；仍 OOM 就回报（A40 49 GB 正常不该 OOM）。
- `KeyError`/`AttributeError` 在 `load_splats` → 回 §1 的依赖预检（`plyfile` / `gsplat.load_ply_to_splats`）。
- 自检产物 `/workspace/res/smoke` 用完即可删，**不要**和正式 `dump/` 混在一起（只有 2 视图，`extend_eval` 会拒绝）。

---

## 4. 正式 dump（7 变体 × 4 场景）

```bash
cd /workspace/code
/root/miniconda3/envs/myconda/bin/python experiments/dump_artifacts.py \
  --archive /workspace/data --scenes flowers,bicycle,treehill,stump \
  --variants clean,prune50,prune30,shdeg1,quant8,quant4,quant6 \
  --out /workspace/res/dump --device cuda --budget-mb 45 \
  2>&1 | tee /workspace/res/dump.log
```

关键点（**别加 `--profile`**，见 §10 坑 1）：

* 默认 `VARIANTS`（6 个）**不含**新的剂量变体，必须用 `--variants` 显式点名；`--profile core/compact` 会把
  `--variants` 覆盖掉。日志第一行应打印
  `profile=full variants=clean,prune50,prune30,shdeg1,quant8,quant4,quant6 downsample=1`。
* `--budget-mb 45`：7 变体在 factor-4 上约 39–45 MB/scene，用默认 30 会刷 `[warn]`，无害但会掩盖真问题。
* `pup30` **不在**本次名单里，所以不需要 `make_pup_variant.py`，也不需要 `--pup-dir`。

预期产物：

```
/workspace/res/dump/{flowers,bicycle,treehill,stump}.npz      # 每场景 ~40MB（7 变体）
/workspace/res/dump/dump_summary.json                          # ~100KB，含每变体 PSNR / resid / per-view 表
```

日志判据（每场景每变体一行，共 28 行 + 4 行写盘）：
`clean / prune50 / prune30 / shdeg1 / quant8 / quant4 / quant6`，且 `n=` 满足
`clean == shdeg* == quant* == 2.4M(量级)`，`prune50 ≈ 0.5×clean`、`prune30 ≈ 0.3×clean`；
PSNR 单调性 `clean > shdeg1 ≈ quant8 > quant6 > quant4 ≳ prune50`（**这只是一次 sanity**，
真实结论以 §8 的覆盖率为准，quant4 未必比 prune50 差）。

写盘行应为 `wrote .../dump/<scene>.npz 3x.xMB ... shapes m=~20 H=259 W=389 V=7`。
`m` 必须等于 §3.1 的 `n_views`。

跑完先自检一致性（一次 exec）：

```bash
/root/miniconda3/envs/myconda/bin/python - <<'PY'
import glob, json, os, numpy as np
tot=0
for f in sorted(glob.glob("/workspace/res/dump/*.npz")):
    with np.load(f, allow_pickle=False) as z:
        m=json.loads(str(z["meta"])); V=z["resid"].shape
        tot+=os.path.getsize(f)
        print(f"{os.path.basename(f):14s} resid{V} views={len(z['views'])} "
              f"variants={[str(v) for v in z['variant_names']]}")
print(f"total {tot/2**20:.0f} MiB")
PY
```

判据：4 个文件、每个 `V=7`、`variant_names` 顺序为
`['clean','prune50','prune30','shdeg1','quant8','quant4','quant6']`、`views` 长度一致，
total 约 **150–165 MiB**（4 场景 × ~40 MB）。

排查：
* 少一个场景 → 该场景在 §3.3 就有问题，单独重跑 `--scenes <scene>`。
* `V=6` → `--variants` 丢了 `quant4/quant6`（多半是误传了 `--profile`）。
* 某变体 `n_primitives` 与 clean 相同但 PSNR 也相同 → 该变体没生效（`shdeg2` 在 2 阶 SH 上就是这种情况，见 §3.2）。
* 中途 `Killed` = 系统 OOM（RAM，不是显存）：`quant*` 会 clone 一份资产，加 `--prim-sample 100000` 减小常驻并不解决，
  真正要做的是单场景跑（`--scenes flowers`，逐个来）。

---

## 5. 打包

```bash
cd /workspace/res
tar -czf extend_dump.tgz dump
ls -l extend_dump.tgz
sha256sum extend_dump.tgz
stat -c %s extend_dump.tgz
base64 -w0 extend_dump.tgz > /tmp/x.b64 && wc -c < /tmp/x.b64
```

预期（downsample=1，7 变体）：`~150 MB` tgz，`stat` 字节数 ≈ 1.5e8，`b64` 字符数 ≈ **2.0e8**（= 4/3 × 字节）。
记下 `stat` 的字节数和 sha256，§6 要用它校验。

---

## 6. 传回本地（**先看体积算术，再选方案**）

`matcli node` **没有** upload/download 子命令，只有 `exec`；`fetch_results9.ps1` 的模式是「每次 exec 吐一块 base64」。
按实测（本机 `--dry-run` 7 变体、18 视图、259×389）：

| 方案 | 体积 | base64 字符 | 16000/块 | 约合次数 | 按 1.5 s/次估 |
|---|---|---|---|---|---|
| `downsample=1`（本次默认） | ~155 MB | 2.07e8 | 12,900 块 | ≈ 5.4 小时 |
| `--downsample 2`（compact） | ~43 MB | 5.7e7 | 3,550 块 | ≈ 1.5 小时 |
| **方案 B：节点上跑 `extend_eval.py`，只传 json+md** | < 100 KB | 1.3e5 | 9 块 | **< 1 分钟** |

> 如果 Lead 手上的 MCP 工具里有「文件下载 / 上传」能力，优先用它传 tgz；下面两段是纯 `matcli` 路线。

### 方案 A（按任务书：把 npz 传回本地）

改进点：**先在节点上把 base64 切成固定大小的块**（`split`），再逐块 `cat`。
`fetch_results9.ps1` 每块都重跑 `base64 -w0` 整个文件，是 O(n²)，大文件会慢到不可用。

```powershell
$ErrorActionPreference = "Stop"
$env:PATH = "$env:APPDATA\npm;$env:PATH"
$node   = '2138004'
$remote = '/workspace/res/extend_dump.tgz'
$b64loc = 'D:\3dsg_1\_tmp_extend_dump.b64'
$tgzloc = 'D:\3dsg_1\experiments\artifacts\extend_dump.tgz'
$chunk  = 16000

function RExec([string]$cmd) {
  (matcli node exec --node-id $node --idle-timeout 180 --command $cmd 2>&1 | Out-String)
}

# 一次切块（节点侧 O(n)），拿块数
$out = RExec "cd /workspace/res && base64 -w0 extend_dump.tgz > /tmp/x.b64 && split -b $chunk -d -a 5 /tmp/x.b64 /tmp/x.part. && ls /tmp/x.part.* | wc -l && stat -c %s extend_dump.tgz"
$ms = [regex]::Matches($out, '(?m)^\s*(\d+)\s*$')
if ($ms.Count -lt 2) { Write-Host "PARSE_FAILED -- raw output:"; Write-Host $out; exit 1 }
$parts = [int]$ms[0].Groups[1].Value
$bytes = [long]$ms[$ms.Count - 1].Groups[1].Value
Write-Host "parts=$parts  node bytes=$bytes"
Remove-Item $b64loc -ErrorAction SilentlyContinue

for ($i = 0; $i -lt $parts; $i++) {
  $name = "/tmp/x.part.{0:D5}" -f $i
  $raw  = RExec "echo CHUNK_START; cat $name; echo; echo CHUNK_END"
  $a = $raw.IndexOf('CHUNK_START'); $b = $raw.LastIndexOf('CHUNK_END')
  if ($a -lt 0 -or $b -lt 0) { Write-Host "chunk $i FAILED, retrying once"; $raw = RExec "echo CHUNK_START; cat $name; echo; echo CHUNK_END"; $a = $raw.IndexOf('CHUNK_START'); $b = $raw.LastIndexOf('CHUNK_END') }
  $body = $raw.Substring($a + 11, $b - ($a + 11)).Trim()
  Add-Content -Path $b64loc -Value $body -NoNewline
  if ($i % 100 -eq 0) { Write-Host ("chunk {0}/{1}" -f $i, $parts) }
}

$b64 = (Get-Content $b64loc -Raw).Trim()
$bin = [Convert]::FromBase64String($b64)
New-Item -ItemType Directory -Force -Path (Split-Path $tgzloc) | Out-Null
[IO.File]::WriteAllBytes($tgzloc, $bin)
Write-Host ("local bytes={0}  (node {1})  {2}" -f $bin.Length, $bytes,
  $(if ($bin.Length -eq $bytes) { "SIZE OK" } else { "** SIZE MISMATCH - refetch **" }))
```

校验（两边都跑，必须一致）：

```powershell
Get-FileHash D:\3dsg_1\experiments\artifacts\extend_dump.tgz -Algorithm SHA256 | Select-Object -ExpandProperty Hash
```

```bash
sha256sum /workspace/res/extend_dump.tgz
```

排查：`parts` 提取失败 = 节点侧 `split` 没装（`coreutils` 自带，正常都有）或 `/tmp` 满；
某块 `FAILED` → 该块重试；`SIZE MISMATCH` → 别用，重跑整个循环（base64 拼接错一个字符就全废）。

### 方案 B（带宽最省，**推荐**：数字与方案 A 完全相同）

`extend_eval.py` 是纯 CPU numpy，节点上直接跑，只把 `json` + `md` 传回（几十 KB）。
注意它要跑 **7–9 分钟**（> 默认 idle 超时），所以要么 `--idle-timeout 900`，要么 `nohup ... &` 后轮询日志：

```bash
cd /workspace/code
nohup /root/miniconda3/envs/myconda/bin/python experiments/extend_eval.py \
  --npz /workspace/res/dump --out /workspace/res/extend_eval.json \
  > /workspace/res/extend_eval.log 2>&1 &
# 之后每 1–2 分钟看一次： tail -3 /workspace/res/extend_eval.log
cd /workspace/res && tar -czf extend_tables.tgz extend_eval.json extend_eval.md extend_eval.log dump/dump_summary.json
ls -l extend_tables.tgz
```

预期：终端打印 4 个场景的 `pixel done / block64 done`，然后 `WROTE .../extend_eval.json` + `.../extend_eval.md`，
最后每个变体一行 `median over scenes: pixel drop ...pp qg ...%  block64 drop ...`。
整个 tarball **< 100 KB** → 用 §6 方案 A 的脚本把 `$remote` 换成 `/workspace/res/extend_tables.tgz` 即可，9 块、< 1 分钟。
传回后本机 `tar -xzf` 展开，再按 §8 复核（可以只重画 markdown，不必重算）。

> 两个方案可以都做：先跑 B 拿结果，A 在后台慢慢拉 npz 存档（A 完成后本机可以独立复算、对照 `region_coverage.py`）。

---

## 7. 核对（可选但便宜）：npz 与 paper 口径是否同源

跑一次既有的 `region_coverage.py`，确认 pixel/block 降幅与 `extend_eval.json` 完全一致（两脚本共用
`common.py` 的同一套协议）。如果走方案 A（`extend_eval` 在本地跑），把两个 json 都放到同一侧再比；
下面按"两者都在节点上"写（= 方案 B 之后）：

```bash
/root/miniconda3/envs/myconda/bin/python experiments/region_coverage.py \
  --npz /workspace/res/dump --out /workspace/res/region_coverage.json \
  --granularities pixel,block --blocks 64 --mode none
/root/miniconda3/envs/myconda/bin/python - <<'PY'
import json
ee=json.load(open("/workspace/res/extend_eval.json"))
rc=json.load(open("/workspace/res/region_coverage.json"))
a={(r["scene"],r["variant"],r["granularity"]):r for r in ee["rows"]}
b={(r["scene"],r["variant"],r["granularity"]):r for r in rc["rows"]}
worst=max(abs(a[k]["drop_mean"]-b[k]["drop_mean"]) for k in a if k in b and a[k]["drop_mean"] is not None)
print(f"{len(a)} extend rows, {len(b)} region rows, max |drop diff| = {worst:.2e}")
PY
```

预期：`max |drop diff| <= 1e-9`（两脚本共用 `common.py` 的同一套协议；本机已断言 0.00e+00）。

---

## 8. 本地复算（本机，纯 CPU，无 GPU）

```powershell
cd D:\3dsg_1
New-Item -ItemType Directory -Force -Path experiments\artifacts | Out-Null
tar -xzf experiments\artifacts\extend_dump.tgz -C experiments\artifacts   # 方案 A
python experiments\extend_eval.py --npz experiments\artifacts\dump `
  --out experiments\artifacts\extend_eval.json --blocks 64
```

预期产物：

```
experiments\artifacts\dump\{flowers,bicycle,treehill,stump}.npz
experiments\artifacts\extend_eval.json     # 每 (scene, variant, granularity) 一行 + 跨场景汇总 + 剂量曲线
experiments\artifacts\extend_eval.md       # 附录表 E1–E6（可直接贴）
```

耗时：本机实测 **~103 s/场景**（400 splits × 7 变体 × pixel+block，18 视图、259×389），
4 场景约 **7–9 分钟**（真实场景视图更多，可能到 10 分钟）；`--downsample 2` 的产物约 2–3 分钟。
日志应打印
`extend_eval: 4 npz, variants=all non-clean, granularities=pixel,block blocks=64, splits=400 alpha=0.1`。

自检：

```powershell
python -c "import json; d=json.load(open(r'experiments\artifacts\extend_eval.json')); print(len(d['rows']),'rows'); print(d['meta']['granularities']); [print(v, {g:(round(x['drop_pp']['median'],1) if x['drop_pp']['median'] is not None else None) for g,x in p.items()}) for v,p in d['summary_by_variant'].items()]"
```

判据：`4 scenes × 7 variants × 2 granularities = 56` 行；`granularities == ['pixel','block64']`。
`clean` 的 drop 必须恰好 0.0；每个变体的 `drop_pp.median` 为负 = 覆盖下降（正 = 反而变好，要在报告里点名）。

排查：
* `no npz artifacts under ...` → tgz 解到别的层级了（`tar -tzf` 看成员名是不是 `dump/xxx.npz`）。
* `too few` / `m < 4` → 误把 §3.3 的 smoke 产物或 `--max-views 2` 的产物丢进来了。
* `missing variants [...]` → 该 npz 是旧的 6 变体产物（缺 `quant4/quant6`），或者你 `--variants` 过滤里
  写了产物里根本没有的变体名。先看 `python -c` 打印的 `variant_names` 再决定。

---

## 9. 估算（显存 / 时间 / 磁盘）

| 项 | 估算 | 依据 |
|---|---|---|
| 显存峰值（`dump_artifacts.py`） | **4–10 GB**（A40 49 GB 余量极大） | 资产 2–6 M prim × 236 B ≈ 0.5–1.4 GB；`quant*` 会再 clone 一份（峰值 2×），gsplat 瓦片缓冲在 259×389 上可忽略 |
| 正式 dump 时间 | **6–12 分钟**（4 场景 × 7 变体 × ~20 视图 ≈ 560 次渲染） | 渲染 0.05–0.2 s/视图；主成本是 4 次 PLY 读入（每场景 1–1.5 GB）+ 4 次 `savez_compressed` |
| 自检（§3.3） | < 1 分钟 | 2 变体 × 2 视图 × 4 场景 |
| 解包 | 2–5 分钟 | 9.59 GB gz（PLY 几乎不可压）→ 约 **10–12 GB** 落盘 |
| 磁盘占用 | 归档 9.6 GB + 解包 ~11 GB + dump ~0.16 GB + tgz ~0.15 GB ≈ **21 GB** | `/` 空闲 344 GB，充裕 |
| 传回（方案 A / downsample 1） | **≈ 5.4 小时**（12,900 块 × 1.5 s） | 见 §6 实测表 |
| 传回（方案 B） | **< 1 分钟** | json+md < 100 KB |
| 本地 `extend_eval` | **7–9 分钟**（4 场景，400 splits） | 本机实测 103 s/场景（18 视图、7 变体、259×389，两个场景 90.7 s + 115.9 s） |

想缩体积：`--downsample 2` 把 npz 从 ~40 MB/scene 降到 ~11 MB/scene（4 场景 43 MB），
代价是 pixel 单位变成 factor 8、`block64` 在 capture 空间变成 512 px——**必须在表头注明**，
且不要和论文里 factor-4 的 pixel 数字直接并列。协议常量（400 splits / α=0.10）不受影响。

---

## 10. 最容易踩的 3 个坑

1. **`--profile` 会静默吃掉 `--variants`。**
   `apply_profile()` 里只有 `profile == "full"` 才保留命令行给的变体；`core`/`compact` 会直接覆盖成预设的
   4/6 个变体。结果就是 dump 里**没有 `quant4`/`quant6`**，而日志前面照常"成功"。自检：日志第一行必须是
   `profile=full variants=clean,prune50,prune30,shdeg1,quant8,quant4,quant6`，且 §4 自检里 `V=7`。

2. **`matcli node exec` 是独立 shell + 有 idle 超时。**
   `export PY=...` 在下一个 exec 里就没了；解包（2–5 分钟）、`pip install`、`tar -czf` 这类命令如果不
   `--idle-timeout 300` 或 `nohup ... &`，会被截断成一个半成品文件，而下一步会"看起来成功"地读它。
   判据：永远用 `stat -c %s` / `ls -l` 核对产物大小，别只信命令结束。

3. **传回体积被严重低估（默认 profile 下 ~155 MB ≈ 5 小时）。**
   7 变体 @ downsample 1 是 6 变体的 ~1.17 倍，而 base64 分块传是**每 16 KB 一次 exec**。
   别用 `fetch_results9.ps1` 原样写法（它每块重跑 `base64 -w0`，O(n²)）；要么按 §6 的 `split` 版、
   要么直接上**方案 B**（节点上跑 `extend_eval.py`，只传 json+md）。先算再传。

### 其他值得注意的（不等于不坑）

4. `--budget-mb` 默认 30 → 7 变体必然刷 `[warn] ... > budget`；这是**正常**的，用 `--budget-mb 45` 消掉噪音。
5. `test/ours_40000/gt` 的文件数必须等于 `i%8==0` 的相机数；不等时加载器只打 warning 并取 `min`，视图数就悄悄变了。
6. 某场景 SH 只有 2 阶时 `shdeg2` 是 no-op（§3.2 已检查）。`dump_artifacts.py` 现在会**直接报错退出**
   （`the checkpoint already has SH degree 2 ...`）而不是写出一行和 `clean` 一模一样的假剂量点；
   遇到就把 `shdeg2` 从这个 `--variants` 里去掉，并在报告里注明。
7. `quant*` 会 clone 一份资产；A40 49 GB 不会显存 OOM，但如果 `Killed` 那是**内存**，改成单场景逐个跑。
8. 本机 Python 是 3.14，节点是 3.11——只用 numpy/stdlib 的部分两边都通过了；**不要**在节点上 `pip install -U numpy`。

---

## 11. 一页速查（命令顺序）

```bash
# 节点侧（每段一条 exec；耗时长的加 --idle-timeout 300）
ls -l /data/output-3dgs.tar.gz && tar -tzf /data/output-3dgs.tar.gz | head -3        # §2.1
mkdir -p /workspace/data && tar -xzf /data/output-3dgs.tar.gz -C /workspace/data      # §2.2
PY ... §2.3 的布局检查                                                                # 全 OK 才继续
PY ... §3.1 视图检查 ;  PY ... §3.2 SH 检查                                           # §3.1-3.2
PY experiments/dump_artifacts.py ... --variants clean,quant4 --max-views 2 ...         # §3.3 冒烟
PY experiments/dump_artifacts.py --archive /workspace/data \
   --variants clean,prune50,prune30,shdeg1,quant8,quant4,quant6 \
   --scenes flowers,bicycle,treehill,stump --out /workspace/res/dump \
   --device cuda --budget-mb 45 2>&1 | tee /workspace/res/dump.log                     # §4 正式
PY ... §4 的 npz 一致性检查                                                            # V=7 x4
cd /workspace/res && tar -czf extend_dump.tgz dump && sha256sum extend_dump.tgz        # §5
```

```powershell
# 本机侧
pwsh -File tools\push_to_node.ps1 ...      # §1（两批，RemoteRoot 不同）
# §6 方案 A 的 PowerShell 脚本（或方案 B：只拉 extend_tables.tgz）
tar -xzf experiments\artifacts\extend_dump.tgz -C experiments\artifacts                # §8
python experiments\extend_eval.py --npz experiments\artifacts\dump `
  --out experiments\artifacts\extend_eval.json --blocks 64                              # §8
```
