"""Fetch the M38 artifacts (per-k reports) into experiments/artifacts/a4/m38."""
import os
import subprocess

MATCLI = os.path.join(os.environ["APPDATA"], "npm", "matcli.cmd")
NODE = "2141436"
LOCAL = os.path.join("experiments", "artifacts", "a4", "m38")
os.makedirs(LOCAL, exist_ok=True)
for name in ("render.txt", "m38_time.txt", "k4096.json", "k16384.json", "k65536.json", "m38.log"):
    r = subprocess.run([MATCLI, "node", "exec", "--node-id", NODE, "--idle-timeout", "120",
                        "--command", f"cat /workspace/res/m38/{name}"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if not r.stdout.strip():
        print(f"skip {name}")
        continue
    with open(os.path.join(LOCAL, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(r.stdout)
    print(f"{name}: {os.path.getsize(os.path.join(LOCAL, name))} B")
