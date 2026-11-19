There are no index cache(s) to remove.
[0;32m机器区域: [0m1区
+------------------------------------------------------------+
| 快捷命令:                                                  |
| - 后台运行Python代码（关电脑、断线都不会中断），输入：[0;32mm[0m    |
| - 定时释放机器，输入：[0;32mtsd[0m                                  |
| - 访问网盘目录：输入：[0;32mcd /mnt[0m                              |
| - 更改apt源，输入：[0;32mapt_source[0m                              |
| - 更改pip源，输入：[0;32mpip_source[0m                              |
| - 更改conda源，输入：[0;32mconda_source[0m                          |
| - huggingface加速下载，输入: [0;32mhfd_source[0m                    |
| - 如有疑问或者其它需求,请查看:	                     |
| - [0;32mhttps://www.matpool.com/supports/contact/methods/[0m	     |
+------------------------------------------------------------+
There are no index cache(s) to remove.
[0;32m机器区域: [0m1区
+------------------------------------------------------------+
| 快捷命令:                                                  |
| - 后台运行Python代码（关电脑、断线都不会中断），输入：[0;32mm[0m    |
| - 定时释放机器，输入：[0;32mtsd[0m                                  |
| - 访问网盘目录：输入：[0;32mcd /mnt[0m                              |
| - 更改apt源，输入：[0;32mapt_source[0m                              |
| - 更改pip源，输入：[0;32mpip_source[0m                              |
| - 更改conda源，输入：[0;32mconda_source[0m                          |
| - huggingface加速下载，输入: [0;32mhfd_source[0m                    |
| - 如有疑问或者其它需求,请查看:	                     |
| - [0;32mhttps://www.matpool.com/supports/contact/methods/[0m	     |
+------------------------------------------------------------+
# M11: per-primitive mode selection

source: `/workspace/res/m11/m11_rd.json`

**outcome** `dead_write_N20`

| criterion | verdict | detail |
|---|---|---|
| P1_near_lossless_12x | FAIL | 5/8 assets (need 6) |
| P2_beats_families_at_matched_bytes | FAIL | 4/8 assets (need 6), median +0.56 pp |
| P3_floor_at_18_20x | n/a | grid misses P3_floor_at_18_20x (covered 5/6) |

## P1 members at >= 12x

| asset | variant | rate | drop pp | dPSNR |
|---|---|---|---|---|
| bicycle_i7k | `msc12-4-a4_c8_o8` | 14.34x | -0.35 | +0.102 |
| flowers | `msc12-3-a4_c8_o8` | 15.71x | -0.78 | +0.066 |
| flowers_i7k | `msc12-4-a4_c8_o8` | 13.13x | -0.15 | +0.006 |
| stump | `msc12-3-a1_c8_o8` | 12.24x | -0.65 | +0.110 |
| stump_i7k | `msc12-4-a4_c8_o8` | 14.27x | -0.26 | +0.091 |

## P2 matched-byte comparison

| asset | msc | rate | drop | rival | rate | drop | diff |
|---|---|---|---|---|---|---|---|
| bicycle | `msc12-2-a1_c8_o8` | 19.84x | -1.85 | `vq12_c8_o8` | 20.02x | -1.89 | +0.04 |
| bicycle_i7k | `msc12-4-a4_c8_o8` | 14.34x | -0.35 | `c8_o8_sh2` | 14.32x | -1.46 | +1.11 |
| flowers | `msc12-2-a1_c8_o8` | 19.61x | -1.39 | `vq12_c8_o8` | 19.70x | -1.41 | +0.01 |
| flowers_i7k | `msc12-4-a4_c8_o8` | 13.13x | -0.15 | `c8_o8_sh2` | 13.80x | -0.71 | +0.56 |
| stump | `msc12-4-a4_c8_o8` | 8.91x | -0.21 | `c8_o8_sh3` | 9.62x | -0.53 | +0.31 |
| stump_i7k | `msc12-4-a4_c8_o8` | 14.27x | -0.26 | `c8_o8_sh2` | 14.21x | -4.31 | +4.05 |
| treehill | `msc12-4-a4_c8_o8` | 8.72x | -0.08 | `c8_o8_sh3` | 9.43x | -0.16 | +0.09 |
| treehill_i7k | `msc12-4-a4_c8_o8` | 15.39x | +0.09 | `c8_o8_sh2` | 14.19x | -0.93 | +1.02 |

