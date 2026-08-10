"""Real Wuji Hand 2 backend via official SDK (optional dependency)."""

from __future__ import annotations

import time
from typing import Any, Optional

import numpy as np

from wuji_r2s2r.schema.joint_mapping import JointMapping
from wuji_r2s2r.schema.types import DOF, HandAction, HandObservation
from wuji_r2s2r.sim.common.backend import HandBackend


class WujiHand2RealBackend(HandBackend):
    name = "real"

    def __init__(self, side: str = "right", dry_run: bool = True):
        self.side = side
        self.dry_run = dry_run
        self.mapping = JointMapping()
        self._hand = None
        self._sdk = None
        self._connected = False
        self._q = np.zeros(DOF)
        self._dq = np.zeros(DOF)
        self._effort = np.zeros(DOF)
        self._target = np.zeros(DOF)
        self._t0 = time.time_ns()
        if not dry_run:
            self._connect()

    def _connect(self) -> None:
        try:
            import wuji_sdk  # type: ignore
            self._sdk = wuji_sdk
            # Prefer unified Wuji SDK Hand2 handle when present.
            mgr = getattr(wuji_sdk, "SdkManager", None)
            if mgr is not None:
                # Actual connect requires network/hardware; left for on-site use.
                raise RuntimeError("Hardware connect requires live device — use dry_run=True offline")
            raise RuntimeError("wuji_sdk present but connect path not configured")
        except ImportError as exc:
            raise RuntimeError(
                "Official Wuji SDK not installed. Use dry_run=True or Mock/MuJoCo backends."
            ) from exc

    def reset(self, qpos=None, **kwargs) -> HandObservation:
        if qpos is not None:
            self._q = np.asarray(qpos, dtype=np.float64).reshape(DOF)
        self._target = self._q.copy()
        return self.observe()

    def observe(self) -> HandObservation:
        return HandObservation(
            timestamp_ns=time.time_ns(),
            joint_position=self._q.copy(),
            joint_velocity=self._dq.copy(),
            effort=self._effort.copy(),
            diagnostics={
                "backend": self.name,
                "dry_run": self.dry_run,
                "connected": self._connected,
                "tactile_available": False,  # Beta 1
            },
            fingertip_tactile=None,
        )

    def command(self, action: HandAction) -> None:
        self._target = action.position_target.copy()
        if self._connected and self._hand is not None:
            # Placeholder for polymorphic 20-array write on WujiHand2
            pass

    def step(self, n: int = 1) -> HandObservation:
        # In dry-run, emulate tracking toward command.
        if self.dry_run:
            self._q = 0.9 * self._q + 0.1 * self._target
            self._dq = (self._target - self._q) * 10.0
        return self.observe()

    def diagnostics(self) -> dict[str, Any]:
        return {
            "backend": self.name,
            "dry_run": self.dry_run,
            "connected": self._connected,
            "revision": "hand2_beta1",
            "tactile": False,
        }

    def close(self) -> None:
        self._connected = False
        self._hand = None
