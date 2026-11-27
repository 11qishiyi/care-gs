"""Prior-art probe for the family law: has anyone already stated it at family level?

Four questions, four query families:
  Q1  does the 3DGS-compression literature already compare pruning against quantisation at a matched rate?
  Q2  does anyone make the outlier/bulk distinction (unbounded deletion vs bounded quantisation) explicit?
  Q3  is the general form known outside 3DGS (video coding: drift / error propagation vs quantisation noise;
      perception-distortion tradeoff)?
  Q4  is the quantile/tail-functional view of rendering error already used as the object of a guarantee?

Writes review/PRIOR_ART_PROBE_2026-11.json with the hits, so the reading list is reproducible.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

UA = {"User-Agent": "care-gs-prior-art/1.0 (mailto:research@example.org)"}
OUT = Path("review/PRIOR_ART_PROBE_2026-11.json")

QUERIES = {
    "Q1_prune_vs_quant_3dgs": '("Gaussian splatting") AND (pruning) AND (quantization) AND (compression)',
    "Q2_outlier_bulk": '(quantization) AND (pruning) AND ("rate-distortion") AND (outlier)',
    "Q3a_video_drift": '("error propagation") AND (quantization) AND (video coding) AND (drift)',
    "Q3b_perception_distortion": '"perception-distortion tradeoff"',
    "Q4_quantile_rendering": '(quantile OR conformal) AND (rendering) AND (guarantee)',
    "Q4b_tail_risk_vision": '("tail risk") AND (image quality) AND (bitrate)',
    "Q5_pcc_geometry_attribute": '("point cloud") AND (geometry) AND (attribute) AND (bitrate) AND (quality)',
}


def openalex(q: str, per_page: int = 25, since: int = 2015) -> list[dict]:
    url = "https://api.openalex.org/works"
    params = {"search": q, "per-page": per_page, "sort": "cited_by_count:desc",
              "filter": f"from_publication_date:{since}-01-01"}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=45)
            if r.status_code == 200:
                break
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3 * (attempt + 1))
    else:
        return []
    out = []
    for w in r.json().get("results", []):
        out.append(dict(
            title=(w.get("title") or "")[:180],
            year=w.get("publication_year"),
            venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            doi=w.get("doi"),
            cites=w.get("cited_by_count"),
            abstract=(w.get("abstract_inverted_index") and " ".join(
                sorted(w["abstract_inverted_index"], key=lambda k: w["abstract_inverted_index"][k][0]))[:400]) or "",
        ))
    return out


def arxiv(q: str, max_results: int = 25) -> list[dict]:
    url = "http://export.arxiv.org/api/query"
    params = {"search_query": q, "start": 0, "max_results": max_results, "sortBy": "submittedDate",
              "sortOrder": "descending"}
    import xml.etree.ElementTree as ET
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=45, headers=UA)
            if r.status_code == 200:
                break
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3 * (attempt + 1))
    else:
        return []
    root = ET.fromstring(r.text)
    out = []
    for e in root.findall("a:entry", ns):
        out.append(dict(
            title=re.sub(r"\s+", " ", (e.findtext("a:title", default="", namespaces=ns) or "")).strip()[:180],
            year=(e.findtext("a:published", default="", namespaces=ns) or "")[:4],
            id=(e.findtext("a:id", default="", namespaces=ns) or "").rsplit("/", 1)[-1],
            abstract=re.sub(r"\s+", " ", (e.findtext("a:summary", default="", namespaces=ns) or "")).strip()[:400],
        ))
    return out


def main() -> None:
    import re  # noqa: PLC0415  (used by arxiv())
    globals()["re"] = re
    hits: dict[str, list] = {}
    for name, q in QUERIES.items():
        hits[name] = openalex(q)
        print(f"{name:28s} openalex {len(hits[name]):3d}")
        time.sleep(1.2)
    ax = {
        "AX1_3dgs_compress": 'abs:"Gaussian splatting" AND abs:compression AND (abs:pruning OR abs:quantization)',
        "AX2_certified": 'abs:"Gaussian splatting" AND (abs:conformal OR abs:certified OR abs:guarantee)',
        "AX3_rate_perception": 'abs:"rate-distortion" AND abs:perception',
    }
    for name, q in ax.items():
        hits[name] = arxiv(q)
        print(f"{name:28s} arxiv    {len(hits[name]):3d}")
        time.sleep(1.0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(hits, indent=1), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()