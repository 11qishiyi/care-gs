"""A4 node-side environment report (read-only, no GPU work beyond one tensor).

    python experiments/a4_envcheck.py --archive /workspace/data/out3dgs

Prints a single block of facts the A4 runbook depends on, so that a mismatch is
visible *before* a 40--70 minute dump burns node time. Deliberately written as a
file instead of `python -c` one-liners: the command crosses PowerShell ->
`matcli node exec` -> `bash -c`, and nested quoting there is a reliable way to
lose an hour.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import shutil
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill")
    ap.add_argument("--probe-gpu", action="store_true",
                    help="run one 4-splat projection + rasterization to prove the API shape")
    args = ap.parse_args(argv)

    print("== python ==")
    print("executable", sys.executable)
    print("version", sys.version.split()[0])

    print("== modules ==")
    for name in ("numpy", "torch", "gsplat", "plyfile", "PIL"):
        try:
            m = importlib.import_module(name)
            print(f"{name:9s} OK      {getattr(m, '__version__', '?')}")
        except Exception as exc:                              # noqa: BLE001
            print(f"{name:9s} MISSING {type(exc).__name__}: {exc}")

    try:
        import torch
        print("== torch ==")
        print("version", torch.__version__, "cuda", torch.version.cuda,
              "available", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("device", torch.cuda.get_device_name(0),
                  "mem_GB", round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1))
    except Exception as exc:                                  # noqa: BLE001
        print("torch probe failed:", exc)

    try:
        import gsplat
        sig = inspect.signature(gsplat.fully_fused_projection)
        print("== gsplat ==")
        print("fully_fused_projection", sig)
        # the A4 allocator relies on the unpacked (radii, means2d, depths, conics, comp)
        # return with packed=False; if this attribute is missing the round cannot run
        print("has rasterization", hasattr(gsplat, "rasterization"))
        print("has load_ply_to_splats", hasattr(gsplat, "load_ply_to_splats"))
        if args.probe_gpu:
            print("== gsplat probe (4 synthetic splats, 16x16) ==")
            import torch
            n, deg = 4, 3
            k = (deg + 1) ** 2
            g = torch.Generator().manual_seed(0)
            means = torch.randn(n, 3, generator=g) * 0.1
            quats = torch.nn.functional.normalize(torch.randn(n, 4, generator=g), dim=-1)
            scales = torch.full((n, 3), 0.05)
            opac = torch.full((n,), 0.7)
            sh = torch.randn(n, k, 3, generator=g) * 0.1
            vm = torch.eye(4)[None].repeat(1, 1, 1)
            vm[0, 2, 3] = 3.0                                   # pull the camera back
            K = torch.tensor([[20.0, 0, 8.0], [0, 20.0, 8.0], [0, 0, 1.0]])[None]
            vm, K = vm.cuda(), K.cuda()
            radii, m2, dep, conics, comp = gsplat.fully_fused_projection(
                means=means.cuda(), covars=None, quats=quats.cuda(),
                scales=scales.cuda(), viewmats=vm, Ks=K, width=16, height=16,
                near_plane=0.01, packed=False)
            print("projection shapes", tuple(radii.shape), tuple(m2.shape), tuple(dep.shape),
                  "-> 5-tuple OK")
            cols, alps, info = gsplat.rasterization(
                means=means.cuda(), quats=quats.cuda(), scales=scales.cuda(),
                opacities=opac.cuda(), colors=sh.cuda(), viewmats=vm, Ks=K,
                width=16, height=16, near_plane=0.01, far_plane=1e10,
                sh_degree=deg, packed=False, render_mode="RGB")
            print("rasterization ->", tuple(cols.shape), tuple(alps.shape),
                  "finite", bool(torch.isfinite(cols).all()))
    except Exception as exc:                                  # noqa: BLE001
        print("gsplat probe failed:", type(exc).__name__, exc)

    print("== disk ==")
    for p in ("/", "/workspace", "/mnt"):
        if os.path.isdir(p):
            u = shutil.disk_usage(p)
            print(f"{p:11s} total {u.total / 2**30:7.1f} GiB free {u.free / 2**30:7.1f} GiB")

    print("== archive ==")
    arch = args.archive
    tar = os.path.join(os.path.dirname(arch.rstrip("/")), "output-3dgs.tar.gz")
    print("tar.gz", tar, "exists" if os.path.isfile(tar) else "absent",
          f"{os.path.getsize(tar) / 2**30:.2f} GiB" if os.path.isfile(tar) else "")
    for sc in args.scenes.split(","):
        ply = os.path.join(arch, "output", sc, "point_cloud", "iteration_40000", "point_cloud.ply")
        ok = os.path.isfile(ply)
        print(f"  {sc:9s} ply {'OK' if ok else 'MISSING'}",
              f"{os.path.getsize(ply) / 2**30:.2f} GiB" if ok else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
