# Codex Execution Plan: mw_dynamic_chapter_projection_20260720

Objective: 为医学写作子系统建立设计驱动的动态章节事实投影和空章节治理，使StudyDefinition、方案摘要、正文、目录及AI候选保持一致且不编造临床事实

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 审计公司方案模板节点与StudyDefinition字段，提出通用语义投影矩阵和必需/条件/不适用/未知章节规则 | `runs/execution/mw_dynamic_chapter_projection_20260720/worker_01.md` |
| `worker_02` | 实现并测试已确认项目事实到章节正文初稿的确定性投影，严格限制写集为medical_writing_protocol_template.py及其专项测试 | `runs/execution/mw_dynamic_chapter_projection_20260720/worker_02.md` |
| `worker_03` | 对D017、RA、RUX三类研究定义做跨项目边缘案例测试，验证不适用/未知条件模块不产生空章节且必需章节有显式待补事实状态 | `runs/execution/mw_dynamic_chapter_projection_20260720/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_dynamic_chapter_projection_20260720/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
