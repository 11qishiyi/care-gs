import sys
sys.path.insert(0, "/workspace/code/research/code")
import numpy as np
from calib.plyio import load_inria_ply

a = load_inria_ply("/workspace/data/models/output/bicycle/point_cloud/iteration_30000/point_cloud.ply")
b = load_inria_ply("/workspace/res/m53g3/k3_o4_vq64/recon.ply")
print("n", len(a["means"]), len(b["means"]))
la, lb = np.log(a["scales"]), np.log(np.clip(b["scales"], 1e-12, None))
d = np.abs(lb - la)
print("scale log diff: mean %.3f p99 %.3f max %.3f" % (d.mean(), np.percentile(d, 99), d.max()))
oa = np.log(np.clip(a["opacities"], 1e-6, 1 - 1e-6) / (1 - np.clip(a["opacities"], 1e-6, 1 - 1e-6)))
ob = np.log(np.clip(b["opacities"], 1e-6, 1 - 1e-6) / (1 - np.clip(b["opacities"], 1e-6, 1 - 1e-6)))
print("opacity logit diff: mean %.3f p99 %.3f max %.3f" % (np.abs(ob - oa).mean(), np.percentile(np.abs(ob - oa), 99), np.abs(ob - oa).max()))
print("quat diff: mean %.4f max %.4f" % (np.abs(a["quats"] - b["quats"]).mean(), np.abs(a["quats"] - b["quats"]).max()))
print("means diff: mean %.4f max %.4f" % (np.abs(a["means"] - b["means"]).mean(), np.abs(a["means"] - b["means"]).max()))
print("sh0 diff: mean %.5f max %.5f" % (np.abs(a["sh0"] - b["sh0"]).mean(), np.abs(a["sh0"] - b["sh0"]).max()))
print("shN diff: mean %.5f max %.5f" % (np.abs(a["shN"] - b["shN"]).mean(), np.abs(a["shN"] - b["shN"]).max()))
