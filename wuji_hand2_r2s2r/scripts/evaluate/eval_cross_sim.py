#!/usr/bin/env python3
"""Sim2Sim gate: compare MuJoCo vs IsaacLab-fallback backends on same actions."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.schema.types import HandAction
from wuji_r2s2r.sim.common.factory import make_backend

def rollout(kind, actions):
    env = make_backend(kind, side="right")
    obs = env.reset(qpos=np.zeros(20))
    qs = [obs.joint_position.copy()]
    for a in actions:
        env.command(HandAction(0, a))
        obs = env.step(5)
        qs.append(obs.joint_position.copy())
    env.close()
    return np.stack(qs)

def main():
    T = 100
    t = np.arange(T) * 0.02
    actions = np.zeros((T, 20))
    actions[:, 4] = 0.4 * np.sin(2 * np.pi * 0.5 * t)
    q_mj = rollout("mujoco", actions)
    q_isaac = rollout("isaaclab", actions)
    # Compare shapes / disagreement metric (Isaac is mock fallback without Isaac Sim)
    disagree = float(np.sqrt(np.mean((q_mj[: len(q_isaac)] - q_isaac[: len(q_mj)]) ** 2)))
    out = {
        "mujoco_final_q_norm": float(np.linalg.norm(q_mj[-1])),
        "isaaclab_final_q_norm": float(np.linalg.norm(q_isaac[-1])),
        "trajectory_disagreement_rmse": disagree,
        "isaaclab_note": "Isaac Sim not installed; backend uses mock fallback",
        "evidence": "[Not yet verified] full PhysX cross-sim requires Isaac Lab install",
    }
    path = ROOT / "reports" / "eval_cross_sim.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
