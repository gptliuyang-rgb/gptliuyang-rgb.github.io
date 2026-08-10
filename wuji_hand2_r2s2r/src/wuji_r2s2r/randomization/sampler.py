"""Sample domain randomization from ID-derived ranges."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[3]


class DRSampler:
    def __init__(self, config_path: str | Path | None = None, seed: int = 0):
        path = Path(config_path) if config_path else REPO / "configs" / "randomization" / "dr_v0.1.yaml"
        with open(path) as f:
            self.cfg = yaml.safe_load(f)
        self.rng = np.random.default_rng(seed)
        self.version = self.cfg["version"]

    def sample(self, stress: bool = False) -> dict[str, float]:
        ranges = self.cfg["stress_test_ranges"] if stress else self.cfg["ranges"]
        out: dict[str, float] = {"randomization_version": self.version, "stress": stress}
        for k, v in ranges.items():
            if k == "note" or not isinstance(v, (list, tuple)) or len(v) != 2:
                continue
            lo, hi = float(v[0]), float(v[1])
            out[k] = float(self.rng.uniform(lo, hi))
        return out
