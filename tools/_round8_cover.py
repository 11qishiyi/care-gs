import pathlib

C = pathlib.Path("submission/cviu/COVER_LETTER.md")
c = C.read_text(encoding="utf-8")

old = ("**Evidence and material.** Nine assets in three provenance groups (five released\n"
       "checkpoints, four trained here with a leak-free interleaved split), four task families, a\n"
       "threshold sweep over 36 cells per asset, paired view-level bootstrap intervals throughout,")
new = ("**Evidence and material.** Nine assets in three provenance groups --- four released\n"
       "Mip-NeRF 360 checkpoints, two further released assets from a second archive, and three we\n"
       "trained here with a leak-free interleaved split --- four task families, a\n"
       "threshold sweep over 36 cells per asset, paired view-level bootstrap intervals throughout,")
assert old in c, "asset sentence"
c = c.replace(old, new)

# the audit grid is eight scene-checkpoints, not the nine assets: say which is which once
old2 = ("and (iii) the envelope, which makes the claim checkable in both directions.")
new2 = ("and (iii) the envelope, which makes the claim checkable in both directions. The audit itself is\n"
        "measured on eight scene-checkpoints (the four released assets, four short-training twins of the\n"
        "same scenes) because its input is a per-view residual dump; the degradation tables cover all\n"
        "nine assets.")
if old2 in c:
    c = c.replace(old2, new2)
C.write_text(c, encoding="utf-8")
print("cover letter patched")
