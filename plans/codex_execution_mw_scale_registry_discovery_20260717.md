# Codex Execution Plan: mw_scale_registry_discovery_20260717

Objective: 为医学写作子系统设计可生产落地的量表/评估工具注册能力：结合现有 StudyDefinition、真实中国临床试验方案中的量表使用、以及权威来源和授权/中文版本边界，输出供 Codex 实现的事实清单与接口建议；不得修改生产代码。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 审计现有后端和前端代码：定位 StudyDefinition、终点、访视/SoA、证据语料、文档导出与UI入口，提出最小兼容的数据模型和联动点，列出文件与行号。 | `runs/execution/mw_scale_registry_discovery_20260717/worker_01.md` |
| `worker_02` | 从 RUX-03-002、D001、PNH 三个真实方案原始 DOCX 重新提取量表/评分工具实例，记录名称、版本、语言、用途、终点/访视关联、方案定位和任何附件/评分描述；不得沿用已解构结果。 | `runs/execution/mw_scale_registry_discovery_20260717/worker_02.md` |
| `worker_03` | 调研常见临床试验量表的权威来源、中文版本和授权边界，优先覆盖 RUX/D001/PNH 中实际出现的工具；区分可存元数据、可链接、可全文再现、需许可、需医学确认的状态，并给出可核查来源。 | `runs/execution/mw_scale_registry_discovery_20260717/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_scale_registry_discovery_20260717/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
