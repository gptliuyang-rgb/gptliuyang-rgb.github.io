#!/usr/bin/env python3
"""Diagnose Hand 2 mapping and optional real hardware."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.schema.joint_mapping import JointMapping
from wuji_r2s2r.sim.common.factory import make_backend

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", default="right")
    ap.add_argument("--backend", default="mujoco", choices=["mujoco","mock","real","mjx","mjwarp","isaaclab"])
    args = ap.parse_args()
    m = JointMapping()
    print("revision:", m.raw["hand_revision"], "dof:", len(m.joints))
    print("canonical:", m.names)
    env = make_backend(args.backend if args.backend != "real" else "real", side=args.side, **({"dry_run": True} if args.backend=="real" else {}))
    obs = env.reset()
    print("observe q:", obs.joint_position.round(4).tolist())
    print("diagnostics:", json.dumps(env.diagnostics(), indent=2, default=str))
    env.close()

if __name__ == "__main__":
    main()
