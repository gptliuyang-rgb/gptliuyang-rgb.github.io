#!/usr/bin/env python3
"""Generate simulated scanner curriculum episodes with scripted policy."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.schema.types import EpisodeMetadata
from wuji_r2s2r.recording.episode_io import save_episode
from wuji_r2s2r.sim.common.factory import make_backend
from wuji_r2s2r.policies.scripted_scanner import ScriptedScannerPolicy
from wuji_r2s2r.randomization.sampler import DRSampler

def main():
    sampler = DRSampler(seed=1)
    policy = ScriptedScannerPolicy()
    scene = ROOT / "assets" / "scanner" / "scanner_scene_right.xml"
    out_root = ROOT / "data" / "simulation" / "R2_TELEOP_DEMOS" / "scripted_v0"
    manifests = []
    for i in range(5):
        params = sampler.sample()
        env = make_backend("mujoco", side="right", scene_xml=scene)
        policy.reset()
        obs = env.reset()
        qs, dqs, effs, acts, ts = [], [], [], [], []
        for _ in range(300):
            action = policy.act(obs)
            env.command(action)
            obs = env.step(10)
            qs.append(obs.joint_position); dqs.append(obs.joint_velocity)
            effs.append(obs.effort); acts.append(action.position_target); ts.append(obs.timestamp_ns)
        meta = EpisodeMetadata(
            episode_id=f"sim_scripted_{i:03d}",
            source="mujoco",
            task="scanner_T0_T5",
            dataset_purpose="R2_TELEOP_DEMOS",
            simulator_parameters=params,
            randomization_version=params["randomization_version"],
        )
        path = save_episode(out_root, meta, np.stack(qs), np.stack(dqs), np.stack(effs), np.stack(acts), np.array(ts),
                            labels={"phase_final": policy.fsm.phase.value, "success": policy.fsm.phase.value=="SUCCESS"})
        manifests.append({"episode": str(path), "params": params})
        env.close()
    man = ROOT / "data" / "manifests" / "sim_scripted_v0.json"
    man.write_text(json.dumps({"episodes": manifests, "n": len(manifests)}, indent=2, default=str))
    print("Wrote", man, "n=", len(manifests))

if __name__ == "__main__":
    main()
