#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wuji_r2s2r.recording.episode_io import load_episode
from wuji_r2s2r.quality.episode_qa import check_episode
from wuji_r2s2r.schema.joint_mapping import JointMapping

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    args = ap.parse_args()
    ep = load_episode(args.episode)
    m = JointMapping()
    report = check_episode(Path(args.episode).name, ep["q"], ep.get("dq"), ep.get("timestamp_ns"), ep.get("actions"),
                           np.array(m.limit_lower()), np.array(m.limit_upper()))
    print(json.dumps(report.to_dict(), indent=2))

if __name__ == "__main__":
    main()
