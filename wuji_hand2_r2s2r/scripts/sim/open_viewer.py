#!/usr/bin/env python3
"""Open MuJoCo viewer even when the project sits under a non-ASCII path."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.sim.mujoco.loader import stage_mjcf_to_ascii_temp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mjcf",
        default=str(ROOT / "assets" / "wuji_hand2" / "mjcf" / "right.xml"),
        help="Path to MJCF file",
    )
    args = ap.parse_args()
    staged = stage_mjcf_to_ascii_temp(args.mjcf)
    print("Staged ASCII MJCF at:", staged)
    subprocess.check_call([sys.executable, "-m", "mujoco.viewer", f"--mjcf={staged}"])


if __name__ == "__main__":
    main()
