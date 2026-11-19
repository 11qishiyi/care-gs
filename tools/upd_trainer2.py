import io
p = r"D:\3dsg_1\research\TRAINER_INVESTIGATION.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""4. **不是场景尺度归一化缺失**——`scene_scale = max(相机散布, 点云半径)`，
   致密化阈值与 means LR 都按它归一化。""",
"""4. **不是场景尺度归一化缺失**——`scene_scale = max(相机散布, 点云半径)`，
   致密化阈值与 means LR 都按它归一化；
5. **不是学习率过高**——`--lr_scale 0.3` 重跑 garden 14k 步：train 16.02 / cal 8.80 / dep 8.19，
   **比默认更差**（默认 cal 11.26）。降 LR 只是让两边一起变差，不改变差距方向。
6. **不是评估口径/图像配对**——训练 PSNR（内存态）与留出 PSNR 走同一条 `load_images` 路径；
   若 GT 配对错，训练 PSNR 也不会到 16–22 dB。""")
s = s.replace("""**尚未排除的候选**（按怀疑度排序）：
1. **`grow_grad2d` 阈值偏低**""",
"""**尚未排除的候选**（按怀疑度排序）：
1. **`grow_grad2d` 阈值偏低**（`--lr_scale` 已排除，见上）""")
io.open(p, "w", encoding="utf-8").write(s)
print("trainer doc updated: lr_scale and pairing ruled out")
