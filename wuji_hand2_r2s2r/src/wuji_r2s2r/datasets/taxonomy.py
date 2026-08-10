"""Dataset purpose taxonomy R0–R7."""

from __future__ import annotations

PURPOSES = [
    "R0_CALIBRATION",
    "R1_SYSTEM_ID",
    "R2_TELEOP_DEMOS",
    "R3_TASK_EVALUATION",
    "R4_POLICY_ROLLOUTS",
    "R5_FAILURES",
    "R6_RECOVERY",
    "R7_FACTORY_LONG_RUN",
]

SPLITS_SYSID = ["SYSID_TRAIN", "SYSID_VALIDATION", "SYSID_HOLDOUT"]
