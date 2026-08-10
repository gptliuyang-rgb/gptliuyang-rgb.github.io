| Backend | Envs | Steps/sec | Startup s | Notes |
|---|---:|---:|---:|---|
| mujoco | 1 | 14702.4 | 0.194 |  |
| mujoco | 16 | 13338.3 | 0.736 |  |
| mjx | 1 | 14848.7 | 0.027 | fallback_cpu:ModuleNotFoundError |
| mjx | 16 | 13425.4 | 0.454 | fallback_cpu:ModuleNotFoundError |
| mjwarp | 1 | 14769.9 | 0.025 | warp=False |
| mjwarp | 16 | 13340.3 | 0.457 | warp=False |
| isaaclab | 1 | 201110.9 | 0.013 | isaac=False (mock fallback) |
| isaaclab | 16 | 223049.3 | 0.187 | isaac=False (mock fallback) |
| mock | 1 | 222950.0 | 0.011 |  |
| mock | 16 | 225003.1 | 0.176 |  |
