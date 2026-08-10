#!/usr/bin/env python3
"""Build DR config from parameter uncertainty."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.sysid.registry import ParameterRegistry
from wuji_r2s2r.randomization.sampler import DRSampler

def main():
    reg = ParameterRegistry()
    sampler = DRSampler(seed=0)
    samples = [sampler.sample() for _ in range(20)]
    coverage = []
    for row in reg.uncertainty_table():
        name = row["parameter"]
        # map names
        key = {
            "actuator_delay_ms": "actuator_delay_ms",
            "scanner_mass": "scanner_mass",
            "scanner_handle_friction": "scanner_handle_friction",
            "finger_friction_sliding": "finger_friction_sliding",
        }[name]
        lo, hi = sampler.cfg["ranges"][key]
        nom = row["nominal"] if not isinstance(row["nominal"], list) else row["nominal"]
        covered = lo <= float(nom) <= hi
        coverage.append({"parameter": name, "real_estimate": nom, "dr_range": [lo, hi], "covered": covered})
    out = {"randomization_version": sampler.version, "coverage": coverage, "example_samples": samples[:3]}
    path = ROOT / "reports" / "dr_coverage.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(coverage, indent=2))

if __name__ == "__main__":
    main()
