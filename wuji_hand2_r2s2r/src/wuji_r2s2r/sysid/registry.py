"""Canonical parameter registry + backend translators."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[3]
DEFAULT = REPO / "configs" / "system_id" / "parameter_registry.yaml"


class ParameterRegistry:
    def __init__(self, path: Path | str | None = None):
        path = Path(path) if path else DEFAULT
        with open(path) as f:
            self.data = yaml.safe_load(f)
        self.path = path

    @property
    def version(self) -> str:
        return str(self.data.get("version", "unknown"))

    def get(self, *keys, default=None):
        cur: Any = self.data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def uncertainty_table(self) -> list[dict[str, Any]]:
        rows = []
        for name, node in [
            ("actuator_delay_ms", self.get("hand", "actuator", "delay_ms")),
            ("scanner_mass", self.get("scanner", "mass")),
            ("scanner_handle_friction", self.get("scanner", "handle_friction")),
            ("finger_friction_sliding", self.get("finger_contact", "friction", "sliding")),
        ]:
            if isinstance(node, dict) and "nominal" in node:
                rows.append({
                    "parameter": name,
                    "nominal": node.get("nominal"),
                    "lower": node.get("lower"),
                    "upper": node.get("upper"),
                    "confidence": node.get("confidence", "unknown"),
                    "source": node.get("source", []),
                })
        return rows

    def to_mujoco_overrides(self) -> dict[str, Any]:
        """Semantic → MuJoCo-oriented overrides (not 1:1 with PhysX)."""
        return {
            "actuator_kp": self.get("hand", "actuator", "kp"),
            "actuator_kd": self.get("hand", "actuator", "kd"),
            "armature": self.get("hand", "dynamics", "armature"),
            "delay_ms": self.get("hand", "actuator", "delay_ms", "nominal"),
            "finger_friction": self.get("finger_contact", "friction", "sliding", "nominal"),
            "scanner_mass": self.get("scanner", "mass", "nominal"),
        }

    def to_isaac_overrides(self) -> dict[str, Any]:
        """Semantic → Isaac/PhysX-oriented overrides (separate conversion)."""
        return {
            "drive_stiffness": self.get("hand", "actuator", "kp"),
            "drive_damping": self.get("hand", "actuator", "kd"),
            "static_friction": self.get("finger_contact", "friction", "sliding", "nominal"),
            "dynamic_friction": self.get("finger_contact", "friction", "sliding", "nominal"),
            "scanner_mass": self.get("scanner", "mass", "nominal"),
            "note": "PhysX contact params are NOT numerically interchangeable with MuJoCo",
        }

    def save(self, path: Path | str | None = None) -> Path:
        path = Path(path) if path else self.path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.safe_dump(self.data, f, sort_keys=False)
        return path

    def clone_with_updates(self, updates: dict[str, Any], new_version: str) -> "ParameterRegistry":
        reg = ParameterRegistry.__new__(ParameterRegistry)
        reg.data = deepcopy(self.data)
        reg.data.update(updates)
        reg.data["version"] = new_version
        reg.path = self.path
        return reg
