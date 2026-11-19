"""M32 -- collect container sizes and rendered PSNR for every plan/scene into one json.

Runs on the node (reads /workspace/res/m32).  The render log lines look like

    m32_bonsai_gp6_6_6_c8_sh3_r16_b048_auto clean  n=1,244,819 ... PSNR= 27.08 ...

so the plan is recovered from the archive name, which is why the render stage names them
``m32_<scene>_<tag>``.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re

PLAN_RE = re.compile(r"_r(\d{2})_b(\d{3})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="/workspace/res/m32")
    ap.add_argument("--scenes", default="bicycle,stump,bonsai")
    ap.add_argument("--json", default="/workspace/res/m32/m32_sizes.json")
    a = ap.parse_args()

    out = {}
    for scene in a.scenes.split(","):
        entry = {"containers": {}, "psnr": {}, "encode_s": None}
        for p in sorted(glob.glob(os.path.join(a.root, scene, "*_auto.gs1"))):
            tag = os.path.basename(p)[:-len(".gs1")]
            m = PLAN_RE.search(tag)
            key = f"r{int(m.group(1))}_b{int(m.group(2))}" if m else tag
            entry["containers"][key] = os.path.getsize(p)
        log = os.path.join(a.root, f"render_{scene}.log")
        if os.path.exists(log):
            for line in open(log, encoding="utf-8", errors="replace"):
                m = re.search(r"m32_%s_(\S+?)_auto\s+clean.*?PSNR=\s*([\d.]+)" % scene, line)
                if not m:
                    continue
                pm = PLAN_RE.search(m.group(1))
                key = f"r{int(pm.group(1))}_b{int(pm.group(2))}" if pm else m.group(1)
                entry["psnr"][key] = float(m.group(2))
        enc = os.path.join(a.root, f"enc_{scene}.txt")
        if os.path.exists(enc):
            m = re.search(r"encode_wall ([\d.]+)", open(enc, encoding="utf-8").read())
            entry["encode_s"] = float(m.group(1)) if m else None
        out[scene] = entry

    json.dump(out, open(a.json, "w", encoding="utf-8"), indent=1)
    for scene, e in out.items():
        print(f"{scene}: {len(e['containers'])} container(s), {len(e['psnr'])} render(s), "
              f"encode {e['encode_s']} s")
        for k in sorted(e["containers"]):
            print(f"   {k:10s} {e['containers'][k]/1e6:7.2f} MB   PSNR {e['psnr'].get(k, '--')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
