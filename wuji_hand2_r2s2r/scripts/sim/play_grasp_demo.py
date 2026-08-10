#!/usr/bin/env python3
"""Visual grasp+lift demo for Wuji Hand 2 + scanner.

IMPORTANT:
  The trained linear BC checkpoint only imitates open/close joint gestures.
  It does NOT yet perform a physics contact grasp. This demo shows the intended
  task motion with an assisted weld after the hand closes (curriculum placeholder
  until real contact/sysID grasp is ready).

Usage:
  python scripts/sim/play_grasp_demo.py
  python scripts/sim/play_grasp_demo.py --fast
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

try:
    from wuji_r2s2r.sim.mujoco.loader import load_mjmodel
except ModuleNotFoundError:
    def load_mjmodel(xml_path: str | Path) -> mujoco.MjModel:
        return mujoco.MjModel.from_xml_path(str(Path(xml_path).resolve()))


def grasp_pose() -> np.ndarray:
    q = np.zeros(20)
    # thumb opposition-ish
    q[0] = 0.25
    q[1] = 0.75
    q[2] = 0.55
    q[3] = 0.55
    # fingers
    for i in [4, 8, 12, 16]:
        q[i] = 0.55
    for i in [6, 10, 14, 18]:
        q[i] = 0.95
    for i in [7, 11, 15, 19]:
        q[i] = 0.75
    return q


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--hold", type=float, default=1.5, help="seconds to hold at top")
    args = ap.parse_args()

    xml = ROOT / "assets" / "scanner" / "grasp_demo_scene.xml"
    if not xml.exists():
        print(f"Missing {xml}. Update assets from the repo branch.")
        sys.exit(1)

    model = load_mjmodel(xml)
    data = mujoco.MjData(model)
    if model.nu < 21 or model.neq < 1:
        print("Unexpected model: need 21 actuators and 1 weld equality")
        sys.exit(1)

    dt = float(model.opt.timestep)
    open_pose = np.zeros(20)
    close_pose = grasp_pose()

    phases = [
        ("OPEN", 0.8, open_pose, 0.0, False),
        ("CLOSE_GRASP", 1.2, close_pose, 0.0, False),
        ("LOCK_GRASP(weld)", 0.3, close_pose, 0.0, True),
        ("LIFT", 2.0, close_pose, 0.18, True),
        ("HOLD", args.hold, close_pose, 0.18, True),
    ]

    print("=== Grasp demo (assisted weld after close) ===")
    print("This is NOT the BC checkpoint. Close the window to stop.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        for name, seconds, hand_q, lift, weld_on in phases:
            print(f"phase: {name}")
            data.eq_active[0] = weld_on
            data.ctrl[:20] = hand_q
            data.ctrl[20] = lift
            n = int(seconds / dt)
            for _ in range(n):
                if not viewer.is_running():
                    print("Stopped.")
                    return
                mujoco.mj_step(model, data)
                viewer.sync()
                if not args.fast:
                    time.sleep(dt)

    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "scanner")
    print("final scanner xyz:", np.round(data.xpos[bid], 4))
    print("Done.")


if __name__ == "__main__":
    main()
