"""P0 scripted baseline for scanner curriculum."""

from __future__ import annotations

import numpy as np

from wuji_r2s2r.schema.types import DOF, HandAction, HandObservation
from wuji_r2s2r.task_graph.scanner_fsm import Phase, ScannerFSM


class ScriptedScannerPolicy:
    """Deterministic joint-space baseline (no learning)."""

    name = "P0_scripted"

    def __init__(self):
        self.fsm = ScannerFSM()
        self._t = 0

    def reset(self):
        self.fsm = ScannerFSM()
        self._t = 0

    def _pose(self, phase: Phase) -> np.ndarray:
        q = np.zeros(DOF)
        # mild flexion on fingers for grasp-like poses
        flex_idx = [0, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19]
        if phase in {Phase.PRESHAPE}:
            q[flex_idx] = 0.3
        elif phase in {Phase.GRASP, Phase.VERIFY_GRASP, Phase.LIFT, Phase.AIM, Phase.TRIGGER}:
            q[flex_idx] = 0.7
            q[7] = 0.9  # index DIP for trigger bias
        elif phase == Phase.SUCCESS:
            q[flex_idx] = 0.6
        return q

    def act(self, obs: HandObservation) -> HandAction:
        self._t += 1
        # Advance FSM slowly for demo
        if self._t % 25 == 0 and self.fsm.phase != Phase.SUCCESS:
            self.fsm.advance()
        target = self._pose(self.fsm.phase)
        return HandAction(timestamp_ns=obs.timestamp_ns, position_target=target)
