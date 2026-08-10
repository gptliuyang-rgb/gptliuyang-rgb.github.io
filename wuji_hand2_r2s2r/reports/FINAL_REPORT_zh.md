# 最终报告：Wuji Hand 2 Real2Sim2Real 平台

## 1. 执行摘要

已在本仓库实现并可执行一套面向 **Wuji Hand 2 Beta 1** 的 Real2Sim2Real 软件平台：官方 Hand 2 资产审计与入库、统一 `HandBackend` 接口、参数注册表、数据质检、系统辨识框架、MuJoCo 数字孪生与扫码枪场景、Real→Sim 回放、ID 派生域随机化、脚本/BC 训练、Sim2Sim 门控、Shadow 部署接口，以及中文报告与复现命令。

**真机**：当前环境 **未连接** Wuji Hand 2。真机采集/部署以 dry-run/接口实现，结论标注 `[Not yet verified]`。

**当前成熟度**：仿真侧 SIM-L0/L1 通过；孪生 v0.1 在合成自由空间 holdout 上回放 RMSE≈0.014 rad；工厂 PoC 物理门控未放行。

## 2. Wuji Hand 2 硬件与版本核实

详见 `reports/00_hand2_model_audit_zh.md`。

- 修订：**Hand 2 Beta 1**，20 DoF，解剖学命名，坐标约定冻结。[Official-doc verified]
- 触觉：**无**（Beta 1）。[Official-doc verified]
- 本机硬件：未连接。[Not yet verified]

## 3. 仿真器选型结论

在本机实测（Hand 2 官方 MJCF，1/16 环境串行步进）：

| Criterion | MuJoCo CPU | MJX | MJWarp | Isaac Lab |
|-----------|----------:|----:|-------:|----------:|
| Hand2 模型集成 | 通过 | API 回退 CPU | API 回退 CPU | USD 已备，运行时未安装 |
| 1-env 吞吐 (steps/s) | ~1.47e4 | ~1.48e4* | ~1.48e4* | ~2.0e5† |
| 16-env 吞吐 | ~1.33e4 | ~1.34e4* | ~1.33e4* | ~2.2e5† |
| 真机回放保真 | 规范后端 | 待 GPU MJX | 待 Warp | 待 PhysX |
| 可调试性 | 最高 | 中 | 中 | 低（本环境） |

\* JAX/Warp 未安装，回退 MuJoCo CPU。† Isaac 未安装，**mock 回退**，吞吐不可比。

**决策**：MuJoCo CPU 作为规范数字孪生；MJWarp/MJX 作为后续 GPU 并行候选；Isaac Lab 保留为交叉验证与视觉合成后端。[Simulation verified][Not yet verified]

## 4. Hand 2 Digital Twin

- 版本：`hand2_twin_v0.1`
- 资产：官方 `hand2_beta1` MJCF + `assets/scanner/scanner_scene_right.xml`
- 参数注册表：`configs/system_id/parameter_registry.yaml`
- 验证：关节映射一致；自由空间合成轨迹 Real→Sim RMSE（holdout mean）≈ **0.0136 rad**。[Simulation verified]

## 5. Real 数据采集

| 数据集 | 状态 |
|--------|------|
| R0 标定 | 接口就绪，无真机数据 |
| R1 系统辨识 | 已生成 **仿真** 自由空间轨线（train/val/holdout） |
| R2 teleop demos | 已生成 5 条脚本策略仿真 episode |
| R3–R7 | 目录与 taxonomy 就位，待真机 |

## 6. 数据质量系统

- 模块：`wuji_r2s2r.quality.episode_qa`
- 等级：A/B/C/REJECT（`configs/data_quality/grades.yaml`）
- 合成 episode 质检：结构与时间戳检查通过。[Code verified]

## 7. 系统辨识

| Parameter | Before | Identified | Confidence | Evidence |
|-----------|-------:|-----------:|------------|----------|
| actuator delay_ms | 8.0 prior | grid best 0.0 on synthetic (same-source) | low | [Simulation verified] 非真机 |
| finger friction | 0.8 prior | 未真机拟合 | low | [Not yet verified] |
| scanner mass | 0.18 prior | 未称重 | low | [Not yet verified] |

说明：同源仿真回放会低估延迟；真机 R1 后再更新孪生版本。

## 8. Real→Sim Replay

| Episode | q RMSE | Scanner Pose Error | Contact Error | Result |
|---------|-------:|-------------------:|--------------:|--------|
| sysid holdout_020 | ≈0.0135 | N/A（自由空间） | N/A | pass proxy |
| sysid holdout_021 | ≈0.0137 | N/A | N/A | pass proxy |

图：`reports/figures/real_vs_sim_joint_position.png`

## 9. Digital Twin Holdout

`holdout_mean_q_rmse ≈ 0.0136`（合成数据）。[Simulation verified]  
真机 holdout：**未测**。[Not yet verified]

## 10. Domain Randomization

