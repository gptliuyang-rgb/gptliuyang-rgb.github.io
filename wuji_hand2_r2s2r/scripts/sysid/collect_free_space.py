#!/usr/bin/env python3
"""Collect free-space sysID trajectories (sim now; real when connected)."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
# Reuse twin evaluator synthesizer path by calling evaluate_twin for now
from scripts.sim.evaluate_twin import synthesize  # type: ignore

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="mujoco")
    ap.add_argument("--split", default="SYSID_TRAIN")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    # Import synthesizer logic inline to avoid package script import issues
    import runpy
    print("Generating via evaluate_twin synthesizer entry; prefer scripts/sim/evaluate_twin.py for batch")
    p = synthesize(args.split, args.seed)
    print("Wrote", p)

if __name__ == "__main__":
    # inline to avoid importing scripts as package
    import importlib.util
    spec = importlib.util.spec_from_file_location("evaluate_twin", ROOT / "scripts" / "sim" / "evaluate_twin.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = mod.synthesize("SYSID_TRAIN", 42)
    print("Wrote", p)
