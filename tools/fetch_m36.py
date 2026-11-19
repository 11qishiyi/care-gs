"""Fetch the M36 artifacts from the node into experiments/artifacts/a4/m36.

Train logs are ~1-2 MB each; the useful part is the eval/rate lines, so they are fetched in full (they are
small enough) and the round's table is regenerated locally from render.txt.
"""
import os
import subprocess
import sys

MATCLI = os.path.join(os.environ["APPDATA"], "npm", "matcli.cmd")
NODE = sys.argv[1] if len(sys.argv) > 1 else "2141303"
REMOTE = "/workspace/res/m36"
LOCAL = os.path.join("experiments", "artifacts", "a4", "m36")
FILES = ["render.txt", "m36_time.txt", "train_a.log", "train_b.log", "train_c.log", "train_d.log",
         "m36.log"]

os.makedirs(LOCAL, exist_ok=True)
for name in FILES:
    dst = os.path.join(LOCAL, name)
    r = subprocess.run([MATCLI, "node", "exec", "--node-id", NODE, "--idle-timeout", "120",
                        "--command", f"cat {REMOTE}/{name}"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", shell=False)
    body = r.stdout
    if not body.strip():
        print(f"skip {name}: empty (exit {r.returncode})")
        continue
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print(f"{name}: {os.path.getsize(dst)} B")
