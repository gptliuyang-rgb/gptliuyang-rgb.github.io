#!/usr/bin/env python3
"""Full scanner PoC runner (simulation until real gates pass)."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.safety.gates import GateStatus, GATES

def main():
    gates = GateStatus()
    # Software-only progress
    for g in GATES[:5]:
        gates.set(g, True if g != "G5_cross_sim" else False, "see reports/")
    allowed = gates.can_proceed_to("G10_full_factory_poc")
    out = {
        "allowed_full_poc": allowed,
        "gates": gates.to_dict(),
        "message": "Physical scanner PoC blocked until real hardware gates G6–G9 pass",
        "evidence": "[Not yet verified] physical deployment",
    }
    path = ROOT / "reports" / "scanner_poc_gate.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
