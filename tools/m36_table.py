"""Assemble the M36 three-arm table: bytes, PSNR, wall clock, and the calibrated lambda per arm.

    python tools/m36_table.py --dir experiments/artifacts/a4/m36

Inputs, all written by `experiments/run_m36.sh`:
  * ``render.txt``      -- ``<arm> <bytes> <probe_render line with PSNR>``
  * ``m36_time.txt``    -- ``wall_<arm> <seconds> s``
  * ``train_<arm>.log`` -- the ``[rate] calibrated lambda=...`` line, and the final eval PSNR

The criteria are evaluated here rather than by hand, so that the branch follows from the numbers:
R1 (rate pays), R2 (it is not weight decay), R3 (affordable).
"""
from __future__ import annotations

import argparse
import json
import os
import re

LAMBDA = re.compile(r"\[rate\] calibrated lambda=(\S+) \(render grad (\S+), rate grad (\S+),")
PSNR = re.compile(r"psnr[=:\s]+(\d+\.\d+)", re.IGNORECASE)
EVAL = re.compile(r"\[eval\].*?psnr[=:\s]+(\d+\.\d+)", re.IGNORECASE)


def read_arms(d: str) -> dict:
    arms = {}
    render = os.path.join(d, "render.txt")
    if os.path.exists(render):
        for line in open(render, encoding="utf-8", errors="replace"):
            parts = line.split()
            if len(parts) < 3:
                continue
            m = PSNR.search(line)
            if not m:
                continue
            arms.setdefault(parts[0], {})["bytes"] = int(parts[1])
            arms[parts[0]]["psnr"] = float(m.group(1))
    times = os.path.join(d, "m36_time.txt")
    if os.path.exists(times):
        for line in open(times, encoding="utf-8", errors="replace"):
            m = re.match(r"wall_(\w+)\s+(\d+)", line.strip())
            if m:
                arms.setdefault(m.group(1), {})["seconds"] = int(m.group(2))
    for arm in list(arms) + [a for a in ("a", "b", "c") if a not in arms]:
        log = os.path.join(d, f"train_{arm}.log")
        if not os.path.exists(log):
            continue
        text = open(log, encoding="utf-8", errors="replace").read()
        m = LAMBDA.search(text)
        if m:
            arms.setdefault(arm, {})["lambda"] = float(m.group(1))
            arms[arm]["grad_render"] = float(m.group(2))
            arms[arm]["grad_rate"] = float(m.group(3))
        evals = [float(x) for x in EVAL.findall(text)] or [float(x) for x in PSNR.findall(text)]
        if evals:
            arms.setdefault(arm, {})["train_eval_psnr"] = evals[-1]
    return arms


def verdict(arms: dict) -> dict:
    out = {}
    if "a" not in arms or "b" not in arms:
        return {"branch": "incomplete", "why": "arms a and b are both required"}
    a, b = arms["a"], arms["b"]
    if "bytes" not in a or "bytes" not in b:
        return {"branch": "incomplete", "why": "container sizes missing"}
    ab = b["bytes"] / a["bytes"]
    adb = b["psnr"] - a["psnr"]
    out["b_vs_a"] = dict(byte_ratio=ab, delta_db=adb)
    #: a dominance clause, added after the fact: the pre-registered criteria assumed the pressure *trades*
    #: bytes for dB, and the measurement came back with both axes improving, which no clause covered.
    out["b_dominates_a"] = ab < 1.0 and adb > 0.0
    out["R1_bytes"] = ab <= 1.02 and adb >= 0.5
    out["R1_matched_psnr"] = ab <= 0.85
    if "c" in arms and "bytes" in arms["c"]:
        c = arms["c"]
        out["c_vs_b"] = dict(byte_ratio=c["bytes"] / b["bytes"], delta_db=b["psnr"] - c["psnr"])
        out["R2"] = (abs(c["bytes"] / b["bytes"] - 1) <= 0.02) and (b["psnr"] - c["psnr"] >= 0.3)
    if "seconds" in a and "seconds" in b:
        out["R3"] = b["seconds"] <= 1.5 * a["seconds"]
        out["b_vs_a"]["time_ratio"] = b["seconds"] / a["seconds"]
    if out.get("R1_bytes") or out.get("R1_matched_psnr"):
        out["branch"] = "rate_pressure_pays" if out.get("R2", False) else "only_shrinkage_pays"
    else:
        out["branch"] = "rate_pressure_does_not_pay"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="experiments/artifacts/a4/m36")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    arms = read_arms(a.dir)
    if not arms:
        print(f"nothing to read in {a.dir}")
        return 1
    print("| arm | loss | λ | container | PSNR | wall |")
    print("|---|---|---|---|---|---|")
    names = {"a": "0.8 L1 + 0.2 (1−SSIM)", "b": "+ log rate term", "c": "+ L2 control",
             "d": "+ log rate term, 15 % share"}
    for k in ("a", "b", "c", "d"):
        if k not in arms:
            continue
        r = arms[k]
        print(f"| {k} | {names[k]} | {r.get('lambda', '—')} | "
              f"{r['bytes']/1e6:.2f} MB | {r['psnr']:.2f} | {r.get('seconds', '—')} s |")
    v = verdict(arms)
    print()
    for key in ("b_vs_a", "c_vs_b"):
        if key in v:
            d = v[key]
            print(f"{key}: byte ratio {d['byte_ratio']:.3f}, ΔdB {d['delta_db']:+.2f}"
                  + (f", time ratio {d['time_ratio']:.2f}" if "time_ratio" in d else ""))
    print("R1 (bytes) " + ("PASS" if v.get("R1_bytes") else "fail")
          + "   R1 (matched PSNR) " + ("PASS" if v.get("R1_matched_psnr") else "fail")
          + "   R2 " + ("PASS" if v.get("R2") else ("fail" if "R2" in v else "n/a"))
          + "   R3 " + ("PASS" if v.get("R3") else ("fail" if "R3" in v else "n/a")))
    if v.get("b_dominates_a"):
        print("b Pareto-dominates a (fewer bytes AND more dB) -- no pre-registered clause covers this case")
    print("branch:", v["branch"], v.get("why", ""))
    if a.json:
        json.dump({"arms": arms, "verdict": v}, open(a.json, "w"), indent=1)
        print("wrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
