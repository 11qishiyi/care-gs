import subprocess
import sys

for mod in ("calib.llff", "calib.colmap_io", "calib.gsrender", "gsplat"):
    try:
        __import__(mod)
        print("ok", mod)
    except Exception as e:  # noqa: BLE001
        print("FAIL", mod, type(e).__name__, e)
