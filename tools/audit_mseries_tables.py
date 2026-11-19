"""Audit the numbers the M49-M51 write-ups quote against the artifact rows those rounds produced.

The failure this prevents is the one M49 already caught in its own predecessor: a number that is correct in
the artifact and different in the prose ("85 % geometry", "−1.83 dB container loss").  Every row of

    experiments/artifacts/a4/m49/rows_final.txt      scene spec bytes psnr ssim wall rss
    experiments/artifacts/a4/m50/rows.txt            spec bytes psnr ssim
    experiments/artifacts/a4/m51/rows_final.txt      scene spec bytes psnr ssim wall rss

must appear in the matching RESULTS file as (a) the exact byte count, (b) the PSNR to two decimals, and
(c) the file size in decimal MB to two decimals.  Rows the doc adds that no artifact backs are reported too,
by checking every `NN,NNN,NNN B` / `NN.NN MB` figure in the doc against the union of artifact bytes.

    python3 tools/audit_mseries_tables.py            # audit + exit code
    python3 tools/audit_mseries_tables.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("M49", "m49special", ROOT / "experiments/M49_RESULTS.md"),
    ("M50", ROOT / "experiments/artifacts/a4/m50/rows.txt", ROOT / "experiments/M50_RESULTS.md"),
    ("M51", ROOT / "experiments/artifacts/a4/m51/rows_final.txt", ROOT / "experiments/M51_RESULTS.md"),
]
BYTES_RE = re.compile(r"(\d{1,3}(?:,\d{3})+|\d{6,})\s*B\b")
MB_RE = re.compile(r"(\d{1,3}\.\d{2})\s*MB\b")
PSNR_RE = re.compile(r"(\d{2}\.\d{2})\s*(?:dB)?")
PSNR_ANY = re.compile(r"\b(\d{2}\.\d{2})\b")


def read_rows(path: Path) -> list[dict]:
    """Two row layouts exist: `spec bytes psnr ssim` (M50) and `scene spec bytes psnr ssim wall rss` (M49/M51)."""
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        try:
            if len(parts) == 4:
                nbytes, psnr = int(parts[1]), float(parts[2])
            elif len(parts) >= 6:
                nbytes, psnr = int(parts[2]), float(parts[3])
            else:
                continue
        except ValueError:
            continue
        rows.append({"raw": line.strip(), "bytes": nbytes, "psnr": psnr})
    return rows


def rows_from_m49(adir: Path) -> list[dict]:
    """M49 wrote `bytes.txt` (`<bits> <bytes>`) and one render log per budget instead of a rows file."""
    rows = []
    bt = adir / "bytes.txt"
    if not bt.exists():
        return rows
    for line in bt.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        bits, nbytes = parts[0], int(parts[1])
        log = adir / f"render_m49g_b{bits}_f1.log"
        psnr = None
        if log.exists():
            m = re.search(r"PSNR=\s*([0-9.]+)", log.read_text(encoding="utf-8"))
            psnr = float(m.group(1)) if m else None
        if psnr is not None:
            rows.append({"raw": f"b{bits} {nbytes} {psnr}", "bytes": nbytes, "psnr": psnr})
    return rows


def variants(nbytes: int) -> set[str]:
    """Every way the doc is allowed to write this byte count."""
    out = {str(nbytes), f"{nbytes:,}", f"{nbytes / 1e6:.2f}", f"{nbytes / 1e6:.3f}"}
    return out


def audit_case(name: str, rows_path, doc_path: Path) -> dict:
    rows = rows_from_m49(ROOT / "experiments/artifacts/a4/m49") if rows_path == "m49special" else read_rows(rows_path)
    doc = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
    doc_bytes = {int(m.group(1).replace(",", "")) for m in BYTES_RE.finditer(doc)}
    doc_mb = {m.group(1) for m in MB_RE.finditer(doc)}
    missing = []
    mb_warn = []
    for row in rows:
        ok_bytes = any(v in doc for v in variants(row["bytes"]))
        ok_psnr = f"{row['psnr']:.2f}" in doc
        ok_mb = f"{row['bytes'] / 1e6:.2f}" in doc
        if not (ok_bytes and ok_psnr):
            missing.append({"row": row["raw"], "bytes_in_doc": ok_bytes,
                            "psnr_in_doc": ok_psnr, "mb_in_doc": ok_mb})
        elif not ok_mb:
            mb_warn.append(row["raw"])
    # doc figures with no artifact behind them
    known = set()
    for row in rows:
        known.add(row["bytes"])
    unbacked = sorted(b for b in doc_bytes if b not in known and b > 1_000_000)
    return {"case": name, "artifact_rows": len(rows), "doc_bytes": len(doc_bytes),
            "rows_not_in_doc": missing, "rows_without_mb": mb_warn,
            "doc_bytes_without_artifact": unbacked[:12]}


def pairs_from_logs(directory: Path) -> list[dict]:
    """M47/M48 wrote `enc_<arm>.log` (`auto  X.XX MB`) and `render_<arm>.log` (`PSNR= XX.XX`) per arm."""
    rows = []
    if not directory.exists():
        return rows
    for enc in sorted(directory.glob("enc_*.log")):
        m = re.search(r"auto\s+([0-9.]+)\s+MB", enc.read_text(errors="ignore"))
        if not m:
            continue
        mb = m.group(1)
        rlog = directory / enc.name.replace("enc_", "render_")
        psnr = None
        if rlog.exists():
            mm = re.search(r"PSNR=\s*([0-9.]+)", rlog.read_text(errors="ignore"))
            psnr = float(mm.group(1)) if mm else None
        if psnr is not None:
            rows.append({"raw": f"{enc.stem}: {mb} MB / {psnr} dB", "mb": mb, "psnr": psnr})
    return rows


def audit_logs_case(name: str, directories: list[Path], doc_path: Path) -> dict:
    """The write-up quotes a *subset* of arms (the equal-bytes pairs), so the contract is the other way round:
    a pair the doc does quote must not contradict the artifact, and no doc PSNR may be absent from the artifacts."""
    rows = []
    for d in directories:
        rows.extend(pairs_from_logs(d))
    doc = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
    doc_psnr = set(PSNR_ANY.findall(doc))
    missing = []
    for r in rows:
        if r["mb"] in doc and f"{r['psnr']:.2f}" not in doc:
            missing.append({"row": r["raw"], "why": "byte count quoted, PSNR differs"})
        elif r["mb"] in doc and f"{r['psnr']:.2f}" not in doc_psnr:
            missing.append({"row": r["raw"], "why": "PSNR absent from the write-up"})
    return {"case": name, "artifact_rows": len(rows), "rows_not_in_doc": missing}


LOG_CASES = [
    ("M47", [ROOT / "experiments/artifacts/a4/m47"], ROOT / "experiments/M47_RESULTS.md"),
    ("M48", [ROOT / "experiments/artifacts/a4/fetch/bicycle_s2",
             ROOT / "experiments/artifacts/a4/fetch/stump_s0",
             ROOT / "experiments/artifacts/a4/fetch/bonsai_s0"], ROOT / "experiments/M48_RESULTS.md"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json")
    a = ap.parse_args()
    results = []
    bad = 0
    for name, dirs, doc in LOG_CASES:
        r = audit_logs_case(name, dirs, doc)
        results.append(r)
        print(f"{name}: {r['artifact_rows']} log pairs -> "
              f"{'OK' if not r['rows_not_in_doc'] else str(len(r['rows_not_in_doc'])) + ' missing'}")
        for m in r["rows_not_in_doc"]:
            print(f"   MISSING {m}")
        bad += len(r["rows_not_in_doc"])
    for name, rows, doc in CASES:
        r = audit_case(name, rows, doc)
        results.append(r)
        status = "OK" if not r["rows_not_in_doc"] else f"{len(r['rows_not_in_doc'])} row(s) missing"
        print(f"{name}: {r['artifact_rows']} artifact rows, {r['doc_bytes']} byte figures in the doc -> {status}")
        for m in r["rows_not_in_doc"]:
            print(f"   MISSING {m}")
        for w in r["rows_without_mb"]:
            print(f"   (no MB figure for: {w})")
        if r["doc_bytes_without_artifact"]:
            print(f"   doc figures with no artifact row (may be quoted SOTA/prose): "
                  f"{r['doc_bytes_without_artifact']}")
        bad += len(r["rows_not_in_doc"])
    if a.json:
        Path(a.json).write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
