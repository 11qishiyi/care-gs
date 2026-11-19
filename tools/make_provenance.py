"""
Provenance record for the results_v70 campaign.

Everything in this file is either read from the stored artifacts (per-scene primitive counts,
render resolutions, view counts, PSNR) or recorded from the run that produced them (archive
identity and size, tool versions). It exists so a reader can tell *which* public checkpoints
the numbers come from: several mirrors host differently-trained assets, and a reader who
fetches from a different mirror will not reproduce these numbers.
"""
import json
import os

import numpy as np

D = "results_v70"

# archive identity, recorded when the archive was fetched
ARCHIVE = {
    "name": "3dgs output archive, scenes trained for 40k iterations, with held-out ground truth",
    "host": "ModelScope dataset Jackie137/3dgs-Output",
    "object": "output-3dgs.tar.gz",
    "object_bytes": 9587304864,
    "layout": "<archive>/output/<scene>/{cameras.json, point_cloud/iteration_40000/point_cloud.ply,"
              " test/ours_40000/gt/*.png}",
    "note": "The Hugging Face mirror dylanebert/3dgs hosts differently-trained 30k checkpoints for "
            "a subset of these scenes; scripts/fetch_hf_data.py can fetch those, but the numbers in "
            "the paper come from this archive.",
}

SCENES = ["bicycle", "flowers", "stump", "treehill"]
reported = {}
for s in SCENES:
    diag = json.load(open(os.path.join(D, f"diag_{s}.json"), encoding="utf-8"))[0]
    rows = {"n_primitives": diag["n_primitives"], "render_width": diag["W"],
            "render_height": diag["H"], "held_out_views": diag["n_views"],
            "psnr_captured_gt": round(diag["protocols"]["raw"]["psnr"], 3),
            "fresh_coverage_pixel": round(diag["protocols"]["raw"]["clean_mean"], 4)}
    bat_path = os.path.join(D, f"battery_{s}.json")
    if os.path.isfile(bat_path):
        bat = json.load(open(bat_path, encoding="utf-8"))
        rows["variants_scored"] = sorted(bat["coverage"].keys())
    reported[s] = rows

out = {
    "campaign": "results_v70 and results_v80 (same archive, two rendering sessions)",
    "purpose": "everything the paper reports about releases assets comes from this campaign",
    "archive": ARCHIVE,
    "rendering": {"renderer": "gsplat", "version": "1.5.3", "downscale_factor": 4,
                  "torch": "2.4.0+cu118", "gpu": "NVIDIA A16 (16 GB)",
                  "protocol": "each held-out view rendered once per model variant, then 400 "
                              "random calibration/deployment splits"},
    "splits": {"n_splits": 400, "alpha": 0.10, "quantile": "ceil((n+1)(1-alpha))-th smallest "
                                                          "pooled calibration-pixel residual"},
    "tasks": {"local re-localisation": "32x32 GT patch, +-24 px window, tol 2 px, peak >= 0.6",
              "registration consensus": "Harris corners, 9x9 patch descriptor, ratio test, RANSAC "
                                        "translation, inlier ratio at 2 px"},
    "per_scene": reported,
}
os.makedirs(D, exist_ok=True)
json.dump(out, open(os.path.join(D, "PROVENANCE.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1)[:1200])
