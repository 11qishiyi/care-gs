import sys
import numpy as np
sys.path.insert(0, "/workspace/code/research/code")
from calib.plyio import load_inria_ply

for tag, p in (("ours", "/workspace/data/strat/abs/point_cloud.ply"),
               ("mirror", "/workspace/data/models_official/output/bicycle/point_cloud/iteration_30000/point_cloud.ply")):
    d = load_inria_ply(p)
    s = d["scales"].astype(np.float64)
    o = d["opacities"].astype(np.float64)
    m = d["means"].astype(np.float64)
    ext = float(np.percentile(np.linalg.norm(m - m.mean(0), axis=1), 99))
    print(f"{tag:7s} n={len(s):8d} extent={ext:7.2f} scale med={np.median(s):.4f} "
          f"p90={np.percentile(s,90):.4f} p99={np.percentile(s,99):.3f} "
          f"rel_med={np.median(s)/ext:.5f} | opac med={np.median(o):.3f} mean={o.mean():.3f}")