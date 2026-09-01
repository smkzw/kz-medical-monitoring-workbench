# Codex Execution Plan: mw_intervention_rules_discovery_20260717

Objective: 从第一性原理冻结M11 6.4试验药物剂量调整、6.9非试验用药治疗、6.10合并治疗的共享结构化事实模型和最小实现边界，严格区分IP处置与CM，并复用现有StudyDefinition、领域表、工作副本和医学监查规则底座

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 审计现有合同、API、StudyDefinition/PICOS、领域表、章节路由、版本一致性与DOCX链，提出最小兼容数据模型及迁移边界，不写产品代码 | `runs/execution/mw_intervention_rules_discovery_20260717/worker_01.md` |
| `worker_02` | 从RUX、D001、PNH三份原始方案重新提取IP剂量调整/暂停恢复/永久停药及CM允许禁用背景补救规则，形成跨项目反例驱动语义矩阵，不使用既有解构结果替代原文 | `runs/execution/mw_intervention_rules_discovery_20260717/worker_02.md` |
| `worker_03` | 审计医学写作与医学监查之间可复用的规则、事件和来源合同，设计双项目逐按钮/API/DOCX/视觉失败矩阵，防止IP与CM串扰和新旧代码冲突，不写产品代码 | `runs/execution/mw_intervention_rules_discovery_20260717/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_intervention_rules_discovery_20260717/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
