# Task Context: monitoring_protocol_evidence_packet_v2

Created: 2026-07-30 06:10:42
Objective: 实现医学监查方案证据包 v2：邻接章节、表格同行/表头、连续列表、检索缺口、原文冲突、estimand领域门及CM/IP边界
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_p10_rux_protocol_candidate_scientific_audit_20260730.md`
- `services/api/app/monitoring_ai_source_packet.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/main.py`
- `tests/test_monitoring_ai_source_packet.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_service.py`
- 用户授权读取的 RUX-03-002 V1.3 原始 DOCX，仅用于只读真实形状探针。

## Scope

- In scope:
  - 命中段落的有界同章节邻接扩展；
  - 表标题、表头、同行条件和动作绑定；
  - 连续列表标题与条目绑定；
  - “方案未规定”与“证据包未检索到”的严格区分；
  - 同一触发条件、同一对象、同一动作的强制/可选原文冲突；
  - estimand 目标人群与入排规则的领域门；
  - 非试验用 CM 与试验药物变更的边界；
  - 后端与测试的最小通用实现。
- Out of scope:
  - 前端、医学写作、运行态数据库、运行服务重启；
  - 接受或驳回任何真实候选；
  - 重新生成 RUX 候选或发布规则；
  - 针对单一项目 locator、项目代码或固定段落写死逻辑。

## Success Criteria

- 真实形状测试覆盖停药需/可冲突、不同条件不误报、表格同行阈值、禁用列表、
  SAE 住院例外和访视表。
- RUX 原始方案只读探针必须同时保留 IGA 条件下需/可停药原文及表 4 同行条件/动作。
- 聚焦与相邻测试、Ruff、未定义名检查及 Python 编译全部通过。
- 主工作区仅提升已在隔离目录验收的后端和测试文件，并记录剩余风险和恢复边界。

## Risk Boundaries

- 先在 `/tmp/monitoring_protocol_evidence_packet_v2_20260730_0645` 隔离目录修改和验证，
  通过后再机械提升到主工作区。
- 不写运行态数据库，不重启 API，不触碰前端和医学写作。
- 结构扩展只增加可追溯证据，不作医学裁决；冲突必须并列保留给用户处理。
- Codex 以真实原始方案只读探针和主工作区回归作为最终验收证据。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 06:10:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30 06:13-06:25: 在隔离目录完成证据包 v2、提示词合同、确定性质量门与测试。
- 2026-07-30 06:26: 真实 RUX 探针发现“可停用”模态与“停用”动作重叠导致漏检；
  改为动作前瞻匹配后检出原文冲突。
- 2026-07-30 06:27: 进一步加入触发条件范围，避免把严重感染需停药与皮损清除后可停药
  误报为同一冲突。
- 2026-07-30 06:29: 隔离区 153 项聚焦、237 项相邻测试通过；Ruff 与编译通过。
- 2026-07-30 06:30: 目标文件修改时间均早于隔离切片创建，确认无并发改写后提升七个文件。
- 2026-07-30 06:31: 提升时一次多源 `rsync` 误把七个副本放到工作区根目录；立即核对、
  正确逐文件提升并删除全部误放副本。目标文件与隔离验收版本逐字节一致。
- 2026-07-30 06:32: 主工作区 239 项相邻回归、Ruff、F821 与 `py_compile` 通过。
- 2026-07-30 06:33: 主工作区真实 RUX 只读探针通过；未修改运行态或真实候选。
- 2026-07-30 06:35: review gate 通过；隔离目录已通过系统废纸篓安全清理，恢复依据已
  固化到 context、run、review、metrics、P10 ledger 和 handoff。
