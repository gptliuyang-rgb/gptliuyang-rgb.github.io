"""Failure mining helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FAILURE_CATEGORIES = [
    "perception",
    "approach",
    "grasp",
    "slip",
    "trigger",
    "aiming",
    "decode",
    "collision",
    "latency",
    "hardware_fault",
    "sim_real_mismatch",
    "unknown",
]


@dataclass
class FailureClip:
    episode_id: str
    timestamp_ns: int
    task_phase: str
    category: str
    notes: str = ""
    context: dict[str, Any] = field(default_factory=dict)


def classify_failure(phase: str, decode_ok: bool | None = None, slipped: bool = False) -> str:
    if slipped:
        return "slip"
    if phase in {"GRASP", "VERIFY_GRASP"}:
        return "grasp"
    if phase == "TRIGGER":
        return "trigger"
    if phase in {"AIM", "LOCATE_QR"} and decode_ok is False:
        return "decode"
    if phase == "APPROACH":
        return "approach"
    return "unknown"
