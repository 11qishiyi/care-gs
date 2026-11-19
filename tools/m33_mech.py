"""Dump the mechanical part of each M33 damage json (what actually changed in the decoded model)."""
import glob
import json
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "/workspace/res/m33"
for scene in ("bicycle", "stump", "bonsai"):
    print(f"== {scene}")
    for f in sorted(glob.glob(os.path.join(root, scene, "dmg", "damage_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        c = d.get("changed", {})
        name = d.get("condition", os.path.basename(f))
        lost = c.get("lost_bytes", 0) / 1e6
        parts = [f"{name:14s} lost {lost:6.2f} MB"]
        for k in ("means_changed_frac", "sh_dc_changed_frac", "sh_rest_changed_frac"):
            if k in c:
                parts.append(f"{k.split('_changed')[0]} {c[k]*100:6.2f}%")
        print("  " + "  ".join(parts))
