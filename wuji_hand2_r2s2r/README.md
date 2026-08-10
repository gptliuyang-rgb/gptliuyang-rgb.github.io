# Wuji Hand 2 Real2Sim2Real Platform

Closed-loop **Real → Data QA → System ID → MuJoCo Digital Twin → Training → Sim2Sim → Real Deploy → Failure Mining** infrastructure for the Wuji Hand 2 dexterous hand.

PoC task: acquire a handheld QR/barcode scanner, grasp, lift, trigger, align to a box QR, decode, verify, retry.

## Key facts (verified against official docs)

| Item | Status | Evidence |
|------|--------|----------|
| Hand 2 Beta 1 = 20 DoF anatomical joints | Yes | [Official-doc verified] |
| Official MJCF/URDF/USD under `hand2/hand2_beta1` | Vendored in `assets/wuji_hand2` | [Official-doc verified] |
| Gen-1 `mujoco-sim` / `MJLab` / Isaac Lab demos target **Wuji Hand**, not Hand 2 | Do not substitute | [Official-doc verified] |
| Beta 1 fingertip tactile | **Not provided** | [Official-doc verified] usage-constraints |
| Soft-body sim model | **Not provided** for Beta 1 | [Official-doc verified] |
| Physical hand in this environment | Not connected | [Not yet verified] |

Canonical physics backend: **MuJoCo CPU**. MJX / MJWarp / Isaac Lab are optional parallel/cross-sim backends.

## Quick start

```bash
cd wuji_hand2_r2s2r
pip install -e ".[dev]"
python scripts/hardware/diagnose_hand.py --backend mujoco
python scripts/sim/smoke_test_hand2.py
python scripts/sim/benchmark_backends.py
python scripts/sim/evaluate_twin.py
python scripts/sysid/fit.py
python scripts/sysid/build_randomization.py
python scripts/collect/generate_sim_dataset.py
python scripts/train/train.py
python scripts/evaluate/eval_sim.py
python scripts/evaluate/eval_cross_sim.py
python scripts/deploy/run_policy.py --mode shadow
pytest -q
```

## Layout

See repository tree under `configs/`, `assets/`, `src/wuji_r2s2r/`, `scripts/`, `reports/`.

## Chinese report

See `reports/FINAL_REPORT_zh.md` and `README_zh.md`.

## License

Code: MIT. Official Wuji assets retain their upstream MIT license (`assets/wuji_hand2/LICENSE.wuji-description`).
