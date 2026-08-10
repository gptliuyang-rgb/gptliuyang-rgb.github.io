"""Backend factory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wuji_r2s2r.sim.common.backend import HandBackend


def make_backend(kind: str, **kwargs: Any) -> HandBackend:
    kind = kind.lower()
    if kind in {"mujoco", "mujoco_cpu"}:
        from wuji_r2s2r.sim.mujoco.backend import MuJoCoHand2Backend
        return MuJoCoHand2Backend(**kwargs)
    if kind in {"mjwarp", "mujoco_warp"}:
        from wuji_r2s2r.sim.mujoco.mjwarp_backend import MJWarpHand2Backend
        return MJWarpHand2Backend(**kwargs)
    if kind == "mjx":
        from wuji_r2s2r.sim.mujoco.mjx_backend import MJXHand2Backend
        return MJXHand2Backend(**kwargs)
    if kind == "isaaclab":
        from wuji_r2s2r.sim.isaaclab.backend import IsaacLabHand2Backend
        return IsaacLabHand2Backend(**kwargs)
    if kind == "replay":
        from wuji_r2s2r.sim.common.replay_backend import ReplayHand2Backend
        return ReplayHand2Backend(**kwargs)
    if kind == "mock":
        from wuji_r2s2r.sim.common.mock_backend import MockHand2Backend
        return MockHand2Backend(**kwargs)
    if kind == "real":
        from wuji_r2s2r.hardware.real_backend import WujiHand2RealBackend
        return WujiHand2RealBackend(**kwargs)
    raise ValueError(f"Unknown backend kind: {kind}")


def default_mjcf(side: str = "right") -> Path:
    # factory.py lives at src/wuji_r2s2r/sim/common/ → repo root is parents[4]
    root = Path(__file__).resolve().parents[4]
    return root / "assets" / "wuji_hand2" / "mjcf" / f"{side}.xml"
