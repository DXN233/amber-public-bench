#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OPTIONAL task-bank builder for maintainers.

Third parties should NOT run this. Ship uses prebuilt tasks/contexts under
data/ or reference/fair_r2/. Rebuilding needs private sandboxes that are NOT
in this repo.

Refuse by default. Only:
  FORCE_REBUILD=1 python3 scripts/build_tasks.py --out data/myset
"""
from __future__ import annotations
import os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def _refuse_unless_forced():
    if os.environ.get("FORCE_REBUILD") == "1":
        return
    print(
        "REFUSED: build_tasks.py rebuilds task banks from private sandboxes.\n"
        "This public repo ships prebuilt fixtures under reference/fair_r2/ and\n"
        "data/sample_minimal/. To use your own data, copy the sample layout\n"
        "(see data/README.md) — do not run build_tasks.\n"
        "Maintainers only: FORCE_REBUILD=1 python3 scripts/build_tasks.py --out DIR",
        file=sys.stderr,
    )
    sys.exit(3)

_refuse_unless_forced()


import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--out", default=None, help="Output data dir (sets AMBER_BUILD_OUT)")
args, rest = ap.parse_known_args()
if args.out:
    os.environ["AMBER_BUILD_OUT"] = str(Path(args.out).resolve())
# re-exec impl in-process
import runpy
sys.argv = [str(REPO / "scripts" / "_build_tasks_impl.py")] + rest
runpy.run_path(str(REPO / "scripts" / "_build_tasks_impl.py"), run_name="__main__")
