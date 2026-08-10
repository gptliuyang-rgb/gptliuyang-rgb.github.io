#!/usr/bin/env python3
"""Self-contained grasp+lift demo. Builds scene from local Hand2 MJCF if needed."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT / "assets" / "scanner" / "grasp_demo_scene.xml"
HAND = ROOT / "assets" / "wuji_hand2" / "mjcf" / "right.xml"


def ensure_scene() -> Path:
    if SCENE.exists():
        return SCENE
    if not HAND.exists():
        raise FileNotFoundError(f"Missing hand MJCF: {HAND}")

    xml = HAND.read_text(encoding="utf-8")
    xml = xml.replace(
        '<body name="r_wrist">',
        """<body name="arm_mount" pos="0 0 0">
      <joint name="wrist_lift" type="slide" axis="0 0 1" range="0 0.25" damping="8"/>
      <body name="r_wrist" pos="0 0 0.22">""",
        1,
    )
    xml = xml.replace(
        "</worldbody>",
        """  </body>
    <body name="scanner" pos="0.01 0.03 0.13">
      <freejoint name="scanner_free"/>
      <inertial pos="0 0 0.02" mass="0.08" diaginertia="8e-5 8e-5 3e-5"/>
      <geom name="handle" type="capsule" fromto="0 0 -0.04 0 0 0.04" size="0.015"
            rgba="0.1 0.1 0.14 1" friction="1.5 0.2 0.05"/>
      <geom name="head" type="box" size="0.03 0.018 0.015" pos="0.035 0 0.05"
            rgba="0.2 0.2 0.25 1"/>
    </body>
    <geom name="floor" type="plane" size="1 1 0.1" rgba="0.25 0.28 0.25 1"/>
  </worldbody>""",
        1,
    )
    xml = xml.replace(
        "</actuator>",
        """  <position name="wrist_lift_act" joint="wrist_lift" kp="400" kv="40"
               ctrlrange="0 0.25" forcerange="-100 100"/>
  </actuator>""",
        1,
    )
    eq = """
  <equality>
    <weld name="grasp_weld" body1="r_wrist" body2="scanner" torquescale="1" active="false"/>
  </equality>
"""
    if "</contact>" in xml:
        xml = xml.replace("</contact>", "</contact>" + eq, 1)
    else:
        xml = xml.replace("</mujoco>", eq + "</mujoco>", 1)

    SCENE.parent.mkdir(parents=True, exist_ok=True)
    SCENE.write_text(xml, encoding="utf-8")
    print("Generated", SCENE)
    return SCENE


def load_model(path: Path) -> mujoco.MjModel:
    try:
        from wuji_r2s2r.sim.mujoco.loader import load_mjmodel

        return load_mjmodel(path)
    except Exception:
        return mujoco.MjModel.from_xml_path(str(path.resolve()))


def grasp_pose() -> np.ndarray:
    q = np.zeros(20)
    q[0], q[1], q[2], q[3] = 0.25, 0.75, 0.55, 0.55
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
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    scene = ensure_scene()
    model = load_model(scene)
    data = mujoco.MjData(model)
    if model.nu < 21 or model.neq < 1:
        raise RuntimeError(f"Bad model nu={model.nu} neq={model.neq}")

    dt = float(model.opt.timestep)
    open_pose = np.zeros(20)
    close_pose = grasp_pose()
    phases = [
        ("OPEN", 0.8, open_pose, 0.0, False),
        ("CLOSE_GRASP", 1.2, close_pose, 0.0, False),
        ("LOCK_GRASP(weld)", 0.3, close_pose, 0.0, True),
        ("LIFT", 2.0, close_pose, 0.18, True),
        ("HOLD", 1.5, close_pose, 0.18, True),
    ]

    print("=== Assisted grasp+lift demo (NOT the BC checkpoint) ===")
    print("Close the MuJoCo window to stop.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        for name, seconds, hand_q, lift, weld_on in phases:
            print("phase:", name)
            data.eq_active[0] = weld_on
            data.ctrl[:20] = hand_q
            data.ctrl[20] = lift
            for _ in range(int(seconds / dt)):
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
