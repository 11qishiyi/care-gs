"""Fetch the M37 artifacts from the node (render.txt, timings, both training logs)."""
import os
import subprocess
import sys

MATCLI = os.path.join(os.environ["APPDATA"], "npm", "matcli.cmd")
NODE = sys.argv[1] if len(sys.argv) > 1 else "2141303"
REMOTE = "/workspace/res/m37"
LOCAL = os.path.join("experiments", "artifacts", "a4", "m37")

os.makedirs(LOCAL, exist_ok=True)
for name in ("render.txt", "m37_time.txt", "train_a.log", "train_b.log", "m37.log",
             "encode_a.log", "encode_b.log"):
    dst = os.path.join(LOCAL, name)
    r = subprocess.run([MATCLI, "node", "exec", "--node-id", NODE, "--idle-timeout", "120",
                        "--command", f"cat {REMOTE}/{name}"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if not r.stdout.strip():
        print(f"skip {name}")
        continue
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(r.stdout)
    print(f"{name}: {os.path.getsize(dst)} B")
