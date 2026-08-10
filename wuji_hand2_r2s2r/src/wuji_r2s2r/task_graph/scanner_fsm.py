"""Scanner PoC explicit task state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Phase(str, Enum):
    READY = "READY"
    LOCATE_SCANNER = "LOCATE_SCANNER"
    APPROACH = "APPROACH"
    PRESHAPE = "PRESHAPE"
    GRASP = "GRASP"
    VERIFY_GRASP = "VERIFY_GRASP"
    LIFT = "LIFT"
    LOCATE_QR = "LOCATE_QR"
    AIM = "AIM"
    TRIGGER = "TRIGGER"
    VERIFY_DECODE = "VERIFY_DECODE"
    SUCCESS = "SUCCESS"
    RETRY_GRASP = "RETRY_GRASP"
    REGRASP = "REGRASP"
    SEARCH = "SEARCH"
    RELOCALIZE = "RELOCALIZE"
    SAFE_STOP = "SAFE_STOP"
    SAFE_ABORT = "SAFE_ABORT"


FORWARD = [
    Phase.READY,
    Phase.LOCATE_SCANNER,
    Phase.APPROACH,
    Phase.PRESHAPE,
    Phase.GRASP,
    Phase.VERIFY_GRASP,
    Phase.LIFT,
    Phase.LOCATE_QR,
    Phase.AIM,
    Phase.TRIGGER,
    Phase.VERIFY_DECODE,
    Phase.SUCCESS,
]


@dataclass
class ScannerFSM:
    phase: Phase = Phase.READY
    retries: int = 0
    max_retries: int = 3
    history: list[str] = field(default_factory=list)

    def advance(self) -> Phase:
        if self.phase == Phase.SUCCESS:
            return self.phase
        try:
            i = FORWARD.index(self.phase)
            self.phase = FORWARD[min(i + 1, len(FORWARD) - 1)]
        except ValueError:
            # recovery states re-enter nominal path
            if self.phase in {Phase.RETRY_GRASP, Phase.REGRASP}:
                self.phase = Phase.PRESHAPE
            elif self.phase in {Phase.SEARCH, Phase.RELOCALIZE}:
                self.phase = Phase.LOCATE_QR
            elif self.phase in {Phase.SAFE_STOP, Phase.SAFE_ABORT}:
                return self.phase
        self.history.append(self.phase.value)
        return self.phase

    def fail(self, reason: str) -> Phase:
        self.retries += 1
        mapping = {
            "GRASP_FAIL": Phase.RETRY_GRASP,
            "SLIP": Phase.REGRASP,
            "DECODE_FAIL": Phase.SEARCH,
            "WRONG_QR": Phase.RELOCALIZE,
            "COMM_FAULT": Phase.SAFE_STOP,
        }
        if self.retries > self.max_retries and reason != "COMM_FAULT":
            self.phase = Phase.SAFE_ABORT
        else:
            self.phase = mapping.get(reason, Phase.SAFE_ABORT)
        self.history.append(f"{reason}->{self.phase.value}")
        return self.phase
