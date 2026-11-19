"""Patch the rank correlation to the no-bonsai grid and state why bonsai was excluded."""
import json

import numpy as np

a = json.load(open("results_v120/audit_bound_nobonsai.json", encoding="utf-8"))
d = json.load(open("results_v120/dump_summary.json", encoding="utf-8"))
fresh = {sc["scene"]: sc["variants"]["clean"]["psnr"] for sc in d["scenes"]}
psnr = {(sc["scene"], v): fresh[sc["scene"]] - st["psnr"]
        for sc in d["scenes"] for v, st in sc["variants"].items()
        if v != "clean" and st.get("psnr") is not None}
cov, db = [], []
for r in a["rows"]:
    k = (r["scene"], r["variant"])
    if k in psnr:
        cov.append(-100 * r["drop_mean"])
        db.append(psnr[k])
rho = float(np.corrcoef(cov, db)[0, 1])
print(f"rho over {len(cov)} cells = {rho:+.2f}")

import pathlib

p = pathlib.Path("submission/cviu/main.tex")
t = p.read_text(encoding="utf-8")
old = "over the $56$ cells the rank correlation between decibels lost and points of\ncoverage lost is $+0.91$"
new = (f"over the $56$ cells the rank correlation between decibels lost and points of\n"
       f"coverage lost is ${rho:+.2f}$")
assert old in t, "rho sentence not found"
t = t.replace(old, new)

anchor = ("an edit\nthat also re-solves the camera poses")
assert anchor in t
add = (
    "\n\nThe third exclusion is an instrument failure we report rather than hide. Bonsai is in the\n"
    "degradation tables of the earlier campaign (1.24M primitives, 37 held-out views, a $10.3$-point\n"
    "loss at 30\\% pruning). For this campaign we re-stitched it from a public mirror, and the\n"
    "re-stitched asset renders at $15.8$\\,dB against its own ground truth --- a camera/ground-truth\n"
    "pairing failure, not a property of the asset. Under that failure the residuals are dominated by\n"
    "a global misalignment, so pruning barely moves the threshold count and the audit would report a\n"
    "$0.9$-point loss: a plausible number produced by a broken measurement. We excluded the\n"
    "checkpoint instead of reporting the number, which is why the audit grid has eight\n"
    "scene-checkpoints and not nine. Anyone who wants the ninth can rebuild the archive with the\n"
    "script in the deposit; the entry will then match the appendix's $10.3$ rather than our $0.9$.\n"
)
t = t.replace(anchor, add.lstrip("\n") + "\n" + anchor)
p.write_text(t, encoding="utf-8")
print("patched main.tex")
