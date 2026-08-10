"""Load and validate canonical joint mapping."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DOF = 20
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MAPPING = REPO_ROOT / "configs" / "hardware" / "joint_mapping.yaml"


@dataclass(frozen=True)
class JointSpec:
    index: int
    name: str
    finger: int
    finger_name: str
    joint_in_finger: int
    sdk_finger: int
    sdk_joint: int
    mjcf_right: str
    mjcf_left: str
    actuator_right: str
    actuator_left: str
    axis: tuple[float, float, float]
    limit_lower: float
    limit_upper: float
    effort_limit: float


class JointMapping:
    def __init__(self, path: Path | str | None = None):
        path = Path(path) if path else DEFAULT_MAPPING
        with open(path) as f:
            raw: dict[str, Any] = yaml.safe_load(f)
        self.raw = raw
        self.joints = [JointSpec(**{**j, "axis": tuple(j["axis"])}) for j in raw["canonical_joints"]]
        if len(self.joints) != DOF:
            raise ValueError(f"Expected {DOF} joints, got {len(self.joints)}")
        for i, j in enumerate(self.joints):
            if j.index != i:
                raise ValueError(f"Joint index mismatch at {i}: {j.index}")
        self.by_name = {j.name: j for j in self.joints}

    @property
    def names(self) -> list[str]:
        return [j.name for j in self.joints]

    def mjcf_names(self, side: str = "right") -> list[str]:
        key = "mjcf_right" if side == "right" else "mjcf_left"
        return [getattr(j, key) for j in self.joints]

    def actuator_names(self, side: str = "right") -> list[str]:
        key = "actuator_right" if side == "right" else "actuator_left"
        return [getattr(j, key) for j in self.joints]

    def limit_lower(self) -> list[float]:
        return [j.limit_lower for j in self.joints]

    def limit_upper(self) -> list[float]:
        return [j.limit_upper for j in self.joints]

    def effort_limits(self) -> list[float]:
        return [j.effort_limit for j in self.joints]

    def sdk_to_canonical(self, finger: int, joint: int) -> int:
        for j in self.joints:
            if j.sdk_finger == finger and j.sdk_joint == joint:
                return j.index
        raise KeyError(f"No mapping for finger={finger} joint={joint}")

    def validate_against_mjcf_joint_names(self, mjcf_joint_names: list[str], side: str = "right") -> None:
        expected = set(self.mjcf_names(side))
        found = set(mjcf_joint_names)
        missing = expected - found
        extra = found - expected
        if missing or extra:
            raise AssertionError(f"MJCF joint mismatch missing={missing} extra={extra}")
