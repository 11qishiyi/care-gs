"""Restore author fields for the arXiv-only bibliography entries, from the arXiv API.

Earlier the duplicated `author = {{METHOD}}` stubs were removed because they rendered as "KF-GS, KF-GS: ...". That
fixed the duplication and created a worse defect: 24 of 49 entries now print with no author at all, and the editorial
office cannot use the reference list for conflict-of-interest screening. This script reads the real author lists from
arXiv (the same source the citation verifier uses), writes them back, and also folds the arXiv identifier into the
journal field so the printed form stops reading "arXiv preprintArXiv:2609.10307".

    python tools/fix_bib_authors.py            # report only
    python tools/fix_bib_authors.py --write    # patch refs.bib
"""
from __future__ import annotations

import argparse
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BIB = Path("submission/jvcir/refs.bib")
ENTRY = re.compile(r"@(\w+)\{([^,]+),(.*?)\n\}", re.S)
ARXIV = re.compile(r"arXiv:\s*(\d{4}\.\d{4,5})")
NS = {"a": "http://www.w3.org/2005/Atom"}


def parse(text: str) -> list[tuple[str, str, str]]:
    return [(k, key.strip(), body) for k, key, body in ENTRY.findall(text)]


def fetch_authors(ids: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for i in range(0, len(ids), 20):
        chunk = ids[i:i + 20]
        url = "http://export.arxiv.org/api/query?id_list=" + ",".join(chunk) + "&max_results=50"
        for attempt in range(4):
            try:
                r = requests.get(url, timeout=40, headers={"User-Agent": "bib-fix/1.0"})
                if r.status_code == 200:
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(3 * (attempt + 1))
        else:
            continue
        root = ET.fromstring(r.text)
        for entry in root.findall("a:entry", NS):
            eid = (entry.findtext("a:id", default="", namespaces=NS) or "").rsplit("/", 1)[-1]
            eid = re.sub(r"v\d+$", "", eid)
            names = [(a.findtext("a:name", default="", namespaces=NS) or "").strip()
                     for a in entry.findall("a:author", NS)]
            names = [n for n in names if n]
            if eid and names:
                out[eid] = names
        time.sleep(0.5)
    return out


def bibtex_name(full: str) -> str:
    """'Haiyang Xu' -> 'Xu, Haiyang'; leaves already-comma'd names alone."""
    if "," in full:
        return full.strip()
    parts = full.strip().split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def fetch_doi_authors(dois: list[str]) -> dict[str, list[str]]:
    """Author lists for entries whose locator is a DOI (the journal articles), from Crossref."""
    out: dict[str, list[str]] = {}
    for doi in dois:
        for attempt in range(4):
            try:
                r = requests.get(f"https://api.crossref.org/works/{doi}", timeout=40,
                                 headers={"User-Agent": "bib-fix/1.0 (mailto:research@example.org)"})
                if r.status_code == 200:
                    break
                if r.status_code == 429:
                    time.sleep(4 * (attempt + 1))
                    continue
                break
            except Exception:  # noqa: BLE001
                time.sleep(3 * (attempt + 1))
        else:
            continue
        try:
            msg = r.json()["message"]
            names = []
            for au in msg.get("author", []) or []:
                family, given = au.get("family", ""), au.get("given", "")
                if family:
                    names.append(f"{family}, {given}" if given else family)
            if names:
                out[doi] = names
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.3)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    text = BIB.read_text(encoding="utf-8")
    entries = parse(text)
    need_arxiv, need_doi = [], []
    for kind, key, body in entries:
        if re.search(r"\n\s*author\s*=", body):
            continue
        m = ARXIV.search(body)
        if m:
            need_arxiv.append((key, m.group(1)))
            continue
        d = re.search(r"\n\s*doi\s*=\s*\{([^}]+)\}", body)
        if d:
            need_doi.append((key, d.group(1).strip()))
    print(f"{len(need_arxiv)} arXiv entries and {len(need_doi)} DOI entries need an author list")
    if not need_arxiv and not need_doi:
        return 0

    authors = fetch_authors([i for _, i in need_arxiv])
    doi_authors = fetch_doi_authors([d for _, d in need_doi])
    authors.update({k: doi_authors[d] for k, d in need_doi if d in doi_authors})
    print(f"resolved {len(authors)} of {len(need_arxiv) + len(need_doi)}")

    missing = {k for k, _ in need_arxiv + need_doi}
    doi_of = dict(need_doi)

    def patch(kind, key, body):
        key = key.strip()
        if key not in missing:
            return body
        names = authors.get(key) or (doi_of.get(key) and doi_authors.get(doi_of[key]))
        if not names:
            return body
        if len(names) > 6:
            names = names[:6] + ["others"]
        auth = " and ".join(bibtex_name(n) for n in names)
        body = body.replace("\n", f"\n  author  = {{{auth}}},\n", 1)
        m = ARXIV.search(body)
        if m:
            body = re.sub(r"journal\s*=\s*\{[^}]*\}", f"journal = {{arXiv preprint arXiv:{m.group(1)}}}", body)
            body = re.sub(r"\n\s*note\s*=\s*\{arXiv:[^}]*\}", "", body)
        return body

    patched = "\n".join(f"@{k}{{{key},{patch(k, key, body)}\n}}" for k, key, body in entries)
    changed = sum(1 for k, key, body in entries if patch(k, key, body) != body)
    print(f"would patch {changed} entries")
    if a.write:
        BIB.write_text(patched.rstrip() + "\n", encoding="utf-8", newline="\n")
        print("wrote", BIB)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
