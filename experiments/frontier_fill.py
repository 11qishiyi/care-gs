"""Re-price an existing RD table on the *measured* byte axis.

``m1_rd.json`` was built before the byte model was replaced by a measurement, so its rates
are the analytic ones (``44 B + 3K*b/8``).  Its coverage/PSNR/SSIM/LPIPS numbers, however,
come from the same renderer and the same 400-split protocol as everything else, and the
variants in it (SH 16/12/8-bit at full geometry) are exactly the low-rate end that the later
grids dropped.  Re-pricing those rows with the measured bytes therefore yields a real,
measured-rate RD point without re-rendering a single image.

    rate = n * fp32_bytes_per_prim(deg) / (zstd_morton_bytes_per_prim * stored)

which is the same formula ``m1_analyse.load_measured_rates`` uses, so the two tables stay
comparable.
"""
import argparse
import json
import os
import sys

import common as C
import m1_analyse as A

DEFAULT_M1 = os.path.join("experiments", "artifacts", "a4", "m1_rd.json")
DEFAULT_BYTES = os.path.join("experiments", "artifacts", "a4", "frontier_bytes.json")
DEFAULT_OUT = os.path.join("experiments", "artifacts", "a4", "m1_rd_measured.json")


def byte_index(doc):
    """``{(scene, spec): {rate, bpp, stored, n}}`` from an ``m4_bytes`` document."""
    out = {}
    for sc in doc.get("scenes", [doc]):
        scene = sc.get("scene", "")
        deg = int(sc.get("sh_degree", doc.get("meta", {}).get("sh_degree", 3)) or 3)
        n_total = sc.get("n")
        for row in sc.get("rows", []):
            bpp = row.get("zstd_morton_bytes_per_prim")
            if bpp is None or bpp <= 0:
                continue
            stored = float(row["stored"])
            n = float(row.get("n") or n_total or stored)
            fp32 = A.fp32_bytes_per_prim(deg)
            out[(scene, row["spec"])] = {"rate": n * fp32 / (bpp * stored),
                                         "bpp": float(bpp), "stored": stored, "n": n}
    return out


def reprice(m1_doc, idx, verbose=True):
    """Same document shape, but every matched row carries a measured rate."""
    scenes, missing, hit = [], 0, 0
    for sc in m1_doc["scenes"]:
        scene = sc["scene"]
        rows = []
        for row in sc["rows"]:
            name = row["variant"]
            src = idx.get((scene, name))
            if src is None:
                missing += 1
                continue
            new = dict(row)
            new["rate"] = src["rate"]
            new["bytes_per_prim"] = round(src["bpp"], 4)
            new["rate_model"] = row.get("rate")
            rows.append(new)
            hit += 1
        rows.sort(key=lambda r: r["rate"])
        keep = dict(sc)
        keep["rows"] = rows
        keep.pop("matched", None)          # stale: those were model-axis interpolations
        keep.pop("comparisons", None)
        scenes.append(keep)
    doc = {"meta": dict(m1_doc.get("meta", {})), "scenes": scenes}
    doc["meta"]["rate_source"] = "measured"
    doc["meta"]["repriced_from"] = "m1_rd.json"
    doc["meta"]["n_repriced"] = hit
    if verbose:
        C.log(f"repriced {hit} row(s), {missing} without a measured byte count")
    return doc


def selftest() -> int:
    fails = []

    def check(name, cond, extra=""):
        print(("  [ok] " if cond else "  [FAIL] ") + name + (f" | {extra}" if extra else ""))
        if not cond:
            fails.append(name)

    m1 = {"meta": {}, "scenes": [{"scene": "s", "rows": [
        {"variant": "sh8_g16", "rate": 3.28, "drop_pp": -0.4, "d_psnr": 0.1, "psnr": 22.1},
        {"variant": "sh4_g16", "rate": 4.92, "drop_pp": -0.5, "d_psnr": 0.12, "psnr": 22.1},
    ]}]}
    bytes_doc = {"meta": {"sh_degree": 3}, "scenes": [{"scene": "s", "n": 4_000_000, "rows": [
        {"spec": "sh8_g16", "stored": 4_000_000, "n": 4_000_000,
         "zstd_morton_bytes_per_prim": 59.0},
    ]}]}
    idx = byte_index(bytes_doc)
    check("the index keys on scene and spec", ("s", "sh8_g16") in idx)
    check("the measured rate follows the shared formula",
          abs(idx[("s", "sh8_g16")]["rate"] - 236.0 / 59.0) < 1e-9,
          f"{idx[('s', 'sh8_g16')]['rate']:.4f}")
    doc = reprice(m1, idx, verbose=False)
    rows = doc["scenes"][0]["rows"]
    check("unmeasured rows are dropped, not guessed", len(rows) == 1, str(len(rows)))
    check("the model rate is kept for the record", abs(rows[0]["rate_model"] - 3.28) < 1e-9)
    check("the rate is the measured one", abs(rows[0]["rate"] - 236.0 / 59.0) < 1e-9)
    check("coverage survives untouched", abs(rows[0]["drop_pp"] + 0.4) < 1e-9)
    check("the source is recorded", doc["meta"]["rate_source"] == "measured")
    check("stale interpolations are discarded", "matched" not in doc["scenes"][0])
    print("=" * 60)
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--m1", default=DEFAULT_M1)
    ap.add_argument("--bytes", dest="bytes_path", default=DEFAULT_BYTES)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    m1_doc = json.load(open(a.m1, encoding="utf-8"))
    idx = byte_index(json.load(open(a.bytes_path, encoding="utf-8")))
    doc = reprice(m1_doc, idx)
    if not doc["meta"]["n_repriced"]:
        raise SystemExit("no row could be repriced -- are the specs in --bytes?")
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
    C.log(f"WROTE {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
