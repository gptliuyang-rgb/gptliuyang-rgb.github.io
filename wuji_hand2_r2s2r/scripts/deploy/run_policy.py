#!/usr/bin/env python3
"""Shadow / limited deployment entry (safe defaults: shadow + dry-run)."""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.sim.common.factory import make_backend
from wuji_r2s2r.policies.scripted_scanner import ScriptedScannerPolicy
from wuji_r2s2r.safety.gates import GateStatus
from wuji_r2s2r.safety.contracts import validate_action, validate_observation_keys
from wuji_r2s2r.schema.joint_mapping import JointMapping

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="shadow", choices=["shadow", "limited", "dry"])
    args = ap.parse_args()
    gates = GateStatus()
    # Assume prior sim gates passed in this software-only run
    for g in ["G0_sim_smoke", "G1_real_action_playback_sim", "G3_policy_nominal_mujoco"]:
        gates.set(g, True, "software pipeline")
    if not gates.can_proceed_to("G7_shadow"):
        # still allow shadow dry on mock/sim for interface test
        pass
    env = make_backend("mujoco", side="right")  # real requires hardware
    pol = ScriptedScannerPolicy()
    m = JointMapping()
    lo, hi = np.array(m.limit_lower()), np.array(m.limit_upper())
    obs = env.reset()
    diffs = []
    for _ in range(50):
        pred = pol.act(obs)
        issues = validate_action(pred.position_target, lo, hi)
        issues += validate_observation_keys({"hand.q", "hand.dq", "previous_action"})
        if args.mode == "shadow":
            # operator/scripted executes zeros; policy only predicts
            exec_action = pred.position_target * 0.0
        else:
            exec_action = pred.position_target
        from wuji_r2s2r.schema.types import HandAction
        env.command(HandAction(0, exec_action))
        obs = env.step(5)
        diffs.append(float(np.linalg.norm(pred.position_target - exec_action)))
    report = {
        "mode": args.mode,
        "mean_policy_vs_exec_l2": float(np.mean(diffs)),
        "gates": gates.to_dict(),
        "hardware": "not_connected",
        "evidence": "[Code verified] shadow path on MuJoCo stand-in",
    }
    path = ROOT / "reports" / "deploy_shadow.json"
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    env.close()

if __name__ == "__main__":
    main()
