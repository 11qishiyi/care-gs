# JVCIR (Journal of Visual Communication and Image Representation) — Editorial & Formal Requirements Brief

Compiled 2026-11-18. Publisher: Elsevier (Academic Press imprint). ISSN 1047-3203 / 1095-9076.
Editor-in-Chief: **Junsong Yuan** (University at Buffalo), 2025–present.
Submission portal: `https://www.editorialmanager.com/JVCI`.

---

## 1. Scope

**Official aims & scope (verbatim):**

> "The Journal of Visual Communication and Image Representation publishes papers on state-of-the-art visual communication and image representation, with emphasis on novel technologies and theoretical work in this multidisciplinary area of pure and applied research. The field of visual communication and image representation is considered in its broadest sense and covers both digital and analog aspects as well as processing and communication in biological visual systems."

Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/about/aims-and-scope (identical text in the Guide for Authors, https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/guide-for-authors)

**Research Areas (official list, 19 items, verbatim):**

Image analysis and synthesis · Mathematical morphology · Computer vision · Image understanding and scene analysis · Video understanding · **RGB-D and 3D processing** · **Deep learning for visual signal processing** · Deterministic and stochastic image modeling · **Visual data reduction and compression** · Image coding and video communication · Virtual and augmented reality for visual communication · Privacy-Enhancing technologies for images and videos · Data hiding, perceptual hashing, fingerprinting for images and videos · Image and video forensics and counterforensics · Biological and medical imaging · Early processing in biological visual systems · Psychophysical analysis of visual perception · Remote sensing

Source: same URLs as above.

**Subject areas (Elsevier classification):** Electrical and Electronic Engineering; Computer Vision and Pattern Recognition; Signal Processing.
Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/about/insights

**Bibliometrics as displayed by the publisher:** Impact Factor 2.8; CiteScore 6.6.
Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/about/insights

