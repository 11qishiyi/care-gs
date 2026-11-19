"""Build the anonymised supplementary material for the TMLR submission.

Layout inside the zip (mirrors the repository's relative paths, so the checker runs
unchanged once `--root` points at the unzipped directory):

    paper/main.tex, paper/fig_*.pdf, paper/tmlr.sty, paper/math_commands.tex
    check/verify_tex_v3.py
    results_v70/*.json                 <- the campaign the paper reports
    research/results_vNN/*.json        <- earlier campaign, used by the appendix
    calib/*.py, scripts/*.py           <- operators and experiment drivers
    experiments/*.py                   <- the revision pipeline (GPU + CPU analyses)
    tools/*.py                         <- figure and table builders
    tests/*.py
    README.md

    python tools/make_supplement.py
"""
from __future__ import annotations

import io
import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTZIP = os.path.join(ROOT, "submission", "supplement.zip")
FINAL = os.path.join(ROOT, "submission", "final")

CALIB = ["__init__.py", "gsrender.py", "plyio.py", "colmap_io.py", "archive_only.py",
         "conformal.py", "sensitivity.py", "downstream_task.py", "voxel_cert.py",
         "weighted.py"]
SCRIPTS = ["many_splits.py", "certificate_audit.py", "edit_families.py", "voxel_and_task.py",
           "three_way.py", "criteria_stats.py", "selfcheck_stats.py", "make_compact.py",
           "make_figures.py", "verify_paper_numbers.py"]
EXPERIMENTS = ["common.py", "node_run.py", "second_task2.py", "third_task.py",
               "merge_variant.py", "make_pup_variant.py", "task_sweep.py",
               "region_coverage.py", "build_archive.py", "fetch_hf_data.py",
               "stage9_eval.py", "stage10_learned.py"]
TOOLS = ["verify_tex_v3.py", "extend_tables.py", "task_intervals.py", "baseline_table.py", "make_figs_v5.py", "make_fig_ext.py", "make_fig3.py", "make_fig3_v90.py", "make_fig_dose.py",
         "make_tables_v70.py", "make_tables_v80.py", "make_tables_v90.py", "make_tables_v100.py",
         "make_provenance.py", "make_figs_v2.py"]
TESTS = ["test_operators.py", "test_advise.py", "test_downstream_task.py", "test_voxel_cert.py",
         "test_new_tools.py"]

# results directories the verifier actually reads
RESEARCH_DIRS = ["results_v17", "results_v22", "results_v24", "results_v28", "results_v35",
                 "results_v51", "results_v52", "results_v53", "results_v54", "results_v55",
                 "results_v58", "results_v60", "results_v61", "results_v62"]

ABS_PATTERNS = [
    (re.compile(r'r"D:\\3dsg_1"'), 'os.path.dirname(os.path.dirname(os.path.abspath(__file__)))'),
    (re.compile(r'"D:\\\\3dsg_1"'), '"."'),
    (re.compile(r"D:/3dsg_1"), "."),
    (re.compile(r"/workspace/[A-Za-z0-9_]+"), "/workspace/data"),
    (re.compile(r"C:\\\\Users\\\\[^\"']+"), "~"),
]


def clean(src: str) -> str:
    s = io.open(src, encoding="utf-8", errors="replace").read()
    for pat, rep in ABS_PATTERNS:
        s = pat.sub(rep, s)
    return s


def add(zf, arc, src):
    zf.writestr(arc, clean(src).encode("utf-8"))


