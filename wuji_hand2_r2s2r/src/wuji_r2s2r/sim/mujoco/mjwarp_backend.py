"""MuJoCo Warp / MJWarp backend stub with CPU fallback."""

from __future__ import annotations

from typing import Any

from wuji_r2s2r.sim.common.backend import HandBackend
from wuji_r2s2r.sim.mujoco.backend import MuJoCoHand2Backend


class MJWarpHand2Backend(HandBackend):
    name = "mjwarp"

    def __init__(self, **kwargs):
        self._impl = MuJoCoHand2Backend(**kwargs)
        self._available = False
        try:
            import warp  # noqa: F401
            self._available = True
        except Exception:
            self._available = False

    def reset(self, qpos=None, **kwargs):
        return self._impl.reset(qpos=qpos, **kwargs)

    def observe(self):
        return self._impl.observe()

    def command(self, action):
        return self._impl.command(action)

    def step(self, n: int = 1):
        return self._impl.step(n)

    def diagnostics(self) -> dict[str, Any]:
        d = self._impl.diagnostics()
        d["backend"] = self.name
        d["warp_available"] = self._available
        d["note"] = "Warp package optional; CPU MuJoCo used for single-env fidelity"
        return d

    def close(self) -> None:
        self._impl.close()
