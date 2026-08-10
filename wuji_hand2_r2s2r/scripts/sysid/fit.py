#!/usr/bin/env python3
"""Run hierarchical sysID fitting on free-space data."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.recording.episode_io import load_episode
from wuji_r2s2r.sysid.fit import fit_delay_grid
from wuji_r2s2r.sysid.registry import ParameterRegistry

def main():
    train_dir = ROOT / "data" / "simulation" / "R1_SYSTEM_ID" / "SYSID_TRAIN"
    episodes = sorted(train_dir.glob("*/timeseries.npz"))
    if not episodes:
        print("No train episodes; run scripts/sim/evaluate_twin.py first")
        sys.exit(1)
    ep = load_episode(episodes[0].parent)
    fit = fit_delay_grid(ep["q"], ep["actions"], backend="mock")
    reg = ParameterRegistry()
    table = reg.uncertainty_table()
    out = {
        "fit": fit,
        "uncertainty_before": table,
        "digital_twin_version": reg.version,
        "evidence": "[Simulation verified] delay grid on synthetic free-space; physical sysID pending",
    }
    path = ROOT / "reports" / "sysid_fit_v0.1.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["fit"]["best"], indent=2))
    print("Wrote", path)

if __name__ == "__main__":
    main()
