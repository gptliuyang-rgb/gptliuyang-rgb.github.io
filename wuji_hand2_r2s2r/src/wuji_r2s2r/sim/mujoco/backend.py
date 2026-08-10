"""MuJoCo CPU backend for Wuji Hand 2."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

import mujoco
import numpy as np

from wuji_r2s2r.schema.joint_mapping import JointMapping
from wuji_r2s2r.schema.types import DOF, HandAction, HandObservation
from wuji_r2s2r.sim.common.backend import HandBackend
from wuji_r2s2r.sim.common.factory import default_mjcf
from wuji_r2s2r.sim.mujoco.loader import load_mjmodel


class MuJoCoHand2Backend(HandBackend):
    name = "mujoco"

    def __init__(
        self,
        side: str = "right",
        model_path: str | Path | None = None,
        scene_xml: str | Path | None = None,
        n_substeps: int = 1,
    ):
        self.side = side
        self.mapping = JointMapping()
        path = Path(scene_xml) if scene_xml else Path(model_path) if model_path else default_mjcf(side)
        if not path.exists():
            raise FileNotFoundError(path)
        # Use Unicode-safe loader (Windows paths like D:\\下载\\... break from_xml_path).
        self.model = load_mjmodel(path)
        self.data = mujoco.MjData(self.model)
        self.n_substeps = n_substeps
        self._joint_qpos_adr: list[int] = []
        self._joint_dof_adr: list[int] = []
        self._act_ids: list[int] = []
        self._bind_joints()
        self._t0 = time.time_ns()
        self._steps = 0
        self._last_action = np.zeros(DOF)

    def _bind_joints(self) -> None:
        names = self.mapping.mjcf_names(self.side)
        acts = self.mapping.actuator_names(self.side)
        for jn, an in zip(names, acts):
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, jn)
            if jid < 0:
                raise KeyError(f"Joint not found in MJCF: {jn}")
            self._joint_qpos_adr.append(int(self.model.jnt_qposadr[jid]))
            self._joint_dof_adr.append(int(self.model.jnt_dofadr[jid]))
            aid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, an)
            if aid < 0:
                # Fallback: actuator order matches joint order in official MJCF
                aid = len(self._act_ids)
            self._act_ids.append(int(aid))
        if len(self._joint_qpos_adr) != DOF:
            raise RuntimeError("Failed to bind 20 joints")

    def reset(self, qpos=None, **kwargs) -> HandObservation:
        mujoco.mj_resetData(self.model, self.data)
        if qpos is not None:
            q = np.asarray(qpos, dtype=np.float64).reshape(DOF)
            for i, adr in enumerate(self._joint_qpos_adr):
                self.data.qpos[adr] = q[i]
        mujoco.mj_forward(self.model, self.data)
        self._steps = 0
        self._last_action = self._read_q()
        self.data.ctrl[:] = 0
        for i, aid in enumerate(self._act_ids):
            if aid < self.model.nu:
                self.data.ctrl[aid] = self._last_action[i]
        return self.observe()

    def _read_q(self) -> np.ndarray:
        return np.array([self.data.qpos[a] for a in self._joint_qpos_adr], dtype=np.float64)

    def _read_dq(self) -> np.ndarray:
        return np.array([self.data.qvel[a] for a in self._joint_dof_adr], dtype=np.float64)

    def _read_effort(self) -> np.ndarray:
        # actuator force if available
        out = np.zeros(DOF)
        for i, aid in enumerate(self._act_ids):
            if aid < self.model.nu:
                out[i] = float(self.data.actuator_force[aid])
        return out

    def observe(self) -> HandObservation:
        return HandObservation(
            timestamp_ns=self._t0 + int(self._steps * self.model.opt.timestep * 1e9),
            joint_position=self._read_q(),
            joint_velocity=self._read_dq(),
            effort=self._read_effort(),
            diagnostics={
                "backend": self.name,
                "ncon": int(self.data.ncon),
                "time": float(self.data.time),
            },
        )

    def command(self, action: HandAction) -> None:
        self._last_action = action.position_target.copy()
        for i, aid in enumerate(self._act_ids):
            if aid < self.model.nu:
                self.data.ctrl[aid] = float(self._last_action[i])

    def step(self, n: int = 1) -> HandObservation:
        for _ in range(n):
            for _s in range(self.n_substeps):
                mujoco.mj_step(self.model, self.data)
            self._steps += 1
        return self.observe()

    def diagnostics(self) -> dict[str, Any]:
        return {
            "backend": self.name,
            "side": self.side,
            "nq": self.model.nq,
            "nv": self.model.nv,
            "nu": self.model.nu,
            "timestep": float(self.model.opt.timestep),
            "ncon": int(self.data.ncon),
            "steps": self._steps,
        }

    def fingertip_positions(self) -> dict[str, np.ndarray]:
        sites = self.mapping.raw["fingertip_sites"][self.side]
        out = {}
        for s in sites:
            sid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, s)
            if sid >= 0:
                out[s] = self.data.site_xpos[sid].copy()
        return out

    def close(self) -> None:
        return None
