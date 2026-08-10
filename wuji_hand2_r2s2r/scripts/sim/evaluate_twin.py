#!/usr/bin/env python3
"""Evaluate digital twin on holdout synthetic free-space episodes."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.schema.types import HandAction, EpisodeMetadata
from wuji_r2s2r.recording.episode_io import save_episode, load_episode
from wuji_r2s2r.sim.common.factory import make_backend
from wuji_r2s2r.sim.mujoco.replay import replay_episode
from wuji_r2s2r.quality.episode_qa import check_episode
from wuji_r2s2r.schema.joint_mapping import JointMapping

def synthesize(split: str, seed: int, T: int = 200) -> Path:
    rng = np.random.default_rng(seed)
    env = make_backend("mujoco", side="right")
    obs = env.reset()
    qs, dqs, effs, acts, ts = [], [], [], [], []
    q0 = obs.joint_position.copy()
    # multi-sine free-space excitation
    t = np.arange(T) * 0.02
    target_traj = np.zeros((T, 20))
    for j in range(20):
        amp = 0.2 + 0.05 * (j % 3)
        freq = 0.4 + 0.1 * (j % 5)
        target_traj[:, j] = amp * np.sin(2 * np.pi * freq * t + rng.uniform(0, 1))
    for i in range(T):
        a = HandAction(int(i * 2e7), target_traj[i])
        env.command(a)
        obs = env.step(10)
        qs.append(obs.joint_position.copy())
        dqs.append(obs.joint_velocity.copy())
        effs.append(obs.effort.copy())
        acts.append(target_traj[i].copy())
        ts.append(obs.timestamp_ns)
    env.close()
    meta = EpisodeMetadata(
        episode_id=f"sysid_{split}_{seed:03d}",
        source="mujoco",
        task="free_space_sine",
        dataset_purpose="R1_SYSTEM_ID",
        digital_twin_version="hand2_twin_v0.1",
    )
    out = ROOT / "data" / "simulation" / "R1_SYSTEM_ID" / split
    return save_episode(out, meta, np.stack(qs), np.stack(dqs), np.stack(effs), np.stack(acts), np.array(ts),
                        labels={"split": split})

def main():
    mapping = JointMapping()
    paths = []
    for split, seeds in [("SYSID_TRAIN", [0,1,2]), ("SYSID_VALIDATION", [10]), ("SYSID_HOLDOUT", [20,21])]:
        for s in seeds:
            paths.append(synthesize(split, s))
    results = []
    for p in paths:
        ep = load_episode(p)
        qa = check_episode(ep["metadata"]["episode_id"], ep["q"], ep["dq"], ep["timestamp_ns"], ep["actions"],
                           np.array(mapping.limit_lower()), np.array(mapping.limit_upper()))
        _, metrics = replay_episode(ep["q"], ep["actions"], ep["timestamp_ns"], backend="mujoco")
        results.append({"episode": str(p), "qa": qa.to_dict(), "replay": metrics.to_dict(), "split": ep["metadata"]["labels"]["split"]})
    hold = [r for r in results if r["split"] == "SYSID_HOLDOUT"]
    summary = {
        "digital_twin_version": "hand2_twin_v0.1",
        "holdout_mean_q_rmse": float(np.mean([r["replay"]["joint_position_RMSE"] for r in hold])),
        "results": results,
        "evidence": "[Simulation verified]",
    }
    out = ROOT / "reports" / "twin_evaluation.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ["digital_twin_version","holdout_mean_q_rmse","evidence"]}, indent=2))

if __name__ == "__main__":
    main()