README = """Anonymised supplementary material
==================================

Layout
------
paper/               the submitted LaTeX source (`main.tex`) and the two figure PDFs
check/               `verify_tex_v3.py` -- verifies every reported number against results/
results_v70/         per-scene artifacts of the first campaign: five ground-truth
                     conventions x 400 splits (`diag_<scene>.json`), dose-response, pixel and
                     block coverage, the threshold sweep (`battery_<scene>.json`), and the
                     registration task (`second_task.json`)
results_v80/         stage-8 artifacts: Fisher-sensitivity and merge variants, the per-scene
                     battery with those variants, and the two-view pose task
results_v90/         stage-9 artifacts, the second measurement round: `stage9/<scene>.json`
                     (opacity / Fisher / opacity-times-volume criteria, per-view residual
                     diagnostics, reduced task sweep), the registration and pose tasks on the
                     two scenes that did not have them, `derived/tables.json` (every entry of
                     Tables 3 and 6, with the paired registration bootstrap), and
                     `PROVENANCE.json` (node, image, timings, reproduction check)
results_v100/        stage-10 artifacts: `stage10/<scene>.json` (LoFTR learned matcher and the
                     hand-built patch task on identical renders) and `derived/learned.json`
                     (every number of Appendix E)
research/results_v*/ earlier campaign, used by the appendix tables
calib/ scripts/      operators (PLY IO, gsplat wrapper, conformal quantile, tasks, voxel
                     certificate) and the experiment drivers
experiments/         the revision pipeline: render + dump on a GPU node, then CPU analyses
tools/               figure and table builders (matplotlib, numpy only)
tests/               unit tests for the operators and the decision modules

Where the assets come from
--------------------------
`results_v70/PROVENANCE.json` records the archive the reported numbers were measured on (the criterion, merge and third-task results in `results_v80/` come from the same archive,
rendered in a second session): a 3DGS
output archive of 40k-iteration checkpoints with held-out ground truth (ModelScope dataset
`Jackie137/3dgs-Output`, `output-3dgs.tar.gz`, 9,587,304,864 bytes), the renderer and versions
used, the split protocol, and the per-scene primitive counts, render resolutions and view
counts. Several public mirrors host 3DGS checkpoints trained to different lengths; fetching
from a different mirror will give differently trained assets and will not reproduce these
numbers. `experiments/fetch_hf_data.py` fetches from one such mirror (Hugging Face
`dylanebert/3dgs`, 30k checkpoints) and is useful for a fresh run on new scenes, but it is not
the source of the tables. `results_v90/PROVENANCE.json` records the node the second round ran
on and the four-for-four check that its opacity-30% numbers reproduce `results_v70`.

Reproduce the numbers
---------------------
    python check/verify_tex_v3.py --root . --tex paper/main.tex

437 assertions, exit code 0 iff every reported value matches the stored artifacts.

Rebuild the paper
-----------------
    cd paper && SOURCE_DATE_EPOCH=1700000000 pdflatex main.tex && pdflatex main.tex

On Windows PowerShell: `$env:SOURCE_DATE_EPOCH="1700000000"` before the two runs.

`paper/` is self-contained (`tmlr.sty`, `math_commands.tex`, both figure PDFs, no external
data), so this reproduces the submitted PDF byte for byte: 15 pages, 376,479 bytes. Without
`SOURCE_DATE_EPOCH` the build is identical except for the embedded creation timestamp.

Rebuild the figures
-------------------
    python tools/make_fig3_v90.py      # -> figures_v2/fig_three.pdf (Figure 2, four scenes)
    python tools/make_tables_v90.py    # -> results_v90/derived/tables.json (Tables 3 and 6)
    python tools/make_tables_v100.py   # -> results_v100/derived/learned.json (Appendix E)
    python tools/make_fig3.py          # -> figures_v2/fig_three.pdf (two-scene version, superseded)
    python tools/make_fig_dose.py      # -> figures_v3/fig_dose.pdf

Re-run the measurement from a raw archive
-----------------------------------------
The archive layout the loaders expect is

    <archive>/output/<scene>/cameras.json
    <archive>/output/<scene>/point_cloud/iteration_40000/point_cloud.ply
    <archive>/output/<scene>/test/ours_40000/gt/{j:05d}.png

with cameras sorted by image name and every eighth view held out. On a GPU node with
`gsplat` installed:

    python experiments/node_run.py diag    --archive <archive> --out res/diag.json
    python experiments/node_run.py battery --archive <archive> --out res/battery
    python experiments/second_task2.py     --archive <archive> --scenes bicycle,flowers \\
                                           --out res/second_task.json

Machine-specific paths, usernames and repository names have been stripped. The
`/workspace/...` prefixes that remain are the documented layout of a rented GPU node, not a
local path. The unit tests import `torch` for two of their four modules; without a GPU they
skip rather than fail.
"""


