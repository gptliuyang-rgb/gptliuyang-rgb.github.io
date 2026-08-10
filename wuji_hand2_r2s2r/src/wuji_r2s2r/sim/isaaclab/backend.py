"""Isaac Lab backend placeholder — optional secondary physics engine."""

from __future__ import annotations

from typing import Any

from wuji_r2s2r.schema.types import HandAction, HandObservation
from wuji_r2s2r.sim.common.backend import HandBackend
from wuji_r2s2r.sim.common.mock_backend import MockHand2Backend


class IsaacLabHand2Backend(HandBackend):
    """Requires NVIDIA Isaac Lab / Isaac Sim. Falls back to mock when absent."""

    name = "isaaclab"

    def __init__(self, **kwargs):
        self._available = False
        self._reason = "Isaac Lab not installed in this environment"
        try:
            import isaaclab  # noqa: F401
            self._available = True
            self._reason = "isaaclab import succeeded; full env wiring TBD"
        except Exception as exc:  # noqa: BLE001
            self._reason = str(exc)
        # Keep interface operational for CI / dry-run.
        self._impl = MockHand2Backend(**{k: v for k, v in kwargs.items() if k in {"side", "dt", "kp"}})

    def reset(self, qpos=None, **kwargs) -> HandObservation:
        return self._impl.reset(qpos=qpos, **kwargs)

    def observe(self) -> HandObservation:
        return self._impl.observe()

    def command(self, action: HandAction) -> None:
        self._impl.command(action)

    def step(self, n: int = 1) -> HandObservation:
        return self._impl.step(n)

    def diagnostics(self) -> dict[str, Any]:
        d = self._impl.diagnostics()
        d.update({
            "backend": self.name,
            "isaaclab_available": self._available,
            "reason": self._reason,
            "usd_asset": "assets/wuji_hand2/usd/{side}/wujihand2.usd",
        })
        return d

    def close(self) -> None:
        self._impl.close()
