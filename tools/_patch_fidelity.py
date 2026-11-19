"""Make the LPIPS backbone fetch conditional on FIDELITY (M7 runs without it)."""
import io
import os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "run_m1.sh")
s = io.open(p, encoding="utf-8").read()

OLD1 = """    say "lpips backbone (D2 needs it; --fidelity degrades to None rather than hanging)"
    $PY - <<'PY'
"""
NEW1 = """    say "lpips backbone (D2 needs it; --fidelity degrades to None rather than hanging)"
    if [ "${FIDELITY:-1}" = "0" ]; then
      # M7 runs without perceptual metrics: this host pulls the backbone at ~10 kB/s.
      echo "FIDELITY=0 -> skipping the LPIPS backbone"
    else
    $PY - <<'PY'
"""

OLD2 = """    sd = torch.hub.load_state_dict_from_url(url, model_dir=d, progress=False)
    print("fetched", fn, "tensors", len(sd))
PY
"""
NEW2 = """    sd = torch.hub.load_state_dict_from_url(url, model_dir=d, progress=False)
    print("fetched", fn, "tensors", len(sd))
PY
    fi
"""

if "FIDELITY=0 -> skipping" in s:
    print("already patched")
else:
    assert OLD1 in s and OLD2 in s
    s = s.replace(OLD1, NEW1, 1).replace(OLD2, NEW2, 1)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("patched")
