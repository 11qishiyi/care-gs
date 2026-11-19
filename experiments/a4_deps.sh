#!/usr/bin/env bash
set -euo pipefail
PY=${PY:-python3}
"$PY" -m pip install --quiet --no-input --no-deps gsplat==1.5.3 rich jaxtyping ninja
"$PY" - <<'PY'
import importlib.util
for m in ("gsplat", "rich", "jaxtyping", "ninja", "plyfile", "zstandard"):
    print(m, bool(importlib.util.find_spec(m)))
import gsplat
print("gsplat version", getattr(gsplat, "__version__", "?"))
PY
