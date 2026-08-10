"""Unit tests for joint mapping and backend contracts."""

from __future__ import annotations

import numpy as np
import mujoco
import pytest

from wuji_r2s2r.schema.joint_mapping import JointMapping, DOF
from wuji_r2s2r.schema.types import HandAction
from wuji_r2s2r.sim.common.factory import make_backend, default_mjcf
from wuji_r2s2r.scanner.surrogate import scan_success
from wuji_r2s2r.task_graph.scanner_fsm import ScannerFSM, Phase
from wuji_r2s2r.safety.contracts import validate_action, validate_observation_keys
from wuji_r2s2r.sysid.registry import ParameterRegistry
from wuji_r2s2r.randomization.sampler import DRSampler
from wuji_r2s2r.quality.episode_qa import check_episode


def test_joint_mapping_count_and_order():
    m = JointMapping()
    assert len(m.joints) == DOF
    assert m.names[0] == "thumb_cmc_flex"
    assert m.names[4] == "index_finger_mcp_flex"
    assert m.sdk_to_canonical(1, 0) == 4


def test_mujoco_model_loads_and_matches_mapping():
    from wuji_r2s2r.sim.mujoco.loader import load_mjmodel

    m = JointMapping()
    path = default_mjcf("right")
    model = load_mjmodel(path)
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(model.njnt)]
    m.validate_against_mjcf_joint_names([n for n in names if n], side="right")
    assert model.nu == 20


def test_mujoco_backend_step():
    env = make_backend("mujoco", side="right")
    obs = env.reset()
    assert obs.joint_position.shape == (20,)
    target = np.zeros(20)
    target[4] = 0.3
    env.command(HandAction(0, target))
    obs2 = env.step(50)
    assert abs(obs2.joint_position[4]) > 0.01
    env.close()


def test_mock_and_contracts():
    env = make_backend("mock")
    obs = env.reset()
    a = np.zeros(20)
    m = JointMapping()
    assert validate_action(a, np.array(m.limit_lower()), np.array(m.limit_upper())) == []
    assert validate_observation_keys({"hand.q", "hand.dq", "previous_action"}) == []
    assert "forbidden" in ",".join(validate_observation_keys({"hand.q", "hand.dq", "previous_action", "simulator.friction"}))
    env.close()


def test_scan_surrogate_and_fsm():
    assert scan_success(True, True, 0.2, 0.1) is True
    assert scan_success(False, True, 0.2, 0.1) is False
    fsm = ScannerFSM()
    assert fsm.advance() == Phase.LOCATE_SCANNER
    fsm.fail("GRASP_FAIL")
    assert fsm.phase == Phase.RETRY_GRASP


def test_registry_and_dr():
    reg = ParameterRegistry()
    assert reg.version.startswith("hand2_twin")
    assert "actuator_kp" in reg.to_mujoco_overrides()
    assert "note" in reg.to_isaac_overrides()
    s = DRSampler(seed=0).sample()
    assert "scanner_mass" in s


def test_episode_qa():
    T = 50
    q = np.zeros((T, 20))
    q[:, 0] = np.linspace(0, 0.1, T)
    ts = (np.arange(T) * 20_000_000).astype(np.int64)
    report = check_episode("ep", q, timestamp_ns=ts, actions=q.copy())
    assert report.grade in {"A", "B"}
