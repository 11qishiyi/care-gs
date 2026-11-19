"""M37 three-way table and K1–K3 verdict: the rate pressure on the full model.

    python tools/m37_table.py --dir experiments/artifacts/a4/m37

Reads `render.txt` (`<arm> <bytes> <probe_render line>`), `m37_time.txt` (`wall_<arm> <s> s`) and the two
training logs for the calibrated λ and the last calibration eval.  The criteria come from
`tools/m37_spec.md`: K1 (bytes or dB at matched budget), K2 (direction agrees with M36 and SSIM holds),
K3 (wall clock ≤ 1.5×).
"""
from __future__ import annotations

import argparse
import json
import os
import re

LAMBDA = re.compile(r"\[rate\] calibrated lambda=(\S+)")
EVAL = re.compile(r"\[eval\].*?cal=(\d+\.\d+)")
SSIM = re.compile(r"ssim=(\d+\.\d+)")


def read(d: str) -> dict:
    arms: dict = {}
    p = os.path.join(d, "render.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="replace"):
            parts = line.split()
            if len(parts) < 3:
                continue
            m = re.search(r"PSNR=\s*(\d+\.\d+)", line)
            s = SSIM.search(line)
            if not m:
                continue
            arms.setdefault(parts[0], {}).update(bytes=int(parts[1]), psnr=float(m.group(1)))
            if s:
                arms[parts[0]]["ssim"] = float(s.group(1))
    p = os.path.join(d, "m37_time.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="replace"):
            m = re.match(r"wall_(\w+)\s+(\d+)", line.strip())
            if m:
                arms.setdefault(m.group(1), {})["seconds"] = int(m.group(2))
    for a in ("a", "b"):
        p = os.path.join(d, f"train_{a}.log")
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8", errors="replace").read()
        m = LAMBDA.search(text)
        if m:
            arms.setdefault(a, {})["lambda"] = float(m.group(1))
        e = EVAL.findall(text)
        if e:
            arms.setdefault(a, {})["eval_cal"] = float(e[-1])
    return arms


def verdict(arms: dict) -> dict:
    if "a" not in arms or "b" not in arms or "bytes" not in arms.get("b", {}):
        return {"branch": "incomplete"}
    a, b = arms["a"], arms["b"]
    r = b["bytes"] / a["bytes"]
    d = b["psnr"] - a["psnr"]
    out = {"byte_ratio": r, "delta_db": d}
    out["K1_smaller"] = r <= 0.95 and d >= -0.10
    out["K1_better"] = d >= 0.10 and r <= 1.02
    out["K2"] = (r < 1.0) and (b.get("ssim", 1.0) >= a.get("ssim", 0.0) - 0.005)
    if "seconds" in a and "seconds" in b:
        out["K3"] = b["seconds"] <= 1.5 * a["seconds"]
        out["time_ratio"] = b["seconds"] / a["seconds"]
    if out.get("K1_smaller") or out.get("K1_better"):
        out["branch"] = "pressure_helps_near_lossless"
    elif r < 1.0 and d < -0.10:
        out["branch"] = "pressure_trades_quality_here"
    elif r >= 0.99:
        out["branch"] = "pressure_does_nothing_full"
    else:
        out["branch"] = "pressure_trades_quality_here"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="experiments/artifacts/a4/m37")
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    arms = read(args.dir)
    if not arms:
        print(f"nothing in {args.dir}")
        return 1
    print("| arm | λ | container | B/prim (236) | PSNR | SSIM | wall |")
    print("|---|---|---|---|---|---|---|")
    for k in ("a", "b"):
        if k not in arms:
            continue
        r = arms[k]
        bp = r["bytes"] / 6_131_954 if "bytes" in r else float("nan")
        print(f"| {k} | {r.get('lambda', '—')} | {r.get('bytes', 0)/1e6:.2f} MB | {bp:.3f} | "
              f"{r.get('psnr', float('nan')):.2f} | {r.get('ssim', float('nan')):.4f} | "
              f"{r.get('seconds', '—')} s |")
    v = verdict(arms)
    print()
    if v.get("branch") == "incomplete":
        print("arm a and arm b with containers are both required")
        return 1
    print(f"b vs a: bytes ×{v['byte_ratio']:.3f}, PSNR {v['delta_db']:+.2f} dB"
          + (f", time ×{v['time_ratio']:.2f}" if "time_ratio" in v else ""))
    print("K1(smaller) " + ("PASS" if v.get("K1_smaller") else "fail")
          + "   K1(better) " + ("PASS" if v.get("K1_better") else "fail")
          + "   K2 " + ("PASS" if v.get("K2") else "fail")
          + "   K3 " + ("PASS" if v.get("K3") else ("fail" if "K3" in v else "n/a")))
    print("branch:", v["branch"])
    if args.json:
        json.dump({"arms": arms, "verdict": v}, open(args.json, "w"), indent=1)
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
