# Codex Main-Venue Plan: medical_monitoring_r4_d02_cm_contract_20260811

Date: 2026-08-11
Objective: Freeze and independently review the isolated synthetic R4-D02 CM medication rationale, indication, prohibited/restricted medication coverage contract and implementation boundary without touching product, medical-writing, real-project, or frozen R1-R3 files

## Task Decomposition

1. Codex 从冻结共同矩阵、v1.1 设计/实施计划和已接受 D01 公共合同形成 D02 草案。
2. 两位参与者在隔离上下文中独立审阅整个草案，分别从医学和工程/身份/coverage 角度寻找反例，不互读输出。
3. Codex 对每项争议回到 source of truth，必要时修订草案并请求同会话定向复核。
4. 两条有效复核路线与 Codex 接受后冻结 D02 合同，记录摘要、review/metrics 和下一执行包边界。

## Source Packet

- v1.1 System Design 与 R0-R8 实施计划的 R4 范围。
- `FROZEN_R4_CONTRACT_V1` 共同合同和 D02 行。
- 已接受 D01 source/API 只用于公共合同兼容性审阅。
- `medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md` 草案。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_qwen38` | `alibaba` | `qwen3.8-max` | `runs/conference/medical_monitoring_r4_d02_cm_contract_20260811/general_pi_qwen38.md` |
| `general_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_monitoring_r4_d02_cm_contract_20260811/general_grok45.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex 复核所有反例是否与冻结矩阵、医学监查实际和公共 API 相符。
- Codex 决定适应证缺失、复方拆分、窗口端点和跨域证据共享的最终合同，不由多数票替代。
- 仅合同冻结后进入实现；不把合同会商等同于代码或产品完成。

## Timeout And Retry Tracking

- 每个角色单次启动，120 分钟硬等待；只在 terminal failure、不完整输出或具体可执行缺口时同会话续作/走声明 fallback。
- 北京日间 Qwen 精确节点由 runner 按全局策略替换为 `cms-smk/cms-model`；记录 declared/effective route。

## Codex Verification Checklist

- [x] 草案完整覆盖五类 L1、L1b、L2 计数和域完整性。
- [x] 复方、商品名、J07/活疫苗、部分日期、稳定/抢救/预防、CM/IP 分层均有明确 fail-closed 规则。
- [x] D02 风险 identity 与 D01 证据共享不复制风险/生命周期。
- [x] Query 为中文三段式，PD 仅核实；旅程为 CM 区间且域标记独立。
- [x] 公共 `RiskDomainUnitResult` 适配的行为保持要求、串行 owner 和 D01 224 回归门已冻结；实际不回归需下一执行包证明。
- [x] 两条独立有效路线完成；医学最终 `ACCEPT`，工程 `ACCEPT_WITH_GAPS` 的全部 G1-G6 已并入；review/metrics 已完成。
