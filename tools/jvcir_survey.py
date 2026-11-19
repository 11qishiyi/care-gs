"""Quantitative survey of recent JVCIR (ISSN 1047-3203) output.

Pulls the journal's 2025 and 2026 output from OpenAlex (abstracts + reference
counts + topics) and computes the editorial/writing conventions that can be
measured from metadata alone: title naming pattern, abstract length, reference
count, metric vocabulary, open-access share, topic mix.

Writes:
  review/JVCIR_CORPUS_2025_2026.json   raw records (id, doi, date, title, abstract, refs, oa, topic)
  review/JVCIR_SURVEY_STATS.json       the computed statistics
  review/JVCIR_SURVEY_2026-11.md       human-readable survey (generated, do not hand-edit)

Usage:
  python tools/jvcir_survey.py            # fetch (cached) + recompute
  python tools/jvcir_survey.py --refresh  # force re-fetch
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "review" / "JVCIR_CORPUS_2025_2026.json"
OUT_STATS = ROOT / "review" / "JVCIR_SURVEY_STATS.json"
OUT_MD = ROOT / "review" / "JVCIR_SURVEY_2026-11.md"

ISSN = "1047-3203"
SELECT = ",".join([
    "id", "doi", "title", "publication_date", "type", "cited_by_count",
    "referenced_works_count", "abstract_inverted_index", "primary_topic",
    "best_oa_location", "open_access", "authorships", "biblio",
])

VOCAB = {
    "PSNR": r"\bPSNR\b",
    "SSIM": r"\bSSIM\b",
    "LPIPS": r"\bLPIPS\b",
    "FID": r"\bFID\b",
    "mAP": r"\bmAP\b",
    "BD-rate": r"\bBD[\s-]?rate\b",
    "bitrate/ratio": r"\b(bit\s?rate|bitrate|compression ratio|bpp)\b",
    "FPS": r"\b(FPS|frames per second|frames/s)\b",
    "FLOPs/params": r"\b(G?FLOPs?|MACs|parameters?|model size)\b",
    "subjective/MOS": r"\b(MOS|subjective (study|experiment|assessment|test)|user study)\b",
    "ablation": r"\bablation\b",
    "code/github": r"\b(code (is )?(publicly )?available|github|open[- ]source[ds]?)\b",
    "dataset(s)": r"\b(datasets?|benchmarks?)\b",
    "speed/runtime": r"\b(runtime|running time|inference time|real[- ]time|latency)\b",
    "memory": r"\b(memory|VRAM|GPU memory)\b",
    "3D/point cloud": r"\b(3D|point cloud|mesh|splatting|NeRF|Gaussian)\b",
    "compression": r"\b(compress(ion|ed)?|quantiz(ation|ed)|prun(ing|ed)|cod(er|ec|ing))\b",
}

ACRONYM_TITLE = re.compile(r"^\s*(?:[A-Z][A-Za-z0-9]*(?:-[A-Z][A-Za-z0-9]*)*)\s*:\s+\S")

# Title-level vocabulary: the only text field the metadata providers actually carry
# for this journal (Elsevier does not deposit abstracts), so the honest denominator is
# all articles, not the 33 with abstracts.
TITLE_VOCAB = {
    "3D / point cloud / mesh": r"\b(3D|point cloud|mesh|RGB-?D)\b",
    "Gaussian / NeRF": r"\b(gaussian|splat\w*|3DGS|NeRF)\b",
    "compression / coding": r"\b(compress\w*|coding|coder|bit\s?rate|rate[- ]distortion)\b",
    "quality assessment / perceptual": r"\b(quality|perceptual|JND|just[- ]noticeable)\b",
    "efficient / lightweight / fast": r"\b(efficient|lightweight|fast|real[- ]time|accelerat\w*)\b",
    "robust / generalizable": r"\b(robust\w*|generaliz\w*)\b",
    "survey / review / benchmark": r"\b(survey|review|benchmark\w*|dataset)\b",
    "multi-modal / cross-modal": r"\b(multi[- ]?modal|cross[- ]?modal|audio[- ]visual|text[- ]guided)\b",
    "diffusion / GAN / transformer": r"\b(diffusion|GAN|transformer|mamba)\b",
    "low-light / underwater / remote sensing": r"\b(low[- ]light|underwater|remote sensing|hazy|dehaz\w*)\b",
}



def _month_windows(start: str, end: str) -> list[tuple[str, str]]:
    """Split [start, end] into calendar-month windows.

    OpenAlex (2026) requires an API key for cursor paging past the first page, so the
    survey pages by date window instead; one window per month stays under per-page=200.
    """
    y0, m0 = int(start[:4]), int(start[5:7])
    y1, m1 = int(end[:4]), int(end[5:7])
    out = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        lo = f"{y:04d}-{m:02d}-01"
        hi = f"{ny:04d}-{nm:02d}-01"
        if hi > end:
            hi = end
        if lo <= end:
            out.append((lo, hi))
        y, m = ny, nm
    return out


def fetch(from_date: str, to_date: str, refresh: bool) -> list[dict]:
    cache = OUT_JSON
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("from") == from_date and data.get("to") == to_date:
            print(f"cache hit: {len(data['records'])} records")
            return data["records"]
    records: list[dict] = []
    seen: set[str] = set()
    base = "https://api.openalex.org/works"
    windows = _month_windows(from_date, to_date)
    for i, (lo, hi) in enumerate(windows, 1):
        params = {
            "filter": f"primary_location.source.issn:{ISSN},"
                      f"from_publication_date:{lo},to_publication_date:{hi}",
            "per-page": "200",
            "select": SELECT,
            "sort": "publication_date:asc",
        }
        last = None
        for attempt in range(4):
            try:
                resp = requests.get(base, params=params, timeout=90, headers={
                    "User-Agent": "jvcir-survey/1.0 (research)",
                    "Accept": "application/json",
                })
                resp.raise_for_status()
                payload = resp.json()
                break
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(2 * (attempt + 1))
        else:
            raise SystemExit(f"OpenAlex fetch failed on {lo}..{hi}: {last}")
        for w in payload["results"]:
            wid = w["id"].rsplit("/", 1)[-1]
            if wid in seen:
                continue
            seen.add(wid)
            records.append({
                "id": wid,
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "date": w.get("publication_date"),
                "title": (w.get("title") or "").strip(),
                "type": w.get("type"),
                "cited_by": w.get("cited_by_count", 0),
                "refs": w.get("referenced_works_count", 0),
                "oa": bool((w.get("open_access") or {}).get("is_oa")),
                "oa_status": (w.get("open_access") or {}).get("oa_status"),
                "topic": ((w.get("primary_topic") or {}).get("display_name") or ""),
                "field": (((w.get("primary_topic") or {}).get("field") or {}).get("display_name") or ""),
                "abstract": inv_to_text(w.get("abstract_inverted_index")),
                "n_authors": len(w.get("authorships") or []),
            })
        print(f"  window {lo}..{hi}: {len(payload['results'])} (total {len(records)})")
        if i < len(windows):
            time.sleep(0.35)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(
        {"from": from_date, "to": to_date, "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "source": "OpenAlex /works", "issn": ISSN, "records": records},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"fetched {len(records)} records -> {OUT_JSON}")
    return records


def inv_to_text(inv: dict | None) -> str:
    if not inv:
        return ""
    pos: dict[int, str] = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.0f}%" if d else "n/a"


def summarise(records: list[dict]) -> dict:
    arts = [r for r in records if r["type"] == "article"]
    with_abs = [r for r in arts if len(r["abstract"].split()) >= 20]
    years = defaultdict(list)
    months = defaultdict(list)
    for r in arts:
        years[(r["date"] or "")[:4]].append(r)
        months[(r["date"] or "")[:7]].append(r)

    def block(rs: list[dict]) -> dict:
        refs = [r["refs"] for r in rs if r["refs"]]
        return {
            "n": len(rs),
            "refs_median": int(st.median(refs)) if refs else None,
            "refs_q1": int(st.quantiles(refs, n=4)[0]) if len(refs) > 3 else None,
            "refs_q3": int(st.quantiles(refs, n=4)[2]) if len(refs) > 3 else None,
            "refs_min": min(refs) if refs else None,
            "refs_max": max(refs) if refs else None,
            "oa_share": round(sum(1 for r in rs if r["oa"]) / len(rs), 3) if rs else None,
            "named_title_share": round(sum(1 for r in rs if ACRONYM_TITLE.match(r["title"])) / len(rs), 3) if rs else None,
        }

    def fam(pattern: str) -> list[dict]:
        rx = re.compile(pattern, re.I)
        hit = [r for r in arts if rx.search(r["title"] + " " + r["abstract"])]
        return sorted(hit, key=lambda r: r["date"] or "", reverse=True)

    title_vocab = {}
    for label, pat in TITLE_VOCAB.items():
        rx = re.compile(pat, re.I)
        title_vocab[label] = sum(1 for r in arts if rx.search(r["title"]))

    abs_vocab = {}
    for label, pat in VOCAB.items():
        rx = re.compile(pat, re.I)
        abs_vocab[label] = sum(1 for r in with_abs if rx.search(r["abstract"]))

    topics = Counter(r["topic"] for r in arts if r["topic"]).most_common(15)
    fields = Counter(r["field"] for r in arts if r["field"]).most_common(10)
    gs = fam(r"\b(gaussian splat|splatting|3DGS|NeRF|neural radiance)\b")
    comp = fam(r"\b(compress|bit\s?rate|rate[- ]distortion|BD[\s-]?rate|quantiz|coder|coding)\b")
    qa = fam(r"\b(quality assess|perceptual quality|JND|just[- ]noticeable|image quality)\b")
    newest = sorted(arts, key=lambda r: r["date"] or "", reverse=True)[:30]

    def refs_of(rs: list[dict]) -> dict:
        vals = [r["refs"] for r in rs if r["refs"]]
        return {"n": len(rs), "refs_median": int(st.median(vals)) if vals else None,
                "refs_min": min(vals) if vals else None, "refs_max": max(vals) if vals else None}

    light = lambda rs: [{"doi": r["doi"], "date": r["date"], "title": r["title"], "refs": r["refs"]} for r in rs]  # noqa: E731
    return {
        "n_articles": len(arts),
        "n_with_abstract": len(with_abs),
        "per_year": {y: block(v) for y, v in sorted(years.items())},
        "per_month": {m: len(v) for m, v in sorted(months.items())},
        "title_vocab": title_vocab,
        "abstract_vocab_subset": abs_vocab,
        "topics_top15": [{"topic": t, "n": n} for t, n in topics],
        "fields_top10": [{"field": f, "n": n} for f, n in fields],
        "gs_papers": light(gs),
        "gs_refs": refs_of(gs),
        "compression_papers": light(comp),
        "compression_refs": refs_of(comp),
        "quality_papers": light(qa),
        "quality_refs": refs_of(qa),
        "newest_30": light(newest),
    }


def write_md(records: list[dict], s: dict) -> None:
    L: list[str] = []
    A = L.append
    N = s["n_articles"]
    A("# JVCIR 语料统计（生成文件，勿手改）")
    A("")
    A(f"> 生成 {datetime.now(timezone.utc).isoformat(timespec='seconds')}（UTC）。来源 OpenAlex "
      f"`primary_location.source.issn:{ISSN}`，窗口 "
      f"{min((r['date'] or '') for r in records)} … {max((r['date'] or '') for r in records)}；")
    A(f"> 记录 {len(records)} 条，其中 `article` **{N}** 篇（其余为 editorial board / erratum / review）。")
    A("> 复现：`python tools/jvcir_survey.py --refresh`。")
    A("")
    A("**方法及其天花板（先声明，免得被读成更强的主张）**：Elsevier 不向 Crossref/OpenAlex 交付本刊的摘要"
      f"（本窗口内只有 {s['n_with_abstract']}/{N} 篇拿到可解析摘要），所以**摘要词汇统计不可用**；"
      "下表所用字段只有标题、发表日期、参考文献数（`referenced_works_count`）与 OA 标志，"
      "均为元数据级事实。正文级的体例事实（图数、表数、是否有主观实验、代码链接位置）来自 "
      "`review/JVCIR_SCOPE_2026-11.md` 里 7 篇全文逐篇解剖，不在本文件里重复。")
    A("")
    A("## 1 体量、参考文献、OA、命名体例")
    A("")
    A("| 窗口 | 篇数 | 参考文献 中位数 (Q1–Q3) | OA 占比 | 标题为 `方法名: 说明` 的占比 |")
    A("|---|---|---|---|---|")
    for y, b in s["per_year"].items():
        A(f"| {y} | {b['n']} | {b['refs_median']} ({b['refs_q1']}–{b['refs_q3']}) | "
          f"{pct(round((b['oa_share'] or 0) * b['n']), b['n'])} | {pct(round((b['named_title_share'] or 0) * b['n']), b['n'])} |")
    A("")
    A("月度节奏（篇/月）：" + "，".join(f"{m} {n}" for m, n in s["per_month"].items()))
    A("")
    A("## 2 标题词汇（全样本，n=%d）" % N)
    A("")
    A("| 术语 | 命中 | 占比 |")
    A("|---|---|---|")
    for k, v in sorted(s["title_vocab"].items(), key=lambda kv: -kv[1]):
        A(f"| {k} | {v} | {pct(v, N)} |")
    A("")
    A("## 3 主题分布（OpenAlex primary_topic）")
    A("")
    A("field：" + "，".join(f"{f['field']} {f['n']}" for f in s["fields_top10"]))
    A("")
    A("| topic | n |")
    A("|---|---|")
    for t in s["topics_top15"]:
        A(f"| {t['topic']} | {t['n']} |")
    A("")

    def famtable(title: str, key: str, rkey: str, note: str) -> None:
        rows = s[key]
        r = s[rkey]
        A(f"### {title}：{r['n']} 篇，参考文献 中位数 {r['refs_median']}（{r['refs_min']}–{r['refs_max']}）")
        A("")
        if note:
            A(note)
            A("")
        A("| 日期 | DOI | 标题 | refs |")
        A("|---|---|---|---|")
        for x in rows[:40]:
            A(f"| {x['date']} | `{x['doi']}` | {x['title']} | {x['refs']} |")
        if len(rows) > 40:
            A(f"| … | | 其余 {len(rows) - 40} 篇略（JSON 里有全量） | |")
        A("")

    A("## 4 与本稿同族的三支")
    A("")
    famtable("4.1 3DGS / NeRF / Gaussian 线（标题+摘要命中）", "gs_papers", "gs_refs",
             "这一支全部是**训练/重建侧**的模块增量；逐篇位置见 `review/CARE_GS_GAP_2026-11-18.md` §2。")
    famtable("4.2 压缩/编码线", "compression_papers", "compression_refs",
             "这一支全是经典点云/视频编码工程（G-PCC / V-PCC / VVC / JND 率控）；**没有一篇 3DGS 压缩**。")
    famtable("4.3 质量评估/感知线", "quality_papers", "quality_refs",
             "这一支决定审稿人对“质量保证”一词的默认期待：IQA 类工作普遍带主观实验与相关度（PLCC/SROCC）。")
    A("## 5 最近 30 篇（本窗口最新，用于看“现在在发什么”）")
    A("")
    A("| 日期 | DOI | 标题 | refs |")
    A("|---|---|---|---|")
    for x in s["newest_30"]:
        A(f"| {x['date']} | `{x['doi']}` | {x['title']} | {x['refs']} |")
    A("")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--from", dest="frm", default="2025-01-01")
    ap.add_argument("--to", dest="to", default=datetime.now(timezone.utc).date().isoformat())
    a = ap.parse_args(argv)
    records = fetch(a.frm, a.to, a.refresh)
    s = summarise(records)
    OUT_STATS.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(records, s)
    print(json.dumps({k: s[k] for k in ("n_articles", "n_with_abstract")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
