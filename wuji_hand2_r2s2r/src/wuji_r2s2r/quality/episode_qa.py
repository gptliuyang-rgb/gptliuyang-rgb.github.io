"""Episode-level data quality gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class QAReport:
    episode_id: str
    grade: str
    checks: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "grade": self.grade,
            "checks": self.checks,
            "failures": self.failures,
        }


def _ts_stats(ts_ns: np.ndarray) -> dict[str, float]:
    if len(ts_ns) < 2:
        return {"n": float(len(ts_ns))}
    dt_ms = np.diff(ts_ns.astype(np.float64)) / 1e6
    return {
        "n": float(len(ts_ns)),
        "mean_dt_ms": float(np.mean(dt_ms)),
        "median_dt_ms": float(np.median(dt_ms)),
        "p95_dt_ms": float(np.percentile(dt_ms, 95)),
        "p99_dt_ms": float(np.percentile(dt_ms, 99)),
        "jitter_ms": float(np.std(dt_ms)),
        "max_gap_ms": float(np.max(dt_ms)),
        "negative_dt": float(np.sum(dt_ms < 0)),
        "duplicate_ts": float(np.sum(dt_ms == 0)),
        "effective_hz": float(1000.0 / max(np.median(dt_ms), 1e-9)),
    }


def check_episode(
    episode_id: str,
    q: np.ndarray,
    dq: np.ndarray | None = None,
    timestamp_ns: np.ndarray | None = None,
    actions: np.ndarray | None = None,
    limit_lower: np.ndarray | None = None,
    limit_upper: np.ndarray | None = None,
) -> QAReport:
    failures: list[str] = []
    checks: dict[str, Any] = {}

    q = np.asarray(q, dtype=np.float64)
    if q.ndim != 2 or q.shape[1] != 20:
        failures.append("schema:q_shape")
        return QAReport(episode_id, "REJECT", checks, failures)

    checks["schema"] = {"ok": True, "T": int(q.shape[0]), "dof": 20}

    if np.isnan(q).any() or np.isinf(q).any():
        failures.append("joint:nan_or_inf")

    # constant / dead joints
    dead = np.where(np.std(q, axis=0) < 1e-8)[0].tolist()
    checks["dead_joints"] = dead

    if limit_lower is not None and limit_upper is not None:
        lo = np.asarray(limit_lower)
        hi = np.asarray(limit_upper)
        oob = np.logical_or(q < lo - 1e-3, q > hi + 1e-3).any(axis=0)
        checks["out_of_limit_joints"] = np.where(oob)[0].tolist()
        if oob.any():
            failures.append("joint:out_of_limit")

    if timestamp_ns is not None:
        ts = np.asarray(timestamp_ns)
        checks["timestamps"] = _ts_stats(ts)
        if checks["timestamps"].get("negative_dt", 0) > 0:
            failures.append("timestamp:non_monotonic")
        if checks["timestamps"].get("max_gap_ms", 0) > 200:
            failures.append("timestamp:large_gap")

    if actions is not None:
        a = np.asarray(actions)
        checks["actions"] = {"shape": list(a.shape), "nan": bool(np.isnan(a).any())}
        if a.shape[-1] != 20 or np.isnan(a).any():
            failures.append("action:invalid")

    # Grade
    if any(f.startswith("schema") for f in failures) or "joint:nan_or_inf" in failures:
        grade = "REJECT"
    elif failures:
        grade = "C" if len(failures) > 2 else "B"
    else:
        jitter = checks.get("timestamps", {}).get("jitter_ms", 0.0)
        grade = "A" if jitter <= 5.0 else "B"

    return QAReport(episode_id, grade, checks, failures)
