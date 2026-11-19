import sys, glob
import numpy as np
for f in sorted(glob.glob("/workspace/res/smb_rates/bicycle/probe/*.npz"))[:2]:
    d = np.load(f, allow_pickle=True)
    print(f, list(d.keys())[:12])
    for k in d.keys():
        if "lpips" in k.lower() or "ssim" in k.lower():
            v = d[k]
            print(" ", k, getattr(v, "shape", None), float(np.mean(v)) if v.size else None)
