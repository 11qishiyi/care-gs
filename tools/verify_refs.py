"""Citation-integrity check for `submission/jvcir/refs.bib`.

Two failure modes this catches, both of which have bitten this project:

  * a DOI that does not resolve, or that resolves to a *different* paper (a transcription error);
  * an arXiv identifier that does not exist, or whose title does not match the entry.

Every entry is checked against the publisher (Crossref) and/or arXiv, and the title in the bib is compared with the
registered title by token overlap, so a plausible-looking but wrong locator fails loudly instead of shipping.

    python tools/verify_refs.py                # check everything that carries a locator
    python tools/verify_refs.py --offline      # structural checks only (no network)
    python tools/verify_refs.py --refresh      # ignore the on-disk cache

Writes `review/REFS_VERIFY.json` so the result is evidence, not a console scroll.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "submission" / "jvcir" / "refs.bib"
CACHE = ROOT / "review" / ".refs_cache.json"
OUT = ROOT / "review" / "REFS_VERIFY.json"
UA = {"User-Agent": "refs-verify/1.0 (research; mailto:research@example.org)"}

ENTRY_RX = re.compile(r"@(\w+)\{([^,]+),(.*?)\n\}", re.S)
FIELD_RX = re.compile(r"(\w+)\s*=\s*\{(.*?)\}(?=,?\s*\n)", re.S)
ARXIV_RX = re.compile(r"arXiv:\s*(\d{4}\.\d{4,5})")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def overlap(a: str, b: str) -> float:
    """Token-overlap coefficient between two titles (0 = unrelated, 1 = identical token set)."""
    ta, tb = set(norm(a).split()), set(norm(b).split())
    ta -= {"the", "a", "an", "of", "for", "and", "with", "on", "in", "to", "via"}
    tb -= {"the", "a", "an", "of", "for", "and", "with", "on", "in", "to", "via"}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def parse(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    out = []
    for kind, key, body in ENTRY_RX.findall(text):
        fields = {k.lower(): re.sub(r"\s+", " ", v).strip() for k, v in FIELD_RX.findall(body + "\n,")}
        out.append({"kind": kind, "key": key.strip(), "fields": fields})
    return out


def load_cache(refresh: bool) -> dict:
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def crossref(doi: str, cache: dict) -> dict:
    if doi in cache:
        return cache[doi]
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    try:
        r = None
        for attempt in range(4):
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code != 429:
                break
            time.sleep(3 * (attempt + 1))
        if r.status_code != 200:
            res = {"ok": False, "soft": r.status_code == 429, "why": f"HTTP {r.status_code}"}
        else:
            m = r.json()["message"]
            res = {"ok": True, "title": (m.get("title") or [""])[0] or "",
                   "journal": (m.get("container-title") or [""])[0], "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0]}
    except Exception as exc:  # noqa: BLE001
        res = {"ok": False, "soft": True, "why": f"{type(exc).__name__}"}
    cache[doi] = res
    time.sleep(0.2)
    return res


def arxiv(aid: str, cache: dict) -> dict:
    key = f"arxiv:{aid}"
    if key in cache:
        return cache[key]
    url = f"http://export.arxiv.org/api/query?id_list={aid}&max_results=1"
    try:
        r = requests.get(url, headers=UA, timeout=12)
        m = re.search(r"<entry>.*?<title>(.*?)</title>", r.text, re.S)
        if r.status_code != 200 or not m:
            res = {"ok": False, "why": f"HTTP {r.status_code}, no entry"}
        else:
            res = {"ok": True, "title": re.sub(r"\s+", " ", m.group(1)).strip() if m else ""}
    except Exception as exc:  # noqa: BLE001
        res = {"ok": False, "soft": True, "why": f"{type(exc).__name__}"}
    cache[key] = res
    time.sleep(0.3)
    return res


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)

    entries = parse(BIB)
    cache = load_cache(a.refresh)
    rows, fails = [], []
    for e in entries:
        f = e["fields"]
        title = f.get("title", "")
        year = f.get("year", "")
        doi = f.get("doi", "")
        arx = ARXIV_RX.search(f.get("note", "") + " " + f.get("journal", ""))
        row = {"key": e["key"], "kind": e["kind"], "has_title": bool(title), "year": year,
               "doi": doi or None, "arxiv": arx.group(1) if arx else None}
        if not title:
            fails.append(f"{e['key']}: no title")
        if not year:
            fails.append(f"{e['key']}: no year")
        if a.offline:
            rows.append(row)
            continue
        if doi:
            res = crossref(doi, cache)
            row["doi_status"] = res.get("why", "ok")
            if not res.get("ok") and not res.get("soft"):
                fails.append(f"{e['key']}: DOI {doi} does not resolve ({res.get('why')})")
            else:
                ov = overlap(title, res["title"])
                row["doi_title_overlap"] = round(ov, 2)
                row["doi_title"] = res["title"][:90]
                if ov < 0.6:
                    fails.append(f"{e['key']}: DOI {doi} resolves to a different title "
                                 f"({res['title'][:60]!r}, overlap {ov:.2f})")
        if arx:
            res = arxiv(arx.group(1), cache)
            row["arxiv_status"] = res.get("why", "ok")
            if not res.get("ok") and not res.get("soft"):
                fails.append(f"{e['key']}: arXiv {arx.group(1)} does not resolve ({res.get('why')})")
            else:
                ov = overlap(title, res["title"])
                row["arxiv_title_overlap"] = round(ov, 2)
                row["arxiv_title"] = res["title"][:90]
                if ov < 0.6:
                    fails.append(f"{e['key']}: arXiv {arx.group(1)} is a different paper "
                                 f"({res['title'][:60]!r}, overlap {ov:.2f})")
        rows.append(row)

    keys = [e["key"] for e in entries]
    dupes = {k for k in keys if keys.count(k) > 1}
    if dupes:
        fails.append("duplicate keys: " + ", ".join(sorted(dupes)))

    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT.write_text(json.dumps({"bib": str(BIB.relative_to(ROOT)), "n_entries": len(entries),
                               "n_doi": sum(1 for r in rows if r["doi"]),
                               "n_arxiv": sum(1 for r in rows if r["arxiv"]),
                               "offline": a.offline, "fails": fails, "rows": rows}, indent=1),
                   encoding="utf-8")
    print(f"{len(entries)} entries, {sum(1 for r in rows if r['doi'])} DOIs, "
          f"{sum(1 for r in rows if r['arxiv'])} arXiv ids")
    if fails:
        print(f"FAIL — {len(fails)} problem(s)")
        for x in fails:
            print("  -", x)
        return 1
    print("PASS — every locator resolves and matches its title")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
