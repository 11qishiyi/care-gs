"""M33 -- break the file and measure what it renders.

For one scene's shipping container: an intact control, burst corruption at six fractions, truncation at
four prefixes.  Each condition is decoded with ``tolerant=True`` (CRC-checked frames, neutral fill), the
decoded model is archived and rendered by the same path as every other number in the paper.

    python tools/m33_damage.py --gs1 <file> --out <dir> [--archive <dir>] [--scene-dir <colmap>]
                               [--render] [--only damage|trunc|control]

The PSNR lines are printed by the render stage; the mechanical facts (lost bytes, frames, changed
primitives) come from the decoder and are written to ``<out>/damage_<tag>.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(HERE, "experiments"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import m19_codec as C  # noqa: E402
import numpy as np  # noqa: E402

DAMAGE = (0.001, 0.0025, 0.005, 0.01, 0.02, 0.05)
TRUNC = (0.25, 0.50, 0.75, 0.90)


def _decode_ok(path: str) -> tuple:
    meta, streams = C.read_container(path, tolerant=True)
    n = int(meta["n"])
    return meta, streams, n


def _changed(meta, streams, ref) -> dict:
    """How much of the model actually moved, in the terms M19's damage report used."""
    out = {"lost_bytes": int(meta.get("damaged_bytes", 0))}
    bad = [s["name"] for s in meta["streams"] if s.get("bad_frames")]
    out["streams_with_lost_frames"] = bad
    try:
        dec = C.decode(meta, streams)
    except Exception as exc:                        # a damaged file may fail to decode at all
        out["decode_error"] = f"{type(exc).__name__}: {exc}"
        return out
    for key in ("means", "sh_dc", "sh_rest", "scales", "opacities", "quats"):
        if key in dec and key in ref:
            a = np.asarray(dec[key], dtype=np.float32)
            b = np.asarray(ref[key], dtype=np.float32)
            if a.shape != b.shape:
                out[f"{key}_shape"] = [list(a.shape), list(b.shape)]
                continue
            diff = np.abs(a - b)
            out[f"{key}_changed_frac"] = float((diff.reshape(len(diff), -1).max(axis=1) > 0).mean())
            out[f"{key}_max_abs"] = float(diff.max())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gs1", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--archive", default="/workspace/data/m360std")
    ap.add_argument("--scene-dir", default=None)
    ap.add_argument("--tag", default=None, help="prefix for archive entries")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--only", default="all", choices=("all", "control", "damage", "trunc"))
    ap.add_argument("--burst", default="",
                    help="comma-separated burst fractions (e.g. 0.001,0.01); overrides the six-"
                         "condition schedule and skips truncation (M34 sweeps frames, not schedules)")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    tag = a.tag or os.path.basename(a.gs1).split("_r")[0]
    ref = None
    burst = tuple(float(x) for x in a.burst.split(",") if x.strip()) if a.burst else DAMAGE

    conds = []
    if a.only in ("all", "control"):
        conds.append(("control", 0.0, None))
    if a.only in ("all", "damage"):
        conds += [(f"damage_{int(round(f*10000)):04d}", f, "damage") for f in burst]
    if a.only in ("all", "trunc") and not a.burst:
        conds += [(f"trunc_{int(round(f*100)):02d}", f, "trunc") for f in TRUNC]

    for name, frac, kind in conds:
        dst = os.path.join(a.out, f"{tag}_{name}.gs1")
        if kind is None:                            # the intact control: a byte-for-byte copy
            if not os.path.exists(dst):
                with open(a.gs1, "rb") as src, open(dst, "wb") as out:
                    out.write(src.read())
            info = {"condition": name, "frac": 0.0, "bytes": os.path.getsize(dst)}
        elif kind == "damage":
            info = C.damage_file(a.gs1, dst, float(frac), burst=True)
            info["condition"] = name
        else:
            info = C.truncate_file(a.gs1, dst, float(frac))
            info["condition"] = name

        meta, streams, n = _decode_ok(dst)
        if ref is None:
            ref = C.decode(meta, streams)           # the control defines "changed"
            info["changed"] = {"means_changed_frac": 0.0}
        else:
            info["changed"] = _changed(meta, streams, ref)
        info["n"] = n
        info["bytes"] = os.path.getsize(dst)
        json.dump(info, open(os.path.join(a.out, f"damage_{name}.json"), "w", encoding="utf-8"), indent=1)
        print(f"{name:14s} {info['bytes']/1e6:7.2f} MB  lost {info['changed'].get('lost_bytes', 0)/1e6:6.2f} MB  "
              f"streams {info['changed'].get('streams_with_lost_frames')}", flush=True)

        if not a.render:
            continue
        ply = os.path.join(a.out, f"{tag}_{name}.ply")
        C.to_ply(meta, streams, ply)
        entry = f"m33_{tag}_{name}"
        subprocess.run([sys.executable, "experiments/make_m360_archive.py", "--scene-dir", a.scene_dir,
                        "--ply", ply, "--archive", a.archive, "--name", entry],
                       check=False, cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        r = subprocess.run(["bash", os.path.join(HERE, "experiments", "probe_render.sh"), entry, "1"],
                           capture_output=True, text=True, cwd=HERE)
        line = [l for l in r.stdout.splitlines() if "PSNR" in l]
        print("   ", line[-1].strip() if line else f"render failed: {r.stdout[-200:]}", flush=True)
        os.remove(ply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
