"""CLI entrypoints."""

from __future__ import annotations


def diagnose_main() -> None:
    from scripts.hardware import diagnose_hand  # type: ignore


def replay_main() -> None:
    print("Use: python3 scripts/sim/replay_real_episode.py --episode <path>")
