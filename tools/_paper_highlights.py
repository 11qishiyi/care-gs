# -*- coding: utf-8 -*-
import io, os

P = r"D:\3dsg_1\submission\cviu\highlights.txt"
lines = [
    "Coverage loss after pruning is measured on nine 3DGS assets and dose-response mapped.",
    "A label-free audit recovers post-edit coverage from the views the certificate ships.",
    "A Kolmogorov envelope bounds the loss an edit can cause; issuers can pre-compute it.",
    "At equal bytes geometry costs 0.04-1.17 coverage points; 8-bit SH costs nothing.",
    "The certified number tracks none of four downstream tasks, which differ by 4-11x.",
]
bad = [(i + 1, len(l)) for i, l in enumerate(lines) if len(l) > 85]
if bad:
    raise SystemExit("over 85 chars: %r" % bad)
io.open(P, "w", encoding="utf-8", newline="\r\n").write("\n".join(lines) + "\n")
print("wrote", os.path.basename(P), "max len", max(len(l) for l in lines))
