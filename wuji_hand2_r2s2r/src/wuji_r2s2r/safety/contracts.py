"""Observation/action contract validation before deployment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[3]


def load_yaml(rel: str) -> dict[str, Any]:
    with open(REPO / rel) as f:
        return yaml.safe_load(f)


def validate_action(action: np.ndarray, limit_lower: np.ndarray, limit_upper: np.ndarray) -> list[str]:
    issues = []
    a = np.asarray(action, dtype=np.float64)
    if a.shape != (20,):
        issues.append("action_dim")
    if np.isnan(a).any() or np.isinf(a).any():
        issues.append("action_nan_inf")
    if np.any(a < limit_lower - 1e-6) or np.any(a > limit_upper + 1e-6):
        issues.append("action_out_of_range")
    return issues


def validate_observation_keys(keys: set[str]) -> list[str]:
    obs = load_yaml("configs/deployment/observation_contract.yaml")
    issues = []
    for k in obs["required"]:
        if k not in keys:
            issues.append(f"missing:{k}")
    for k in obs["forbidden_privileged"]:
        if k in keys:
            issues.append(f"forbidden:{k}")
    return issues
