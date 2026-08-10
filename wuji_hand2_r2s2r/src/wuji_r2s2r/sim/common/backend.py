"""Unified HandBackend interface for real and simulated hands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from wuji_r2s2r.schema.types import HandAction, HandObservation


class HandBackend(ABC):
    """Semantic interface shared by real robot and all simulators."""

    name: str = "base"

    @abstractmethod
    def reset(self, qpos=None, **kwargs) -> HandObservation:
        ...

    @abstractmethod
    def observe(self) -> HandObservation:
        ...

    @abstractmethod
    def command(self, action: HandAction) -> None:
        ...

    @abstractmethod
    def step(self, n: int = 1) -> HandObservation:
        ...

    @abstractmethod
    def diagnostics(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
