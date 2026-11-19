"""Add the two 2026 references that define where this paper sits, plus the sentence that says it."""
import pathlib

B = pathlib.Path("submission/cviu/refs.bib")
b = B.read_text(encoding="utf-8")
if "splatwizard2026" not in b:
    b += r"""
@inproceedings{splatwizard2026,
  author = {Xiang Liu and Yimin Zhou and Jinxiang Wang and Yujun Huang and Shuzhao Xie and
            Shiyu Qin and Mingyao Hong and Jiawei Li and Yaowei Wang and Zhi Wang and
            Shu-Tao Xia and Bin Chen},
  title = {{Splatwizard}: A Benchmark Toolkit for {3D} {Gaussian} Splatting Compression},
  booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern
               Recognition (CVPR), Findings},
  pages = {2261--2271},
  year = {2026}
}

@article{ali2026compression,
  author = {M. S. Ali and C. Zhang and M. Cagnazzo and G. Valenzise and E. Tartaglione and
            S. H. Bae},
  title = {Compression in {3D} {Gaussian} Splatting: A Survey of Methods, Trends, and Future
           Directions},
  journal = {IEEE Transactions on Circuits and Systems for Video Technology},
  volume = {36},
  number = {7},
  pages = {9291--9308},
  year = {2026}
}
"""
B.write_text(b, encoding="utf-8")

M = pathlib.Path("submission/cviu/main.tex")
t = M.read_text(encoding="utf-8")
anchor = ("\\paragraph{Proxy metrics versus downstream tasks.}")
assert anchor in t, "anchor"
add = (
    "\\paragraph{Compression benchmarks, and what they leave out.} The compression side of this\n"
    "literature now has a survey of its methods and trends~\\citep{ali2026compression} and a\n"
    "benchmark toolkit that puts compressors on one protocol~\\citep{splatwizard2026}. Both compare\n"
    "compressors against each other, and both are the right instrument for the question they ask ---\n"
    "which compressor wins at a budget. Neither asks what happens to a guarantee that was attached to\n"
    "one of those compressors before the budget was chosen. A benchmark ranks assets; a certificate\n"
    "commits one asset to a number, and the two can disagree: an asset that places third on a\n"
    "benchmark can be the only one whose shipped guarantee survives the edit. That is the gap this\n"
    "paper occupies, and it is why we compare against a certificate rather than against a leaderboard.\n\n")
t = t.replace(anchor, add + anchor)
M.write_text(t, encoding="utf-8")
print("bib entries:", b.count("@"), "| new cites:", t.count("splatwizard2026"),
      t.count("ali2026compression"))
