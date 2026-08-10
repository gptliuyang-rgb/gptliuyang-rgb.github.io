#!/usr/bin/env python3
"""Placeholder: collect R0 calibration when hardware is available."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
out = ROOT / "data" / "calibration" / "pending_hand_mount_v0.json"
out.write_text(json.dumps({
    "status": "awaiting_hardware",
    "calibration_version": "hand_mount_v0_pending",
    "fields": [
        "robot_base_transform",
        "hand_mount_transform",
        "camera_intrinsics",
        "camera_extrinsics",
        "scanner_cad_frame",
        "box_qr_frames",
    ],
    "evidence": "[Not yet verified]",
}, indent=2))
print("Wrote", out)
