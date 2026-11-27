"""Second prior-art probe: precise, abstract-level, and it looks for the *claim* rather than the topic.

Round 1 (tools/prior_art_probe.py) sorted OpenAlex by citations and returned generic high-cited work. This probe asks
four narrow questions and then *scans abstracts* for the comparative statements that would make our contribution
incremental:

  S1  any 2024-2026 3DGS-compression paper that compares pruning against quantisation at a matched rate?
  S2  any paper that states the outlier/bulk (unbounded vs bounded perturbation) distinction for rendering quality?
  S3  in video coding, is the drift/error-propagation-vs-quantisation-noise distinction textbook? (it is; we need the
      canonical reference, not a discovery)
  S4  is the quantile/tail-functional framing of a rendering guarantee already used (VSCP, QuantileGS, AURORA...)?

Writes review/PRIOR_ART_PROBE2_2026-11.json.
"""
from __future__ import annotations

import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

OUT = Path("review/PRIOR_ART_PROBE2_2026-11.json")
UA = {"User-Agent": "care-gs-prior-art/1.0"}

# the phrases that would make our claim incremental if they appear in an abstract
COMPARE = re.compile(r"(prun\w*).{0,120}(quantiz\w*)|(quantiz\w*).{0,120}(prun\w*)", re.I)
SUPERL = re.compile(r"(more effective|better than|outperform\w*|superior to|compared (?:to|with)|"
                    r"more efficient than|whereas|in contrast)", re.I)
OUTLIER = re.compile(r"(outlier|heavy[- ]tailed|long[- ]tailed|unbounded|bounded)", re.I)


def s2(query: str, limit: int = 20, year: str = "2023-2026") -> list[dict]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": limit, "year": year,
              "fields": "title,year,abstract,venue,citationCount,externalIds"}
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=45)
            if r.status_code == 200:
                return r.json().get("data", [])
            if r.status_code in (429, 503):
                time.sleep(5 * (attempt + 1))
        except Exception:  # noqa: BLE001
            time.sleep(4)
    return []


def arxiv(q: str, n: int = 60) -> list[dict]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    params = {"search_query": q, "start": 0, "max_results": n, "sortBy": "submittedDate", "sortOrder": "descending"}
    for attempt in range(3):
        try:
            r = requests.get("http://export.arxiv.org/api/query", params=params, headers=UA, timeout=45)
            if r.status_code == 200:
                break
        except Exception:  # noqa: BLE001
            pass
        time.sleep(4 * (attempt + 1))
    else:
        return []
    root = ET.fromstring(r.text)
    out = []
    for e in root.findall("a:entry", ns):
        out.append(dict(
            id=(e.findtext("a:id", default="", namespaces=ns) or "").rsplit("/", 1)[-1],
            year=(e.findtext("a:published", default="", namespaces=ns) or "")[:4],
            title=re.sub(r"\s+", " ", e.findtext("a:title", default="", namespaces=ns) or "").strip(),
            abstract=re.sub(r"\s+", " ", e.findtext("a:summary", default="", namespaces=ns) or "").strip(),
        ))
    return out


def scan(papers: list[dict], label: str) -> list[dict]:
    hits = []
    for p in papers:
        ab = (p.get("abstract") or "")
        if not ab:
            continue
        m = COMPARE.search(ab)
        if m and SUPERL.search(ab):
            hits.append(dict(title=p.get("title", "")[:150], year=p.get("year"),
                             id=p.get("id") or (p.get("externalIds") or {}).get("ArXiv") or p.get("paperId"),
                             sentence=" ".join(ab[max(0, m.start() - 160):m.end() + 200].split())))
    print(f"  {label}: {len(hits)} of {len(papers)} abstracts contain a pruning-vs-quantisation comparison")
    return hits


def main() -> None:
    out: dict[str, object] = {}

    print("S1 3DGS compression, pruning vs quantisation")
    ax = arxiv('abs:"Gaussian splatting" AND abs:compression AND (abs:pruning OR abs:prune OR abs:quantization)', 100)
    out["S1_arxiv_scan"] = scan(ax, "arxiv 3DGS compression")
    time.sleep(1)

    print("S1b semantic scholar, comparative phrasing")
    s2hits = []
    for q in ("3D Gaussian splatting compression pruning quantization which is better",
              "3D Gaussian splatting pruning versus quantization rate-distortion comparison"):
        s2hits += s2(q, 20)
        time.sleep(2)
    out["S1b_s2"] = [dict(title=p.get("title"), year=p.get("year"), venue=p.get("venue"),
                          cites=p.get("citationCount"), id=(p.get("externalIds") or {}).get("ArXiv"))
                     for p in s2hits if COMPARE.search((p.get("abstract") or ""))]
    print(f"  s2: {len(out['S1b_s2'])} with a pruning/quantisation sentence")

    print("S2 outlier vs bulk, rendering quality")
    ax2 = arxiv('abs:"3D Gaussian" AND (abs:outlier OR abs:"heavy-tailed" OR abs:"error bound")', 60)
    out["S2_outlier_scan"] = [dict(id=p["id"], title=p["title"][:150], year=p["year"])
                              for p in ax2 if OUTLIER.search(p["abstract"])]
    print(f"  {len(out['S2_outlier_scan'])} abstracts mention outliers/boundedness")

    print("S3 video coding: drift / error propagation vs quantisation noise")
    ax3 = arxiv('abs:"error propagation" AND abs:quantization AND (abs:drift OR abs:coding)', 40)
    out["S3_drift"] = [dict(id=p["id"], title=p["title"][:150], year=p["year"]) for p in ax3]
    print(f"  {len(out['S3_drift'])} hits")

    print("S4 quantile / tail / conformal framing of a rendering guarantee")
    ax4 = arxiv('abs:"Gaussian splatting" AND (abs:conformal OR abs:quantile OR abs:certified)', 60)
    out["S4_quantile"] = [dict(id=p["id"], title=p["title"][:150], year=p["year"]) for p in ax4]
    print(f"  {len(out['S4_quantile'])} hits")

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()