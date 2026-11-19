import glob
import json
import os

import frontier as F

paths = []
base = os.path.join("experiments", "artifacts", "a4")
for tag in F.SOURCES:
    paths += sorted(glob.glob(os.path.join(base, f"{tag}.json")))
rows = F.load_rows(paths)
for name in ("p30", "p50", "p90", "sh16_g16", "sh12_g16", "sh8_g16", "sh6_g16"):
    vals = [(s, r) for s, rs in rows.items() for r in rs if r["variant"] == name]
    if not vals:
        continue
    rates = [r["rate"] for _, r in vals]
    drops = [r["drop_pp"] for _, r in vals]
    srcs = sorted({r["from"] for _, r in vals})
    print(f"{name:10s} n={len(vals):3d} rate {min(rates):5.2f}-{max(rates):5.2f}x "
          f"drop {min(drops):+7.2f}..{max(drops):+7.2f} from {srcs}")
