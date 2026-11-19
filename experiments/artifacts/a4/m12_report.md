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
# M12: product quantisation of the SH block

source: `/workspace/res/m12/m12_rd.json`

**outcome** `dead_write_N21`

| criterion | verdict | detail |
|---|---|---|
| Q1_pq_beats_vq_at_matched_bytes | FAIL | 1/8 assets (need 6), median +0.01 pp |
| Q2_shelf_at_16x | FAIL | 2/8 covered (need 6) |

## Q1 matched-byte comparison

| asset | pq | rate | drop | vq | rate | drop | diff |
|---|---|---|---|---|---|---|---|
| bicycle | `pq4-8_c8_o8` | 17.15x | -1.67 | `vq16_c8_o8` | 17.24x | -1.15 | -0.52 |
| bicycle_i7k | `pq4-4_c8_o8` | 20.42x | -0.97 | `vq12_c8_o8` | 20.38x | -0.70 | -0.28 |
| flowers | `pq4-8_c8_o8` | 16.76x | -0.92 | `vq16_c8_o8` | 16.74x | -0.94 | +0.01 |
| flowers_i7k | `pq6-4_c8_o8` | 18.92x | -0.32 | `vq14_c8_o8` | 17.87x | -0.38 | +0.06 |
| stump | `pq4-8_c8_o8` | 17.13x | -2.23 | `vq16_c8_o8` | 17.07x | -1.77 | -0.46 |
| stump_i7k | `pq4-8_c8_o8` | 17.20x | -0.99 | `vq16_c8_o8` | 16.80x | -0.54 | -0.45 |
| treehill | `pq8-3_c8_o8` | 18.72x | -0.19 | `vq14_c8_o8` | 18.05x | -0.28 | +0.09 |
| treehill_i7k | `pq8-3_c8_o8` | 19.43x | +0.81 | `vq12_c8_o8` | 20.34x | +0.18 | +0.62 |

## Q2 members at >= 16x

| asset | variant | rate | drop pp | dPSNR |
|---|---|---|---|---|
| bicycle_i7k | `pq4-6_c8_o8` | 18.59x | -0.80 | +0.026 |
| stump_i7k | `pq4-8_c8_o8` | 17.20x | -0.99 | +0.054 |

