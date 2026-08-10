"""Real→Sim open-loop replay engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from wuji_r2s2r.schema.types import HandAction
from wuji_r2s2r.sim.common.factory import make_backend


@dataclass
class ReplayMetrics:
    joint_position_RMSE: float
    joint_velocity_RMSE: float
    trajectory_divergence_time: float | None
    per_joint_rmse: list[float]
    extra: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "joint_position_RMSE": self.joint_position_RMSE,
            "joint_velocity_RMSE": self.joint_velocity_RMSE,
            "trajectory_divergence_time": self.trajectory_divergence_time,
            "per_joint_rmse": self.per_joint_rmse,
            **self.extra,
        }


def replay_episode(
    q_real: np.ndarray,
    actions: np.ndarray,
    timestamp_ns: np.ndarray | None = None,
    backend: str = "mujoco",
    side: str = "right",
    control_steps_per_action: int = 10,
    diverge_thresh: float = 0.25,
    scene_xml=None,
) -> tuple[np.ndarray, ReplayMetrics]:
    """Replay real actions open-loop and compare to real q."""
    env = make_backend(backend, side=side, scene_xml=scene_xml) if scene_xml else make_backend(backend, side=side)
    try:
        obs = env.reset(qpos=q_real[0])
        q_sim = [obs.joint_position.copy()]
        dq_sim = [obs.joint_velocity.copy()]
        T = min(len(q_real), len(actions))
        for t in range(1, T):
            env.command(HandAction(timestamp_ns=0, position_target=actions[t - 1]))
            obs = env.step(control_steps_per_action)
            q_sim.append(obs.joint_position.copy())
            dq_sim.append(obs.joint_velocity.copy())
        q_sim_a = np.stack(q_sim)
        dq_sim_a = np.stack(dq_sim)
        q_r = q_real[: len(q_sim_a)]
        err = q_sim_a - q_r
        rmse = float(np.sqrt(np.mean(err ** 2)))
        per_joint = np.sqrt(np.mean(err ** 2, axis=0)).tolist()
        # velocity if possible
        if timestamp_ns is not None and len(timestamp_ns) >= 2:
            dt = np.diff(timestamp_ns.astype(np.float64)) / 1e9
            dt = np.clip(dt, 1e-4, 1.0)
            dq_r = np.zeros_like(q_r)
            dq_r[1:] = np.diff(q_r, axis=0) / dt[: len(q_r) - 1, None]
        else:
            dq_r = np.gradient(q_r, axis=0)
        v_rmse = float(np.sqrt(np.mean((dq_sim_a - dq_r[: len(dq_sim_a)]) ** 2)))
        norms = np.linalg.norm(err, axis=1)
        diverge_idx = np.where(norms > diverge_thresh)[0]
        diverge_t = float(diverge_idx[0]) if len(diverge_idx) else None
        metrics = ReplayMetrics(
            joint_position_RMSE=rmse,
            joint_velocity_RMSE=v_rmse,
            trajectory_divergence_time=diverge_t,
            per_joint_rmse=per_joint,
            extra={"T": len(q_sim_a), "backend": backend},
        )
        return q_sim_a, metrics
    finally:
        env.close()
