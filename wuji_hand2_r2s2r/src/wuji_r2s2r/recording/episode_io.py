"""Episode IO with provenance."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from wuji_r2s2r.schema.types import EpisodeMetadata


def save_episode(
    out_dir: str | Path,
    metadata: EpisodeMetadata,
    q: np.ndarray,
    dq: np.ndarray,
    effort: np.ndarray,
    actions: np.ndarray,
    timestamp_ns: np.ndarray,
    labels: dict[str, Any] | None = None,
    privileged: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ep_dir = out_dir / metadata.episode_id
    ep_dir.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        ep_dir / "timeseries.npz",
        q=np.asarray(q),
        dq=np.asarray(dq),
        effort=np.asarray(effort),
        actions=np.asarray(actions),
        timestamp_ns=np.asarray(timestamp_ns),
    )
    meta = {
        **metadata.__dict__,
        "saved_at": time.time(),
        "labels": labels or {},
        "privileged_keys": list((privileged or {}).keys()),
        "extra": extra or {},
    }
    (ep_dir / "metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    if privileged:
        np.savez_compressed(ep_dir / "privileged.npz", **{k: np.asarray(v) for k, v in privileged.items()})
    return ep_dir


def load_episode(ep_dir: str | Path) -> dict[str, Any]:
    ep_dir = Path(ep_dir)
    ts = np.load(ep_dir / "timeseries.npz")
    meta = json.loads((ep_dir / "metadata.json").read_text())
    out = {"metadata": meta, **{k: ts[k] for k in ts.files}}
    priv = ep_dir / "privileged.npz"
    if priv.exists():
        p = np.load(priv)
        out["privileged"] = {k: p[k] for k in p.files}
    return out
