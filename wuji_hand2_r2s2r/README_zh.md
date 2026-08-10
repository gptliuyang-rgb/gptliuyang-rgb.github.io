# Wuji Hand 2 Real2Sim2Real 平台

面向 Wuji Hand 2 的闭环 **真机数据 → 数据质检 → 系统辨识 → MuJoCo 数字孪生 → 训练 → Sim2Sim → 真机部署 → 失败挖掘** 基础设施。

工业 PoC：抓取手持扫码枪 → 稳定抓取抬起 → 扣动扳机 → 对准纸箱二维码 → 解码校验 → 智能重试。

## 重要核实

- Hand 2 Beta 1：20 主动自由度，解剖学关节命名，坐标约定自 Beta 1 冻结。
- 官方资产：`wuji-description` 的 `hand2/hand2_beta1`（MJCF/URDF/USD/STEP），**不是**一代 Wuji Hand。
- 一代仓库 `mujoco-sim` / `Wuji MJLab` / Isaac Lab 示例默认针对 **Wuji Hand**，不可静默替换为 Hand 2。
- Beta 1 **无指尖触觉**；软体仿真模型尚未提供。
- 本环境未连接真机，已完成仿真侧可执行闭环；真机步骤以接口/干跑实现并标注证据等级。

详细结论见 `reports/FINAL_REPORT_zh.md` 与 `reports/00_hand2_model_audit_zh.md`。
