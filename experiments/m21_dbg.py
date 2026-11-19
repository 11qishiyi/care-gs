import os
import sys

import numpy as np

sys.path.insert(0, "/workspace/code/experiments")
import m19_codec as C  # noqa: E402

p = sys.argv[1]
meta, streams = C.read_container(p, tolerant=True)
print("damaged", meta["damaged_bytes"])
for e in meta["streams"]:
    if e["name"].startswith("sh_"):
        print(f"  {e['name']:12s} comp {e['comp']:>10,}  bad {e.get('bad_frames')}/{e.get('frame_count')}"
              f"  lost {e.get('lost_ranges')}")
out = C.decode(meta, streams)
for k in ("sh_dc", "sh_rest"):
    a = out[k]
    print(f"{k}: shape {a.shape} absmax {np.abs(a).max():.4f} mean {a.mean():.4f} "
          f"frac_zero {float((a == 0).mean()):.4f}")
print("means absmax", np.abs(out["means"]).max(), "opacity mean", out["opacities"].mean())
