"""MJX backend wrapper. Falls back to MuJoCo CPU if JAX/MJX unavailable."""

from __future__ import annotations

from typing import Any

from wuji_r2s2r.sim.common.backend import HandBackend
from wuji_r2s2r.sim.mujoco.backend import MuJoCoHand2Backend


class MJXHand2Backend(HandBackend):
    name = "mjx"

    def __init__(self, **kwargs):
        self._impl: HandBackend
        self._mode = "fallback_cpu"
        try:
            import jax  # noqa: F401
            from mujoco import mjx  # noqa: F401
            # Full MJX parallel env is implemented in batch_env.py; single-env
            # path currently uses CPU MuJoCo for API parity.
            self._impl = MuJoCoHand2Backend(**kwargs)
            self._mode = "mjx_api_parity_cpu"
        except Exception as exc:  # noqa: BLE001
            self._impl = MuJoCoHand2Backend(**kwargs)
            self._mode = f"fallback_cpu:{type(exc).__name__}"

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
        d["mjx_mode"] = self._mode
        return d

    def close(self) -> None:
        self._impl.close()
