"""Deployment safety gates G0–G10."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


GATES = [
    "G0_sim_smoke",
    "G1_real_action_playback_sim",
    "G2_real_holdout_replay",
    "G3_policy_nominal_mujoco",
    "G4_policy_randomized_mujoco",
    "G5_cross_sim",
    "G6_dry_run_real_obs",
    "G7_shadow",
    "G8_low_risk_real",
    "G9_scanner_subskill",
    "G10_full_factory_poc",
]


@dataclass
class GateStatus:
    results: dict[str, bool] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def set(self, gate: str, ok: bool, note: str = "") -> None:
        if gate not in GATES:
            raise KeyError(gate)
        self.results[gate] = ok
        if note:
            self.notes[gate] = note

    def can_proceed_to(self, gate: str) -> bool:
        idx = GATES.index(gate)
        for g in GATES[:idx]:
            if not self.results.get(g, False):
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {"results": self.results, "notes": self.notes}
