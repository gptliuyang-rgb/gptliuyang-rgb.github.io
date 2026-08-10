"""Deterministic mock backend for CI without hardware/sim GPU."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from wuji_r2s2r.schema.joint_mapping import JointMapping
from wuji_r2s2r.schema.types import DOF, HandAction, HandObservation
from wuji_r2s2r.sim.common.backend import HandBackend


class MockHand2Backend(HandBackend):
    name = "mock"

    def __init__(self, side: str = "right", dt: float = 0.002, kp: float = 20.0):
        self.side = side
        self.dt = dt
        self.kp = kp
        self.mapping = JointMapping()
        self.q = np.zeros(DOF)
        self.dq = np.zeros(DOF)
        self.effort = np.zeros(DOF)
        self.target = np.zeros(DOF)
        self._t0 = time.time_ns()
        self._steps = 0

    def reset(self, qpos=None, **kwargs) -> HandObservation:
        self.q = np.zeros(DOF) if qpos is None else np.asarray(qpos, dtype=np.float64)
        self.dq[:] = 0
        self.effort[:] = 0
        self.target = self.q.copy()
        self._steps = 0
        return self.observe()

    def observe(self) -> HandObservation:
        return HandObservation(
            timestamp_ns=self._t0 + int(self._steps * self.dt * 1e9),
            joint_position=self.q.copy(),
            joint_velocity=self.dq.copy(),
            effort=self.effort.copy(),
            diagnostics={"backend": self.name, "steps": self._steps},
        )

    def command(self, action: HandAction) -> None:
        self.target = action.position_target.copy()

    def step(self, n: int = 1) -> HandObservation:
        for _ in range(n):
            err = self.target - self.q
            self.effort = self.kp * err
            self.dq = err / max(self.dt, 1e-6) * 0.1
            self.q = self.q + self.dq * self.dt
            self._steps += 1
        return self.observe()

    def diagnostics(self) -> dict[str, Any]:
        return {"backend": self.name, "side": self.side, "steps": self._steps}

    def close(self) -> None:
        return None
