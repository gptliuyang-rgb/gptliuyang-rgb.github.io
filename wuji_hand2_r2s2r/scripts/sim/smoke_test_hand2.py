#!/usr/bin/env python3
"""SIM-L0/L1 smoke: load Hand2, map joints, step actuators."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.schema.joint_mapping import JointMapping
from wuji_r2s2r.schema.types import HandAction
from wuji_r2s2r.sim.common.factory import make_backend
import mujoco

def main():
    mapping = JointMapping()
    env = make_backend("mujoco", side="right")
    # Validate joint names against model
    names = []
    for i in range(env.model.njnt):
        names.append(mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_JOINT, i))
    mapping.validate_against_mjcf_joint_names([n for n in names if n], side="right")
    obs = env.reset()
    target = np.array(mapping.limit_lower()) * 0.0
    target[4] = 0.5  # index mcp flex
    for _ in range(100):
        env.command(HandAction(0, target))
        obs = env.step(1)
    tips = env.fingertip_positions()
    report = {
        "sim_level": "SIM-L1",
        "nq": env.model.nq,
        "nu": env.model.nu,
        "final_q": obs.joint_position.tolist(),
        "fingertips": {k: v.tolist() for k, v in tips.items()},
        "diagnostics": env.diagnostics(),
    }
    out = ROOT / "reports" / "sim_l1_smoke.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    env.close()
    print("Wrote", out)

if __name__ == "__main__":
    main()
