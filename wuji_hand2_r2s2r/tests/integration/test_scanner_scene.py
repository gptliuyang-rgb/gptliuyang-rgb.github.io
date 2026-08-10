"""Integration: scanner scene load + scripted rollout."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from wuji_r2s2r.policies.scripted_scanner import ScriptedScannerPolicy
from wuji_r2s2r.sim.common.factory import make_backend

ROOT = Path(__file__).resolve().parents[2]


def test_scanner_scene_rollout():
    scene = ROOT / "assets" / "scanner" / "scanner_scene_right.xml"
    env = make_backend("mujoco", side="right", scene_xml=scene)
    pol = ScriptedScannerPolicy()
    obs = env.reset()
    for _ in range(30):
        a = pol.act(obs)
        env.command(a)
        obs = env.step(5)
    assert obs.joint_position.shape == (20,)
    assert env.diagnostics()["ncon"] >= 0
    env.close()
