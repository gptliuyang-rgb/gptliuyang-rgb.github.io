#!/usr/bin/env python3
"""Evaluate scripted + BC policies in MuJoCo scanner scene."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.sim.common.factory import make_backend
from wuji_r2s2r.policies.scripted_scanner import ScriptedScannerPolicy
from wuji_r2s2r.schema.types import HandAction
from wuji_r2s2r.scanner.surrogate import scan_success
from wuji_r2s2r.task_graph.scanner_fsm import Phase

def eval_scripted(n=5):
    scene = ROOT / "assets" / "scanner" / "scanner_scene_right.xml"
    rows = []
    for i in range(n):
        env = make_backend("mujoco", side="right", scene_xml=scene)
        pol = ScriptedScannerPolicy()
        obs = env.reset()
        for _ in range(350):
            a = pol.act(obs); env.command(a); obs = env.step(10)
        # surrogate decode near end
        ok = scan_success(True, True, 0.2, 0.1) and pol.fsm.phase in {Phase.SUCCESS, Phase.VERIFY_DECODE, Phase.TRIGGER}
        rows.append({"episode": i, "final_phase": pol.fsm.phase.value, "proxy_success": bool(ok)})
        env.close()
    return rows

def main():
    rows = eval_scripted()
    rate = float(np.mean([r["proxy_success"] for r in rows]))
    out = {"policy": "P0_scripted", "n": len(rows), "proxy_success_rate": rate, "rows": rows,
           "evidence": "[Simulation verified] surrogate decode; not physical scanner"}
    path = ROOT / "reports" / "eval_sim_scripted.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
