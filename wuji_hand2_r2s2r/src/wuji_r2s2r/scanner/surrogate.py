"""Configurable scanner decode success surrogate."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ScanSurrogateConfig:
    distance_min_m: float = 0.05
    distance_max_m: float = 0.35
    max_angular_error_rad: float = 0.35
    require_trigger: bool = True
    require_line_of_sight: bool = True


def scan_success(
    trigger_active: bool,
    target_visible: bool,
    distance_m: float,
    angular_error_rad: float,
    line_of_sight_valid: bool = True,
    cfg: ScanSurrogateConfig | None = None,
    rng: np.random.Generator | None = None,
    success_probability_model: dict | None = None,
) -> bool:
    cfg = cfg or ScanSurrogateConfig()
    if cfg.require_trigger and not trigger_active:
        return False
    if not target_visible:
        return False
    if not (cfg.distance_min_m <= distance_m <= cfg.distance_max_m):
        return False
    if abs(angular_error_rad) > cfg.max_angular_error_rad:
        return False
    if cfg.require_line_of_sight and not line_of_sight_valid:
        return False
    if success_probability_model is not None and rng is not None:
        # Empirical P(success|state) when calibrated from real data
        p = float(success_probability_model.get("p", 1.0))
        return bool(rng.random() < p)
    return True