def main():
    n = 0
    with zipfile.ZipFile(OUTZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        # paper
        for f in ("main.tex", "fig_three.pdf", "fig_dose.pdf", "fig_ext.pdf", "tmlr.sty", "math_commands.tex"):
            p = os.path.join(FINAL, f)
            if os.path.isfile(p):
                if f.endswith(".tex") or f.endswith(".sty"):
                    add(zf, f"paper/{f}", p)
                else:
                    zf.write(p, f"paper/{f}")
                n += 1
        # checker
        p = os.path.join(ROOT, "tools", "verify_tex_v3.py")
        if os.path.isfile(p):
            add(zf, "check/verify_tex_v3.py", p)
            n += 1
        # the campaigns reported in the paper
        for _dir in ("results_v70", "results_v80", "results_v90", "results_v100", "results_v110"):
            _root = os.path.join(ROOT, _dir)
            if not os.path.isdir(_root):
                continue
            for _dp, _dn, _fn in os.walk(_root):
                for f in sorted(_fn):
                    if not f.endswith(".json"):
                        continue
                    _full = os.path.join(_dp, f)
                    _rel = os.path.relpath(_full, _root).replace(os.sep, "/")
                    add(zf, f"{_dir}/{_rel}", _full)
                    n += 1
        # earlier campaign
        for d in RESEARCH_DIRS:
            src = os.path.join(ROOT, "research", d)
            if not os.path.isdir(src):
                continue
            for f in sorted(os.listdir(src)):
                fp = os.path.join(src, f)
                if os.path.isfile(fp) and f.endswith(".json") and os.path.getsize(fp) > 2:
                    add(zf, f"research/{d}/{f}", fp)
                    n += 1
        # code
        for f in CALIB:
            p = os.path.join(ROOT, "research", "code", "calib", f)
            if os.path.isfile(p):
                add(zf, f"calib/{f}", p)
                n += 1
        for f in SCRIPTS:
            p = os.path.join(ROOT, "research", "code", "scripts", f)
            if os.path.isfile(p):
                add(zf, f"scripts/{f}", p)
                n += 1
        for f in EXPERIMENTS:
            p = os.path.join(ROOT, "experiments", f)
            if os.path.isfile(p):
                add(zf, f"experiments/{f}", p)
                n += 1
        for f in TESTS:
            for base in (os.path.join(ROOT, "research", "code", "tests"),
                         os.path.join(ROOT, "experiments", "tests")):
                p = os.path.join(base, f)
                if os.path.isfile(p):
                    add(zf, f"tests/{f}", p)
                    n += 1
                    break
        for f in TOOLS[1:]:
            p = os.path.join(ROOT, "tools", f)
            if os.path.isfile(p):
                add(zf, f"tools/{f}", p)
                n += 1
        for f in ("run_all.sh", "README.md"):
            p = os.path.join(ROOT, "repro", f)
            if os.path.isfile(p):
                add(zf, f"repro/{f}", p)
                n += 1
        for f in ("QA_REPORT.md",):
            p = os.path.join(ROOT, "figures_v5", f)
            if os.path.isfile(p):
                add(zf, f"figures_v5/{f}", p)
                n += 1
        zf.writestr("README.md", README)

    print(f"wrote {OUTZIP}  ({n} files, {os.path.getsize(OUTZIP)/1e6:.2f} MB)")
    with zipfile.ZipFile(OUTZIP) as zf:
        bad = []
        for name in zf.namelist():
            txt = zf.read(name).decode("utf-8", "replace")
            # our own identifiers only: dataset namespaces such as Jackie137 or dylanebert
            # belong to third parties and are required for reproducibility
            for tok in ("D:\\3dsg_1", "\\71736", "C:\\Users", "\\Users\\7", "AppData"):
                if tok in txt:
                    bad.append((name, tok))
        print("leak check:", "clean" if not bad else bad[:5])
        print("file count:", len(zf.namelist()))


if __name__ == "__main__":
    main()
