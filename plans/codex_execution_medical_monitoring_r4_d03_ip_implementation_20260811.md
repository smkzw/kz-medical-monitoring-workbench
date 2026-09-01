# Codex Execution Plan: medical_monitoring_r4_d03_ip_implementation_20260811

Objective: 实现已接受 FROZEN_R4_D03_CONTRACT_V1_1 的合成离线研究药暴露、依从性、处置关系与 renderer-neutral Patient Journey 纵切，并保持 D01/D02 不回归

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 ip.py：D03 输入合同、expected-set、六类评价、Query、coverage/lifecycle 适配及聚焦测试 | `runs/execution/medical_monitoring_r4_d03_ip_implementation_20260811/worker_01.md` |
| `worker_02` | 实现 ip_projection.py：typed 访视轴事件、六类风险 marker、稳定双向 join 及投影测试 | `runs/execution/medical_monitoring_r4_d03_ip_implementation_20260811/worker_02.md` |
| `worker_03` | 实现 ip_fixtures.py、挑战矩阵、根包导出和跨域/相邻回归测试；不修改产品或医学写作路径 | `runs/execution/medical_monitoring_r4_d03_ip_implementation_20260811/worker_03.md` |

执行顺序固定为 `worker_01 → worker_02 → worker_03 → manager`。共享 workspace 不并行写入；每个后续 worker 只读取已完成前序产物。

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r4_d03_ip_implementation_20260811/manager.md` |

## Codex Acceptance

Codex 逐文件审查变更，运行 D03 聚焦测试、R4/R2/R3 全量回归、Ruff、compileall、公共导入/对象身份、确定性与 8911 停止检查；随后由独立 reviewer 接受稳定哈希快照。任何 worker 自报通过不构成接受。
