#!/usr/bin/env python3
"""Visual playback for trained / scripted policies in MuJoCo.

Examples (from wuji_hand2_r2s2r/, venv active):

  python scripts/sim/play_policy.py --mode bc --scene scanner
  python scripts/sim/play_policy.py --mode scripted --scene scanner
  python scripts/sim/play_policy.py --mode episode
  python scripts/sim/play_policy.py --mode bc --fast   # no realtime sleep

Close the MuJoCo window to stop.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.policies.scripted_scanner import ScriptedScannerPolicy
from wuji_r2s2r.recording.episode_io import load_episode
from wuji_r2s2r.schema.joint_mapping import JointMapping
from wuji_r2s2r.schema.types import HandObservation
from wuji_r2s2r.sim.mujoco.loader import load_mjmodel


class LinearBCPolicy:
    """Matches scripts/train/train.py: action = [q, dq] @ W."""

    def __init__(self, checkpoint: Path):
        data = np.load(checkpoint)
        self.W = np.asarray(data["W"], dtype=np.float64)
        if self.W.shape != (40, 20):
            raise ValueError(f"Unexpected W shape {self.W.shape}, expected (40, 20)")

    def act(self, q: np.ndarray, dq: np.ndarray) -> np.ndarray:
        return np.concatenate([q, dq], axis=0) @ self.W


def _xml_for_scene(scene: str) -> Path:
    if scene == "hand":
        return ROOT / "assets" / "wuji_hand2" / "mjcf" / "right.xml"
    if scene == "scanner":
        return ROOT / "assets" / "scanner" / "scanner_scene_right.xml"
    raise ValueError(scene)


def _bind_hand(model: mujoco.MjModel) -> tuple[list[int], list[int], list[int]]:
    mapping = JointMapping()
    qadr, dadr, aids = [], [], []
    for jn, an in zip(mapping.mjcf_names("right"), mapping.actuator_names("right")):
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, jn)
        if jid < 0:
            raise KeyError(jn)
        qadr.append(int(model.jnt_qposadr[jid]))
        dadr.append(int(model.jnt_dofadr[jid]))
        aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, an)
        aids.append(int(aid))
    return qadr, dadr, aids


def _read_obs(data: mujoco.MjData, qadr: list[int], dadr: list[int], t_ns: int) -> HandObservation:
    q = np.array([data.qpos[a] for a in qadr], dtype=np.float64)
    dq = np.array([data.qvel[a] for a in dadr], dtype=np.float64)
    return HandObservation(timestamp_ns=t_ns, joint_position=q, joint_velocity=dq, effort=np.zeros(20))


def play_live(mode: str, scene: str, checkpoint: Path, steps: int, realtime: bool, substeps: int) -> None:
    model = load_mjmodel(_xml_for_scene(scene))
    data = mujoco.MjData(model)
    qadr, dadr, aids = _bind_hand(model)
    mujoco.mj_forward(model, data)

    bc = LinearBCPolicy(checkpoint) if mode == "bc" else None
    scripted = ScriptedScannerPolicy() if mode == "scripted" else None

    control_dt = float(model.opt.timestep) * substeps
    print(f"Playing mode={mode} scene={scene}  control_dt={control_dt:.3f}s  steps={steps}")
    print("Close the MuJoCo window to stop.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        for i in range(steps):
            if not viewer.is_running():
                break
            obs = _read_obs(data, qadr, dadr, i)
            if mode == "bc":
                target = bc.act(obs.joint_position, obs.joint_velocity)
            else:
                target = scripted.act(obs).position_target
            for k, aid in enumerate(aids):
                if 0 <= aid < model.nu:
                    data.ctrl[aid] = float(target[k])
            for _ in range(substeps):
                mujoco.mj_step(model, data)
            viewer.sync()
            if realtime:
                time.sleep(control_dt)

    print("Done.")


def play_episode(episode: Path, scene: str, realtime: bool) -> None:
    ep = load_episode(episode)
    q = np.asarray(ep["q"], dtype=np.float64)
    model = load_mjmodel(_xml_for_scene(scene))
    data = mujoco.MjData(model)
    qadr, _, _ = _bind_hand(model)

    ts = ep.get("timestamp_ns")
    if ts is not None and len(ts) > 1:
        dt = float(np.median(np.diff(ts.astype(np.float64))) / 1e9)
        dt = float(np.clip(dt, 0.005, 0.1))
    else:
        dt = 0.02

    print(f"Replaying {episode.name}  T={len(q)}  dt={dt:.3f}s")
    print("Close the MuJoCo window to stop.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        for i in range(len(q)):
            if not viewer.is_running():
                break
            for j, adr in enumerate(qadr):
                data.qpos[adr] = float(q[i, j])
            mujoco.mj_forward(model, data)
            viewer.sync()
            if realtime:
                time.sleep(dt)
    print("Done.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Visual policy / episode player")
    ap.add_argument("--mode", choices=["bc", "scripted", "episode"], default="bc")
    ap.add_argument("--scene", choices=["hand", "scanner"], default="scanner")
    ap.add_argument("--checkpoint", default=str(ROOT / "checkpoints" / "scanner_bc_v0.npz"))
    ap.add_argument("--episode", default="")
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--substeps", type=int, default=10)
    ap.add_argument("--fast", action="store_true", help="Disable realtime sleep")
    args = ap.parse_args()
    realtime = not args.fast

    if args.mode == "episode":
        if args.episode:
            ep_dir = Path(args.episode)
        else:
            cand = sorted(
                (ROOT / "data" / "simulation" / "R2_TELEOP_DEMOS" / "scripted_v0").glob(
                    "*/timeseries.npz"
                )
            )
            if not cand:
                print("No episode found. Run: python scripts/collect/generate_sim_dataset.py")
                sys.exit(1)
            ep_dir = cand[0].parent
        play_episode(ep_dir, args.scene, realtime)
        return

    ckpt = Path(args.checkpoint)
    if args.mode == "bc" and not ckpt.exists():
        print(f"Missing checkpoint: {ckpt}\nRun: python scripts/train/train.py")
        sys.exit(1)
    play_live(args.mode, args.scene, ckpt, args.steps, realtime, args.substeps)


if __name__ == "__main__":
    main()
