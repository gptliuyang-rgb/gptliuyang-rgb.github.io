"""Resolve repository root from any package module depth."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return wuji_hand2_r2s2r/ directory."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "assets" / "wuji_hand2").exists() and (parent / "configs").exists():
            return parent
    raise RuntimeError("Could not locate repository root")
