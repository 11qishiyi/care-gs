import sys
sys.path.insert(0, "/workspace/code/research/code")
import numpy as np
from calib.plyio import load_inria_ply

for tag, path in (("orig", "/workspace/data/models/output/bicycle/point_cloud/iteration_30000/point_cloud.ply"),
                  ("recon", "/workspace/res/m53g3/k3_o4_vq64/recon.ply")):
    d = load_inria_ply(path)
    s = np.log(np.clip(d["scales"], 1e-12, None))
    o = np.clip(d["opacities"], 1e-6, 1 - 1e-6)
    print(tag, "n", len(d["means"]),
          "| means p1/p50/p99 %.2f %.2f %.2f" % (np.percentile(d["means"][:, 0], 1), np.median(d["means"][:, 0]), np.percentile(d["means"][:, 0], 99)),
          "| logscale p1/p50/p99 %.2f %.2f %.2f" % (np.percentile(s, 1), np.median(s), np.percentile(s, 99)),
          "| opacity p1/p50/p99 %.3f %.3f %.3f" % (np.percentile(o, 1), np.median(o), np.percentile(o, 99)))
