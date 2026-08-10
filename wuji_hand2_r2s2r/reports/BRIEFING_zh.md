# Wuji Hand 2 Real2Sim2Real 项目简报（可外发）

> 版本：R2S2R_000 / digital twin `hand2_twin_v0.1`  
> 日期：2026-08-10  
> 代码与完整报告：仓库目录 `wuji_hand2_r2s2r/`  
> PR：https://github.com/gptliuyang-rgb/gptliuyang-rgb.github.io/pull/1

---

## 一、一句话结论

已建成并跑通 **以真机为真相源、以 MuJoCo 为规范数字孪生** 的 Wuji Hand 2 Real2Sim2Real **软件闭环**；本轮环境 **未连接真机**，仿真侧验证到 **SIM-L1**，工厂扫码 PoC 物理部署 **尚未放行**。

---

## 二、上轮工作回顾（摘要）

### 做了什么

1. **官方核实**：确认使用 Wuji Hand 2 **Beta 1** 资产（`hand2/hand2_beta1`），禁止用一代 Hand 模型替代。
2. **平台落地**：在 `wuji_hand2_r2s2r/` 实现采集→质检→辨识→孪生→训练→门控→部署接口全链路。
3. **仿真执行**：MuJoCo 冒烟、后端吞吐对比、自由空间回放、脚本/BC 基线、Shadow 干跑。
4. **产物入库**：代码、官方 MJCF/URDF/USD、仿真数据、图表、中文报告已推 GitHub。

### 关键实测数字

| 指标 | 数值 | 证据等级 |
|------|------|----------|
| 主动自由度 | 20 | [Official-doc verified] |
| 关节映射一致性 | 通过 | [Code verified] |
| MuJoCo 1-env 吞吐 | ~1.47×10⁴ steps/s | [Simulation verified] |
| Holdout 关节位置 RMSE | ≈0.014 rad（合成数据） | [Simulation verified] |
| 脚本策略代理成功率 | 1.0（n=5，几何解码代理） | [Simulation verified] |
| 单元/集成测试 | 8/8 通过 | [Code verified] |
| 真机扫码成功率 | N/A（未连接） | [Not yet verified] |

### 重要约束（官方）

- Beta 1 **无指尖触觉**；软体仿真模型 **尚未提供**。
- 一代仓库 `mujoco-sim` / Wuji MJLab / Isaac Lab 示例默认针对 **Wuji Hand**，不能静默当作 Hand 2。

---

## 三、架构与选型

```
真机 (真相源) → 数据湖 → 质检 → SysID → 数字孪生 → Real→Sim 回放
                                              ↓
                                    ID 派生域随机化 → 训练
                                              ↓
                              MuJoCo 规范  +  Isaac Lab 交叉验证
                                              ↓
                                    Shadow → 受限真机 → 工厂 PoC
                                              ↓
                                         失败挖掘 → 回流
```

| 后端 | 角色 | 本环境状态 |
|------|------|------------|
| **MuJoCo CPU** | 规范孪生 / SysID / 回放 | 已跑通 |
| MJX / MJWarp | GPU 并行候选 | 未装，回退 CPU |
| Isaac Lab | 交叉验证 / 视觉合成 | 未装，mock 回退 |

---

## 四、扫码枪 PoC 状态机

`READY → 定位扫码枪 → 接近 → 预抓形 → 抓取 → 验抓 → 抬起 → 定位二维码 → 瞄准 → 扳机 → 验码 → SUCCESS`  
失败恢复：`RETRY_GRASP / REGRASP / SEARCH / RELOCALIZE / SAFE_STOP`

当前：**仿真脚本基线可走通状态机**；真机子任务 Attempts=0。

---

## 五、工厂成熟度（0–5）

| 维度 | 分 | 说明 |
|------|---|------|
| Hardware | 1 | 资产与接口有，真机未连 |
| Data QA | 3 | 规则与等级已实现 |
| Digital Twin | 2 | SIM-L1；接触级未验 |
| Training | 2 | P0/P2 基线 |
| Real Deployment | 1 | Shadow 接口 only |
| QR Scan（真机） | 0–1 | 仅几何代理 |
| Long-run | 0 | 未做 |

---

## 六、下一轮优先级

- **P0**：连接 Hand 2；采集 R0 标定 + R1 自由空间/延迟；更新 `hand2_twin_v0.2`
- **P0**：真机 Real→Sim 回放（非合成数据）
- **P1**：扫码枪称重/摩擦/扳机实验；安装 Isaac Lab 交叉验证
- **P2**：MJWarp GPU bake-off；残差策略与混合真机微调

---

## 七、报告材料索引

| 材料 | 路径 | 用途 |
|------|------|------|
| **完整终稿（25 章）** | `wuji_hand2_r2s2r/reports/FINAL_REPORT_zh.md` | 正式技术报告 |
| **本简报** | `wuji_hand2_r2s2r/reports/BRIEFING_zh.md` | 汇报/外发摘要 |
| **模型审计** | `wuji_hand2_r2s2r/reports/00_hand2_model_audit_zh.md` | Hand2 vs Hand、关节核对 |
| **迭代记录** | `wuji_hand2_r2s2r/reports/iterations/R2S2R_000_zh.md` | 第 0 轮变更 |
| **中文 README** | `wuji_hand2_r2s2r/README_zh.md` | 项目入口 |
| 后端对比表 | `reports/backend_benchmark.md` | 选型数据 |
| 孪生评估 JSON | `reports/twin_evaluation.json` | holdout RMSE |
| 图：关节回放 | `reports/figures/real_vs_sim_joint_position.png` | 汇报插图 |
| 图：DR 覆盖 | `reports/figures/param_vs_dr_range.png` | 汇报插图 |
| 图：吞吐 | `reports/figures/backend_throughput.png` | 汇报插图 |

---

## 八、对 8 个核心问题的回答

1. **孪生是否验证？** 仅到 SIM-L1；真机 SIM-L2+ **否**。  
2. **仿真预测真机精度？** 未知（无真机）。  
3. **主导 gap 参数？** 先验：接触摩擦、延迟、扫码枪惯性——待辨识。  
4. **ID 派生 DR 是否提升真机？** 未测。  
5. **交叉仿真是否淘汰脆弱策略？** 接口有，PhysX 未跑。  
6. **全自动闭环是否运转？** 软件闭环可跑；真机闭环未运行。  
7. **真机扫码成功率？** N/A。  
8. **距工厂部署差什么？** 真机数据、接触级孪生、门控 G6–G10、长跑可靠性。

---

## 九、复现命令

```bash
cd wuji_hand2_r2s2r
pip install -e ".[dev]"
python3 scripts/sim/smoke_test_hand2.py
python3 scripts/sim/benchmark_backends.py
python3 scripts/sim/evaluate_twin.py
python3 scripts/collect/generate_sim_dataset.py
python3 scripts/train/train.py
python3 scripts/evaluate/eval_sim.py
python3 scripts/deploy/run_policy.py --mode shadow
python3 -m pytest -q
```
