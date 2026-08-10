#!/usr/bin/env python3
"""Minimal training entry: BC on scripted sim data (P2) or residual stub."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.recording.episode_io import load_episode

def train_bc(episodes: list[Path], out: Path, steps: int = 200) -> dict:
    # Extremely small linear BC: action ≈ W @ [q, dq] + b  (demo infrastructure)
    Xs, Ys = [], []
    for p in episodes:
        ep = load_episode(p)
        q, dq, a = ep["q"], ep["dq"], ep["actions"]
        T = min(len(q), len(a))
        X = np.concatenate([q[:T], dq[:T]], axis=1)
        Xs.append(X); Ys.append(a[:T])
    X = np.concatenate(Xs); Y = np.concatenate(Ys)
    # ridge
    d = X.shape[1]
    W = np.linalg.lstsq(X.T @ X + 1e-3 * np.eye(d), X.T @ Y, rcond=None)[0]
    pred = X @ W
    rmse = float(np.sqrt(np.mean((pred - Y) ** 2)))
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, W=W)
    return {"family": "P2_sim_bc", "train_rmse": rmse, "n_samples": int(len(X)), "checkpoint": str(out)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/training/scanner.yaml")
    args = ap.parse_args()
    data = ROOT / "data" / "simulation" / "R2_TELEOP_DEMOS" / "scripted_v0"
    eps = sorted([p for p in data.glob("*") if (p / "timeseries.npz").exists()])
    if not eps:
        print("No sim dataset; run generate_sim_dataset.py")
        sys.exit(1)
    result = train_bc(eps, ROOT / "checkpoints" / "scanner_bc_v0.npz")
    (ROOT / "reports" / "train_scanner_bc_v0.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