版本 `dr_v0.1`，由不确定度区间派生。覆盖检查见 `reports/dr_coverage.json`（名义值均落在 DR 内）。图：`reports/figures/param_vs_dr_range.png`

## 11. Simulation Training

| Policy | 结果 |
|--------|------|
| P0 scripted | FSM 可达 SUCCESS（代理指标） |
| P2 sim BC | train RMSE ≈ 0.0053，checkpoint `checkpoints/scanner_bc_v0.npz` |

## 12. Sim Evaluation

脚本策略 proxy success rate = **1.0**（n=5，decode 为几何代理，非光学固件）。[Simulation verified]

## 13. Sim2Sim Evaluation

MuJoCo vs IsaacLab-接口：Isaac 未安装 → mock 回退，分歧 RMSE≈0.019。完整 PhysX 交叉验证 **未完成**。[Not yet verified]

## 14. Real Shadow Evaluation

Shadow 路径在 MuJoCo 替身上跑通；观测/动作契约校验启用；**无真机**。[Code verified]

## 15. Real Scanner PoC

| Subtask | Attempts | Successes | Rate |
|---------|---------:|----------:|-----:|
| 全部真机子任务 | 0 | 0 | N/A |

门控：`allowed_full_poc = false`（缺 G5–G10 真机条件）。

## 16. Sim-vs-Real

无真机成功图；仅有仿真成功代理。Gap **无法计算**。[Not yet verified]

## 17. Failure Analysis

尚无真机失败样本。仿真侧失败挖掘管道：`task_graph` + episode labels 已就绪。

## 18. R2S2R Improvement

| Iteration | Twin Error | Sim Success | Real Success |
|-----------|----------:|------------:|-------------:|
| R2S2R_000 | ≈0.014 (synth) | 1.0 proxy | N/A |

## 19. 数据质量结论

仿真数据足以支撑 **软件管道回归**；不足以支撑工厂策略训练。需要真机 R0/R1/R2。

## 20. 工厂部署成熟度（0–5）

| 维度 | 分 |
|------|---|
| Hardware | 1（资产/接口，无真机） |
| Data Collection | 2 |
| Data QA | 3 |
| Calibration | 1 |
| System ID | 2 |
| Digital Twin | 2 |
| Domain Randomization | 3 |
| Training | 2 |
| Sim Validation | 3 |
| Sim2Sim | 1 |
| Real Deployment | 1 |
| Scanner Grasp | 1 |
| QR Scan | 1（代理） |
| Recovery | 2（FSM） |
| Long-run Reliability | 0 |

## 21. 尚未完成

- 真机连接、标定、R1 激励轨迹
- 接触/扫码枪物理辨识
- MJX/MJWarp GPU 批仿真实装
- Isaac Lab 完整环境
- 教师-学生蒸馏与残差策略大规模训练
- 光学解码经验概率模型
- 工厂长跑

## 22. 下一轮优先级

- **P0**：连接 Hand 2，跑 R0/R1，更新 `hand2_twin_v0.2`
- **P0**：真机 free-space Real→Sim 回放与延迟辨识
- **P1**：扫码枪称重/摩擦/扳机实验 E1–E5
- **P1**：安装 Isaac Lab 做交叉验证
- **P2**：GPU MJWarp 吞吐 bake-off；残差策略

## 23. 完整复现命令

```bash
cd wuji_hand2_r2s2r
pip install -e ".[dev]"
python3 scripts/sim/smoke_test_hand2.py
python3 scripts/sim/benchmark_backends.py
python3 scripts/sim/evaluate_twin.py
python3 scripts/sysid/fit.py
python3 scripts/sysid/build_randomization.py
python3 scripts/collect/generate_sim_dataset.py
python3 scripts/train/train.py
python3 scripts/evaluate/eval_sim.py
python3 scripts/evaluate/eval_cross_sim.py
python3 scripts/deploy/run_policy.py --mode shadow
python3 -m pytest -q
```

## 24. 文件清单

- 代码：`src/wuji_r2s2r/**`
- 资产：`assets/wuji_hand2/**`, `assets/scanner/**`
- 配置：`configs/**`
- 报告：`reports/**`
- 数据：`data/simulation/**`

## 25. 最终判断

1. **MuJoCo 数字孪生是否验证？** SIM-L1 是；SIM-L2+ 对真机 **否**。[Simulation verified]/[Not yet verified]
2. **仿真预测真机精度？** 未知（无真机）。[Not yet verified]
3. **主导 Sim2Real gap 的参数？** 先验指向接触摩擦、延迟、扫码枪惯性——待辨识。[Not yet verified]
4. **ID 派生 DR 是否提升真机？** 未测。[Not yet verified]
5. **交叉仿真是否淘汰脆弱策略？** 接口有，PhysX 未跑。[Not yet verified]
6. **全自动 R2S2R 闭环？** 软件闭环可跑；真机闭环未运行。[Code verified]
7. **真机扫码成功率？** N/A。[Not yet verified]
8. **距工厂部署还差什么？** 真机数据、接触级孪生、安全门控 G6–G10、长跑可靠性。
