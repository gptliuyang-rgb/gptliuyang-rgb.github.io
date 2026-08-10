# Wuji Hand 2 模型审计报告

**证据等级说明**：结论均标注证据标签；未连接真机处明确写明。

## 1. 官方文档与仓库入口

| 来源 | 用途 | 证据 |
|------|------|------|
| https://docs.wuji.tech/en/ | Docs Center | [Official-doc verified] |
| https://docs.wuji.tech/docs/en/wuji-hand/latest/overview/ | Hand 2 Beta 1 产品说明 | [Official-doc verified] |
| https://docs.wuji.tech/docs/en/wuji-hand/latest/usage-constraints/ | Beta 约束 | [Official-doc verified] |
| https://github.com/wuji-technology/wuji-description | 官方 URDF/MJCF/USD | [Official-doc verified] |

## 2. Hand 2 vs Hand（一代）

| 项目 | Wuji Hand 2 Beta 1 | Wuji Hand（一代） |
|------|--------------------|-------------------|
| 资产路径 | `hand2/hand2_beta1/body/` | `hand/body/` |
| 关节命名 | 解剖学（`r_thumb_cmc_flex` 等） | 不同命名体系 |
| 官方 mujoco-sim / MJLab / Isaac Lab 示例 | **不适用 / 未直接支持 Hand 2** | 适用 |
| 本仓库使用 | **仅 Hand 2 Beta 1** | 不作为数字孪生基础 |

**结论**：禁止用一代模型静默替代 Hand 2。[Official-doc verified]

## 3. 硬件修订核实

| 项 | 值 | 证据 |
|----|----|------|
| 修订 | Hand 2 Beta 1 | [Official-doc verified] |
| 主动自由度 | 20（5 指 × 4） | [Official-doc verified] |
| 控制 | MIT 力位混合，1000 Hz × 20 | [Official-doc verified] |
| 通信 | Ethernet 100BASE-TX | [Official-doc verified] |
| 指尖触觉 | **Beta 1 不提供**（Beta 2+） | [Official-doc verified] |
| 软体仿真模型 | **本版本未提供** | [Official-doc verified] |
| 本环境真机连接 | **未连接** | [Not yet verified] |

## 4. MJCF 审计（右侧）

来源：`assets/wuji_hand2/mjcf/right.xml`（自官方仓库复制）。

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 关节数 | 20 hinge | [Code verified] |
| 执行器数 | 20 position | [Code verified] |
| 根连杆 | `r_wrist` | [Code verified] |
| 指尖 site | 5（thumb/index/middle/ring/pinky） | [Code verified] |
| timestep | 0.002 s，RK4，Newton | [Code verified] |
| 单位 | radian | [Code verified] |
| 碰撞 | mesh + 10 组装配重叠 exclude | [Code verified] |

### 关节顺序（canonical = SDK finger-major）

0–3 thumb, 4–7 index, 8–11 middle, 12–15 ring, 16–19 pinky。

完整映射：`configs/hardware/joint_mapping.yaml`。[Code verified]

### 关节限位（rad，摘自 MJCF）

与官方文档角度范围一致（文档以度为展示，MJCF 为弧度）。[Official-doc verified][Code verified]

## 5. URDF / USD

- URDF：`assets/wuji_hand2/urdf/{left,right}.urdf`（及 `-ros`）
- USD：`assets/wuji_hand2/usd/{left,right}/wujihand2.usd`（分层 physics/robot/sensor）
- STEP：体积较大，未入库；见 `assets/wuji_hand2/SOURCE.md`

## 6. 仿真冒烟

`scripts/sim/smoke_test_hand2.py`：

- 模型加载成功，nq=nv=nu=20
- 关节名与 canonical mapping 一致
- 对 index MCP flex 施加目标后关节响应非零
- 指尖 site 位姿可读

**成熟度：SIM-L1（运动学/加载）已通过；SIM-L2+ 需真机轨迹。** [Simulation verified]

## 7. 策略含义

- 部署观测契约 **不得**要求触觉（Beta 1）。
- 数字孪生 v0.1 基于官方骨架 MJCF + 参数注册表先验；接触/延迟等需 R1 真机辨识。
