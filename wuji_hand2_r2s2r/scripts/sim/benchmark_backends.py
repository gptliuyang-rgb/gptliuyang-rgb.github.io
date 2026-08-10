#!/usr/bin/env python3
"""Benchmark MuJoCo CPU / MJX / MJWarp / Isaac Lab backends."""
from __future__ import annotations
import json, time, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.schema.types import HandAction
from wuji_r2s2r.sim.common.factory import make_backend

def bench(kind: str, n_steps: int = 500, n_envs: int = 1) -> dict:
    t0 = time.perf_counter()
    envs = [make_backend(kind, side="right") for _ in range(n_envs)]
    startup = time.perf_counter() - t0
    for e in envs:
        e.reset()
    action = HandAction(0, np.zeros(20))
    t1 = time.perf_counter()
    for _ in range(n_steps):
        for e in envs:
            e.command(action)
            e.step(1)
    elapsed = time.perf_counter() - t1
    total_steps = n_steps * n_envs
    diag = envs[0].diagnostics()
    for e in envs:
        e.close()
    return {
        "backend": kind,
        "n_envs": n_envs,
        "n_steps_per_env": n_steps,
        "startup_s": startup,
        "elapsed_s": elapsed,
        "steps_per_sec": total_steps / max(elapsed, 1e-9),
        "diagnostics": diag,
    }

def main():
    results = []
    for kind in ["mujoco", "mjx", "mjwarp", "isaaclab", "mock"]:
        for n_env in [1, 16]:
            try:
                r = bench(kind, n_steps=200 if n_env == 1 else 50, n_envs=n_env)
            except Exception as exc:  # noqa: BLE001
                r = {"backend": kind, "n_envs": n_env, "error": str(exc)}
            results.append(r)
            print(r)
    out = ROOT / "reports" / "backend_benchmark.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    # markdown table
    lines = ["| Backend | Envs | Steps/sec | Startup s | Notes |",
             "|---|---:|---:|---:|---|"]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['backend']} | {r['n_envs']} | - | - | error: {r['error'][:60]} |")
        else:
            note = r.get("diagnostics", {})
            lines.append(f"| {r['backend']} | {r['n_envs']} | {r['steps_per_sec']:.1f} | {r['startup_s']:.3f} | {json.dumps(note)[:80]} |")
    (ROOT / "reports" / "backend_benchmark.md").write_text("\n".join(lines) + "\n")
    print("Wrote", out)

if __name__ == "__main__":
    main()
