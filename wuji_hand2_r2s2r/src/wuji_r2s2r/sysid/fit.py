"""Hierarchical system identification fitting."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from wuji_r2s2r.sim.mujoco.replay import replay_episode
from wuji_r2s2r.sysid.registry import ParameterRegistry


def free_space_objective(
    q_real: np.ndarray,
    actions: np.ndarray,
    backend: str = "mujoco",
) -> float:
    _, metrics = replay_episode(q_real, actions, backend=backend)
    return metrics.joint_position_RMSE


def fit_delay_grid(
    q_real: np.ndarray,
    actions: np.ndarray,
    delays_ms: list[float] | None = None,
    backend: str = "mock",
) -> dict[str, Any]:
    """Coarse delay search using action shifting (proxy for command delay)."""
    delays_ms = delays_ms or [0, 4, 8, 12, 16, 20]
    best = {"delay_ms": 0.0, "rmse": float("inf")}
    results = []
    dt = 0.02
    for d in delays_ms:
        shift = int(round((d / 1000.0) / dt))
        if shift <= 0:
            a = actions
            q = q_real
        else:
            a = actions[:-shift]
            q = q_real[shift : shift + len(a)]
        if len(q) < 5:
            continue
        rmse = free_space_objective(q, a, backend=backend)
        results.append({"delay_ms": d, "rmse": rmse})
        if rmse < best["rmse"]:
            best = {"delay_ms": float(d), "rmse": float(rmse)}
    return {"best": best, "grid": results}


def fit_with_optuna(
    objective: Callable[[dict[str, float]], float],
    search_space: dict[str, tuple[float, float]],
    n_trials: int = 30,
    seed: int = 0,
) -> dict[str, Any]:
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        # Fallback random search
        rng = np.random.default_rng(seed)
        best_p, best_v = {}, float("inf")
        history = []
        for _ in range(n_trials):
            p = {k: float(rng.uniform(lo, hi)) for k, (lo, hi) in search_space.items()}
            v = float(objective(p))
            history.append({"params": p, "value": v})
            if v < best_v:
                best_p, best_v = p, v
        return {"best_params": best_p, "best_value": best_v, "history": history, "optimizer": "random"}

    def _obj(trial: "optuna.Trial") -> float:
        p = {k: trial.suggest_float(k, lo, hi) for k, (lo, hi) in search_space.items()}
        return float(objective(p))

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(_obj, n_trials=n_trials)
    return {
        "best_params": study.best_params,
        "best_value": float(study.best_value),
        "optimizer": "optuna",
        "n_trials": n_trials,
    }


def update_registry_from_fit(reg: ParameterRegistry, fit: dict[str, Any], new_version: str) -> ParameterRegistry:
    data = dict(reg.data)
    best = fit.get("best_params") or fit.get("best") or {}
    if "delay_ms" in best:
        data.setdefault("hand", {}).setdefault("actuator", {}).setdefault("delay_ms", {})
        data["hand"]["actuator"]["delay_ms"]["nominal"] = float(best["delay_ms"])
        data["hand"]["actuator"]["delay_ms"]["confidence"] = "medium"
        data["hand"]["actuator"]["delay_ms"]["source"] = ["sysid_fit"]
    return reg.clone_with_updates({"hand": data.get("hand", reg.data["hand"])}, new_version)
