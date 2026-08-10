"""Canonical observation/action schemas shared by real and sim backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

DOF = 20


@dataclass
class HandObservation:
    timestamp_ns: int
    joint_position: np.ndarray  # (20,)
    joint_velocity: np.ndarray  # (20,)
    effort: np.ndarray  # (20,)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    fingertip_tactile: Optional[np.ndarray] = None  # None on Beta 1

    def __post_init__(self) -> None:
        self.joint_position = np.asarray(self.joint_position, dtype=np.float64).reshape(DOF)
        self.joint_velocity = np.asarray(self.joint_velocity, dtype=np.float64).reshape(DOF)
        self.effort = np.asarray(self.effort, dtype=np.float64).reshape(DOF)


@dataclass
class HandAction:
    timestamp_ns: int
    position_target: np.ndarray  # (20,)
    velocity_target: Optional[np.ndarray] = None
    effort_ff: Optional[np.ndarray] = None

    def __post_init__(self) -> None:
        self.position_target = np.asarray(self.position_target, dtype=np.float64).reshape(DOF)
        if self.velocity_target is not None:
            self.velocity_target = np.asarray(self.velocity_target, dtype=np.float64).reshape(DOF)
        if self.effort_ff is not None:
            self.effort_ff = np.asarray(self.effort_ff, dtype=np.float64).reshape(DOF)


@dataclass
class EpisodeMetadata:
    episode_id: str
    source: str  # real | mujoco | mjwarp | isaaclab | mock
    task: str
    dataset_purpose: str  # R0..R7
    hardware_version: str = "hand2_beta1"
    firmware_version: str = "unknown"
    simulator_version: str = ""
    simulator_parameters: dict[str, Any] = field(default_factory=dict)
    dataset_version: str = "v0"
    calibration_version: str = "none"
    digital_twin_version: str = "hand2_twin_v0.1"
    randomization_version: str = ""
    git_commit: str = ""