> Conflict noted: X-MOL lists IF 3.1 for 2024 (https://www.x-mol.com/8paper/1201710390262435840); LetPub reports IF 2.8 with WoS JIF quartiles Q3 (CS-Information Systems, 150/267) and Q2 (CS-Software Engineering, 61/130) (https://www.letpub.com/journal-selector/journal/5437); Peeref reports JCR 2026 quartiles Q3/Q2 matching LetPub (https://www.peeref.com/zh/journals/5437/journal-of-visual-communication-and-image-representation). The publisher's own 2.8 figure should be treated as current; X-MOL's 3.1 appears stale.

**Scope-fit evidence for 3D Gaussian Splatting:** JVCIR actively publishes 3DGS work, e.g. "Depth error points optimization for 3D Gaussian Splatting in few-shot synthesis", DOI 10.1016/j.jvcir.2025.104682 (https://www.cqvip.com/authorservice/00854JP1MNC85J5XMNDG0JP1MPDO8) and "KF-GS: Kalman filter-guided Gaussian splatting for real-time high-quality dynamic scene reconstruction", DOI 10.1016/j.jvcir.2026.104815 (https://www.cqvip.com/authorservice/00854JP1MNC04ILX67BO9JP1MPDO8).

---

## 2. Article types and length limits

**Official statement (the complete enumeration):**

> "Regular papers, research reports, and short communications describing either original research results or novel technologies are welcome."

Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/guide-for-authors

| Type | Accepted? | Stated length limit |
|---|---|---|
| Regular research paper | Yes (explicit) | **None stated** — no page or word cap appears anywhere in the Guide for Authors |
| Research report | Yes (explicit) | None stated |
| Short communication | Yes (explicit) | None stated (no max page/word count given) |
| Survey / review article | Not enumerated, **but published in practice** | None stated |
| Software / tool paper | **Not an article type** | — |
| Benchmark / dataset paper | **Not an article type** | — |
| Registered report | **Not offered** | — |

Notes and evidence:

- **No hard length limit exists in the official documentation.** The Guide for Authors contains no "types of paper"/length section; this is a verified *absence*, not an unverified claim. Third-party summaries reproduce the same three-type list with no length figures, e.g. X-MOL's "收录体裁 | Regular papers, research reports, and short communications" (https://www.x-mol.com/8paper/1201710390262435840).
- **Review articles do appear** despite not being enumerated: ScienceDirect groups Volume 86 (July 2022) under a **"Review Papers"** heading with entries tagged "Review article" (https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/vol/86/suppl/C); ACM DL tags JVCIR Vol. 112 (Nov 2025) as `review-article` (https://dl.acm.org/profile/99660146793); earlier surveys exist, e.g. "An extensive review on spectral imaging in biometric systems" (Vol. 65, 2019, https://dblp.dagstuhl.de/db/journals/jvcir/jvcir65.html) and "A survey of recent work on fine-grained image classification techniques" (Vol. 59, 2019, https://dl.acm.org/profile/99660159149). So surveys are accepted as *regular submissions framed as reviews*; there is no separate review track with its own rules.
- **Software/tool and benchmark/dataset papers have no dedicated type.** They can only enter as a regular paper whose contribution is framed as a method/representation advance. Whether such a paper would survive editorial screening is **unverified**; no JVCIR policy text addresses it either way.
- **Registered reports are not an article type.** The phrase "registered report" appears in the Guide only in the boilerplate prior-publication exception ("The work described has not been published previously except in the form of a preprint, abstract, published lecture, academic thesis, or registered report"), which is standard Elsevier text and does not create an RR track. Source: Guide for Authors (URL above).
- Practical length norm (author inference, not policy): published JVCIR articles typically run ~10–16 journal pages; **unverified** as a rule.

---

## 3. Submission checklist specifics

All items below are from the official Guide for Authors unless another URL is given:
https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/guide-for-authors

**Highlights — MANDATORY.**
> "You are required to provide article highlights at submission."
- **3 to 5 bullet points, each a maximum of 85 characters, including spaces.**
- Submitted as a **separate editable file** with the word "highlights" in the file name.

**Abstract — required, ≤250 words.**
> "You are required to provide a concise and factual abstract that does not exceed 250 words."
- Must stand alone; avoid references; define any abbreviations at first mention.

**Keywords — required, 1 to 7.**
> "You are required to provide 1 to 7 keywords for indexing purposes."
- In English; avoid multi-word keywords containing "and"/"of"; abbreviations only if firmly established.

**Graphical abstract — ENCOURAGED, not mandatory.**
> "You are encouraged to provide a graphical abstract at submission."
- At least **1328 pixels wide**, longest side horizontal, readable at a width of **13 cm**.
- Preferred file types: **TIFF, EPS, PDF, or MS Office**; separate file; third-party permissions required.

**CRediT author statement — REQUIRED.**
> "Corresponding authors are required to acknowledge co-author contributions using CRediT (Contributor Roles Taxonomy) roles."
- The 14 standard roles are listed (Conceptualization … Writing – review and editing).

**Declaration of competing interests — REQUIRED.**
- "The declarations tool should always be completed." Authors with nothing to declare select "I have nothing to declare."
- The generated Word file must be uploaded at the "attach/upload files" step, saved as **.doc/.docx**; signatures not required.

**Funding sources — REQUIRED disclosure**, in a fixed format; if none: "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."

**Data availability statement — REQUIRED, and this is the strictest formal item for code/data.**
> "For this journal, **Option C** instructions from our research data guidelines apply. This means that you are **required** to: Deposit your research data in a relevant data repository. Provide a link to the dataset during the submission process. If sharing your research data isn't possible, make a statement explaining why during the submission process. The statement will appear in your published article."

Option C is the *mandatory* tier of Elsevier's five-tier scheme — "You are required to" (contrast Option A/B, "You are encouraged to"): https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-guidelines
- Elsevier's definition of research data explicitly includes "software, code, models, algorithms, protocols, methods".
- **Mendeley Data** is supported for depositing "raw and processed data, video, code, software, algorithms, protocols, and methods"; the dataset DOI can be supplied at submission and is listed next to the published article.

**Declaration of generative AI — REQUIRED if AI was used.** A new section titled "Declaration of generative AI and AI-assisted technologies in the manuscript preparation process" placed **before the reference list**. Not needed for basic grammar/spelling/reference tools. AI may not be listed as an author. AI must not be used to create or alter primary experimental images.

**Cover letter — not mentioned anywhere in the Guide for Authors. Unverified** whether the Editorial Manager form makes it mandatory or optional. No JVCIR-specific cover-letter guidance was found.

**Suggested reviewers — not mentioned in the Guide for Authors. Unverified** whether requested or capped. (Editorial Manager generally exposes an optional reviewer-suggestion field; no JVCIR policy text found.)

**LaTeX / file format.**
- "Submit files with .doc/.docx extensions for Word and .tex for LaTeX files. **A PDF is not an acceptable source file.**"
- "Format Word files in a **single-column** layout. Double-column formatting is only permitted for LaTeX submissions."
- "We encourage you use our **LaTeX template** when preparing a LaTeX submission" — i.e. the standard Elsevier `elsarticle` class (the Guide links Elsevier's LaTeX template/support pages rather than naming `elsarticle.cls` explicitly; **the specific class name is not stated on the JVCIR page**).
- Editable source files required at submission or revision; remove all strikethrough/underline.

**Reference style.**
- "This journal does **not set strict requirements on reference formatting at submission**" — any style, as long as it is **consistent** and includes authors, titles, year, volume, article number, pagination where applicable.
- Final style: **numbered square brackets in order of appearance**, e.g. "[3,6]"; journal names abbreviated per **LTWA**; journal style applied at **proof stage**.
- DOIs encouraged; [dataset] and [software] tags supported; preprints must be marked as such with a DOI.

**Figure requirements.**
- Artwork supplied as **separate files**, cited in text, numbered in order, logical naming (Figure_1 …).
- Photographs (colour/greyscale): TIFF/JPG/PNG, **min 300 dpi** (min width 1063 px single column, 2244 px full page).
- Bitmapped line drawings: TIFF/JPG/PNG, **min 1000 dpi** (min width 3543 px single column, 7480 px full page).
- Vector drawings: EPS/PDF with fonts embedded or text as graphics.
- Charts/large tables: XLS/XLSX. Annotated images: PPT/PPTX (embedded images ≥300 dpi).
- Do **not** submit low-resolution files, disproportionately small text, or **multiple images combined into one file** (exception: intentionally compared images, e.g. before/after).
- Every figure needs a caption (brief title + description); colour must be accessible to colour-vision-impaired readers.

**Other required elements:** title page with corresponding author e-mail (published), numbered sections (1, 1.1, 1.1.1), acknowledgements in a separate section immediately before the references, appendices numbered A/B with Eq. (A.1)/Table A.1, SI units, editable (not image) equations and tables.
**Video:** accepted; ≤150 MB per file, ≤1 GB total; "stills" required.
**Proofs:** corrections within **2 days**.

---

## 4. Review process

**Anonymity: SINGLE anonymized (single-blind).**
> "This journal follows a **single anonymized** review process. Your submission will initially be assessed by our editors. If your submission is deemed suitable, it will typically be sent to be reviewed by a **minimum of two reviewers** for an independent expert assessment of the scientific quality. Our editors decide whether to accept or reject your article."

Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/guide-for-authors
Implication: author identities are visible to reviewers; no need to anonymise the manuscript.

> **Conflict flagged.** A Baidu Developer article claims "双盲审稿扩展：JVCIR 2023年试点作者-审稿人双向匿名制度" ("JVCIR piloted double-anonymous review in 2023") — https://developer.baidu.com/article/detail.html?id=3663719. This is **contradicted by the official Guide for Authors**, which states single anonymized, and appears to be low-quality/AI-generated content with no primary source. Treat as **false/unreliable**; the official page governs.

**Publisher-stated timeline (journal insights page, median values):**
| Stage | Days |
|---|---|
| Submission → first decision | **15** |
| Submission → decision after review | **98** |
| Submission → acceptance | **215** |
| Acceptance → online publication | **9** |

Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/about/insights

**Author-reported / aggregator-reported times:**
| Source | Reported figure |
|---|---|
| LetPub (176 author reviews) | "Average Peer Review: **About 12.0 months**"; competitiveness "Easy" — https://www.letpub.com/journal-selector/journal/5437 |
| 小木虫 / Muchong (20 contributors) | "平均 **9.9** 个月的审稿周期" (avg 9.9 months, unofficial) — https://mob.muchong.com/bbs/journal.php/journal.php?view=detail&jid=5464 |
| Peeref | "平均审稿时间 **14.3 Week(s)**" — https://www.peeref.com/zh/journals/5437/journal-of-visual-communication-and-image-representation |
| X-MOL | "平均12.0个月 / 平均14.3周" (both figures shown) — https://www.x-mol.com/8paper/1201710390262435840 |

**Dated individual cases (most reliable evidence of the modern spread):**
- Submit **Feb 2026** → two revisions → accepted **end of April 2026** → published 3 days later (≈2.5 months) — https://www.peeref.com/zh/journals/5437/journal-of-visual-communication-and-image-representation
- **27 Jan 2026** submit → 11 Mar 2026 major revision → 1 Apr resubmit → 13 Apr minor-revision acceptance → 17 Apr 2026 accepted (≈3 months) — same URL
- **10 Oct 2024** submit → 22 Oct 2024 first round → 31 Dec 2024 major revision → 27 Jan 2025 resubmit → 11 Mar 2025 second round → 8 May 2025 accepted (≈7 months) — same URL
- **Four rounds** of revision (major, major, minor, major) before acceptance — same URL
- **10 Mar 2020** submit → **17 Dec 2020** major revision → 12 Feb 2021 resubmit → 30 May 2021 accepted (≈14.5 months) — https://mob.muchong.com/bbs/journal.php/journal.php?view=detail&jid=5464
- "19年8月4号投稿，一直是with editor，已经9个月了" (9 months stuck at "with editor", 2019–2020) — same URL
- **≈6 months** end-to-end with a 2-month first round and 1-month second round (2017 report) — same URL

**Net range to plan for:** ~2.5–3 months for a smooth two-revision acceptance; **~7 months** typical; 9–14 months in the tail. The publisher's 215-day (≈7-month) submission-to-acceptance median matches the author-reported cases well; the oft-quoted "12 months" figure is an average skewed by pre-2021 slow years.

**Appeals:** one appeal per submission only, decision final (Guide for Authors).
**Special issues** follow the same peer review but a guest editor may handle reviewers and recommend a decision; the journal editor makes the final decision.

---

## 5. Open access / APC

- **Hybrid**: authors choose gold OA or subscription at acceptance; "Your publication choice will have no effect on the peer review process or acceptance of your submission."
- **APC: USD 2,660 (excluding taxes), "All articles"** — i.e. one flat price for every article type.
  Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/open-access-options
- Independently corroborated on the journal comparison table: "USD 2,660". Source: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/about/insights
- **Licences offered:** CC BY, CC BY-NC, CC BY-NC-ND (CC BY can be applied for post-acceptance to satisfy funders).
- **Subscription route costs the author nothing** ("No open access publication fee").
- **Green OA embargo: 24 months** for the accepted manuscript via an institutional repository; the published PDF may not be posted on ResearchGate/Academia.edu.
- **Waivers/discounts:** the guide states no discretionary waiver policy. What exists is (a) the **"Best price promise"** — a personalised APC computed at submission from country, institutional affiliation and society membership; and (b) **open access agreements** with institutions/consortia that may cover the APC. Whether JVCIR grants individual waivers to unfunded authors is **unverified**; LetPub lists "APC Waiver: N/A" (https://www.letpub.com/journal-selector/journal/5437).
- Gold OA uptake is low: **6.67%** of articles (LetPub, same URL; also Peeref).

---

## 6. Desk-rejection patterns

There is **no JVCIR editorial, "why manuscripts are rejected" note, or published desk-rejection criterion list** — searches for one returned nothing. **Unverified** as an official policy. What follows is inference from the publisher's own metrics plus documented author reports.

**Structural inference from official data:** a **15-day median submission-to-first-decision** (https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/about/insights) combined with a 98-day median to a post-review decision means a large share of submissions never reach external review. Editorial screening is fast and consequential.

**Documented desk-rejection / editorial-rejection reports:**

| Evidence | What it indicates |
|---|---|
| "I submitted a traditional SLAM paper, but it was rejected on the **third day** without any reasons given. They asked me to resubmit it to a **deep learning journal with an impact factor of 7**." (LetPub, 2026-06-12) — https://www.letpub.com/journal-selector/journal/5437 | **Classical/geometry-only CV work with no learning framing is out of scope.** Non-DL, engineering-flavoured papers are screened out fast. |
| "After careful evaluation, I have determined that there are **other journals that may be a better fit** for your work." (LetPub, 2026-06-26; another rejection in **under one day**, 2026-06-23) — same URL | Standard **scope-mismatch** boilerplate; sub-24h turnaround is pure editorial triage. |
| "2025.9.20 STJ → 2025.10.19 **Desk Reject**" (LetPub, user "yr") — same URL | Desk rejection can also take ~1 month. |
| "投稿过去，with editor 3周后**没有送外审，直接拒掉**" (with editor 3 weeks, rejected without external review) — https://mob.muchong.com/bbs/journal.php/journal.php?view=detail&jid=5464 | Same pattern, older data point. |
| Editor-in-Chief rejected **after** a good first round and revision, stating the journal "**did not have the energy to review so many articles** and the **innovation points were not enough**" (Peeref) — https://www.peeref.com/zh/journals/5437/journal-of-visual-communication-and-image-representation | **Insufficient novelty** is an explicit, stated rejection ground, and can be applied even late in the process. |
| Chinese venue guides describe JVCIR as a "CCF C 保底期刊，创新要求不高" ("fallback CCF-C journal, novelty bar not high") — https://mp.weixin.qq.com/s?__biz=MzY5MTA0Mjk1Ng==&mid=2247484584&idx=1&sn=d91ea4f7ff2f6b7d4293b9e31cf7d9e9 (article body itself was paywalled/blocked on fetch; claim comes from the search snippet) | **Conflicting** author folklore: low novelty bar. Contradicted by the "innovation points were not enough" rejection above and by the 15-day triage. Treat as unreliable folklore, not policy. |

**Synthesis — what gets desk-rejected at JVCIR (evidence-graded):**
1. **Scope mismatch** — work not recognisably about visual communication / image representation (e.g. generic ML, pure robotics, non-visual signal processing). *Well evidenced* (boilerplate rejection text).
2. **No deep-learning / representation-learning framing** — traditional geometry or hand-crafted pipelines. *Evidenced by one detailed report; the reviewer-told-to-go-elsewhere case.*
3. **Insufficient novelty / incremental module-stacking.** *Evidenced by the EiC statement.*
4. **Too engineering / too applied**, lacking theoretical or methodological contribution — plausible from the aims & scope wording ("emphasis on novel technologies **and theoretical work**") but *unverified* as an explicit desk-reject trigger.
5. **Insufficient experiments** — no direct JVCIR evidence found; **unverified**. (A Baidu guide asserts reviewers expect ≥3 mainstream datasets plus complexity analysis; that is third-party advice, not policy — https://developer.baidu.com/article/detail.html?id=3663719.)

---

## 7. Special issues / calls for papers open as of 2026-11-18

**Bottom line: no CFP relevant to 3D vision, Gaussian splatting, compression or quality assessment is currently open.** The journal's own special-issues page lists exactly **one** active Call for Papers, and its window has closed.

| Special issue | Status | Dates | Relevance |
|---|---|---|---|
| **Intelligent and Generative Multimedia Computing — Outstanding Papers of ChinaMM2026** (GEs: Dan Guo, Yifan Jiao, Wu Liu, Jiaying Liu, Hua Huang) | **Closed**; also **"Guest Editor Invitation Only"** | Open **30 May 2026 → deadline 30 Sep 2026**; article type code "VSI: China MM 2026" | Multimedia generation/AIGC, multimodal, "Multimedia Spatial Computing", "Multimedia Data Compression, Coding, and Representation", "Evaluation Benchmarks". Partly adjacent to 3DGS/compression/QA but closed and invitation-only. |
| **Generative Media Processing, Computing, and Evaluation** (GEs: Kejun Wu, Lijuan Wang, You Yang, Xinchao Wang, Gang Yu, Junsong Yuan) | Closed | Open 26 Jul 2024; **deadline 1 Mar 2025**; acceptance 1 Jul 2025 | **Explicitly listed "Gaussian Splatting"** and "compression", "Novel model evaluation, benchmarking" in scope. The single most on-topic JVCIR SI in recent years — now closed. |
| **Multimodal Learning for Visual Intelligence: From Emerging Techniques to Real-World Applications** (GEs: Guanghui Yue, Weide Liu, Ziyang Wang, Hadi Amirpour, Zhedong Zheng, Wei Zhou) | Closed | Open 30 May 2025; **deadline 30 Nov 2025**; acceptance 30 May 2026 | Includes "Generation and reconstruction techniques"; not 3DGS-specific. |
| Long-Term Action Understanding; Multi-media Communication… ChinaMM2025 | Closed (last updates Dec 2025 / Mar 2026) | — | Not relevant. |

Sources: https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/special-issues · https://www.sciencedirect.com/special-issue/332977/intelligent-and-generative-multimedia-computing-outstanding-papers-of-chinamm2026 · https://www.sciencedirect.com/special-issue/1043WK27ZD6 · https://athena.itec.aau.at/2025/05/jvcir-special-issue/

No 2027 CFP was found on the journal site, on guest-editor lab pages, or via search. **Unverified** whether a 2027 3DGS/compression/QA special issue is in preparation — announcements typically appear on the journal's special-issues page first.

---

## Actionable consequences for an author preparing a JVCIR submission

1. **Position the paper as visual-signal/representation research, not general ML.** Name the fit explicitly in the abstract and introduction using the journal's own vocabulary — "RGB-D and 3D processing", "visual data reduction and compression", "deep learning for visual signal processing". The documented desk rejections are scope-mismatch boilerplate and a sub-24-hour triage.
2. **Make novelty legible on page 1.** The EiC has rejected a revised paper for "innovation points not enough". State the mechanism (not the module) and quantify the gain over the strongest baseline in the abstract — the median first decision is 15 days, so nothing later in the manuscript will rescue a weak first impression.
3. **Do not submit a classical/hand-crafted pipeline without a learning framing** — one author was told on day 3 to send a traditional SLAM paper to a deep-learning journal instead.
4. **Prepare the mandatory four now:** highlights (3–5 bullets, **≤85 characters each including spaces**, separate `highlights` file), abstract **≤250 words**, **1–7** keywords, and the CRediT statement. These are hard gates, not preferences.
5. **Treat data/code deposition as compulsory.** JVCIR applies Elsevier **Option C**: deposit in a repository (Mendeley Data or Zenodo), supply the DOI at submission, and if you cannot share, write an explicit statement of why — it will be printed. "Code available on request" is not compliant.
6. **Assemble the declarations bundle before starting the submission:** competing-interests `.docx` from the Elsevier tool, funding statement (fixed wording if unfunded), and a GenAI declaration section placed before the references if any AI tool was used.
7. **Format for the formal checks, not for taste:** `elsarticle` LaTeX (or single-column Word; PDF is not an acceptable source), figures as separate files at 300 dpi photos / 1000 dpi line art (1063 px single-column, 2244 px full-page), numbered references in order of appearance with LTWA abbreviations — any consistent reference style is accepted at submission and restyled at proof.
8. **Plan a 3–7 month timeline and skip the special-issue route.** Median submission-to-acceptance is 215 days, smooth two-revision cases run ~3 months, and the tail reaches 9–14 months. No 3DGS/compression/QA special issue is open (the only live CFP, ChinaMM2026, closed 30 Sep 2026 and was invitation-only), so submit as a regular paper; single-anonymized review means **keep author names in the manuscript**.
