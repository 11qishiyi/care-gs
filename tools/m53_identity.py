import sys
sys.path.insert(0, "/workspace/code/research/code")
import numpy as np
from calib.plyio import load_inria_ply, save_inria_ply

SRC = "/workspace/data/models/output/bicycle/point_cloud/iteration_30000/point_cloud.ply"
d = load_inria_ply(SRC)
print("n", len(d["means"]), "sh0", d["sh0"].shape, "shN", d["shN"].shape)
save_inria_ply("/tmp/identity.ply", d["means"], d["scales"], d["quats"], d["opacities"], d["sh0"], d["shN"])
e = load_inria_ply("/tmp/identity.ply")
print("max abs diff means", float(np.abs(e["means"] - d["means"]).max()))
print("max abs diff shN", float(np.abs(e["shN"] - d["shN"]).max()))
print("max abs diff quats", float(np.abs(e["quats"] - d["quats"]).max()))
print("max abs diff opacities", float(np.abs(e["opacities"] - d["opacities"]).max()))
