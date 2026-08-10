#!/usr/bin/env python3
"""Replay a recorded episode open-loop in simulation."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wuji_r2s2r.recording.episode_io import load_episode
from wuji_r2s2r.sim.mujoco.replay import replay_episode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True, help="episode directory")
    ap.add_argument("--backend", default="mujoco")
    args = ap.parse_args()
    ep = load_episode(args.episode)
    q_sim, metrics = replay_episode(ep["q"], ep["actions"], ep.get("timestamp_ns"), backend=args.backend)
    out = Path(args.episode) / f"replay_{args.backend}.json"
    out.write_text(json.dumps(metrics.to_dict(), indent=2))
    np.savez_compressed(Path(args.episode) / f"replay_{args.backend}_q.npz", q_sim=q_sim)
    print(json.dumps(metrics.to_dict(), indent=2))

if __name__ == "__main__":
    main()
