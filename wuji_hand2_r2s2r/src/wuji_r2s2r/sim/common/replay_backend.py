"""Replay recorded joint trajectories without physics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from wuji_r2s2r.schema.types import DOF, HandAction, HandObservation
from wuji_r2s2r.sim.common.backend import HandBackend


class ReplayHand2Backend(HandBackend):
    name = "replay"

    def __init__(self, episode_path: str | Path):
        path = Path(episode_path)
        data = np.load(path, allow_pickle=True)
        self.q = np.asarray(data["q"], dtype=np.float64)
        self.dq = np.asarray(data["dq"], dtype=np.float64) if "dq" in data else np.zeros_like(self.q)
        self.effort = np.asarray(data["effort"], dtype=np.float64) if "effort" in data else np.zeros_like(self.q)
        self.ts = np.asarray(data["timestamp_ns"]) if "timestamp_ns" in data else np.arange(len(self.q))
        assert self.q.ndim == 2 and self.q.shape[1] == DOF
        self.idx = 0

    def reset(self, qpos=None, **kwargs) -> HandObservation:
        self.idx = 0
        return self.observe()

    def observe(self) -> HandObservation:
        i = min(self.idx, len(self.q) - 1)
        return HandObservation(
            timestamp_ns=int(self.ts[i]),
            joint_position=self.q[i],
            joint_velocity=self.dq[i],
            effort=self.effort[i],
            diagnostics={"backend": self.name, "frame": i},
        )

    def command(self, action: HandAction) -> None:
        # Open-loop replay ignores commands; retained for interface parity.
        return None

    def step(self, n: int = 1) -> HandObservation:
        self.idx = min(self.idx + n, len(self.q) - 1)
        return self.observe()

    def diagnostics(self) -> dict[str, Any]:
        return {"backend": self.name, "frames": len(self.q), "idx": self.idx}

    def close(self) -> None:
        return None
