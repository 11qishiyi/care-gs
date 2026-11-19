import io
p = r"D:\3dsg_1\APPENDIX_negative_results.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("# 附录：八个被否定的方向及其证据", "# 附录：九个被否定的方向及其证据")
s = s.replace("**检验**：在发布检查点上实现三套估计器（4 场景以外，flowers 单场景 32 个图像块、18,432 像素），\n与真实误差做秩相关。",
              "**检验**：在 flowers 发布检查点上实现三套估计器（32 个图像块、18,432 像素），与真实误差做秩相关。")
s = s.replace("| bonsai | 211k | 0.903 | 0.896 | −0.7 |", "| bonsai | 211k | 0.903 | 0.896 | −0.8 |")
s = s.replace("（−0.7 ~ +3.2pp）", "（−0.8 ~ +3.2pp）")
io.open(p, "w", encoding="utf-8").write(s)
print("appendix: title + numbers fixed")
