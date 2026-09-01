# Conference Context: monitoring_p7_loop1

Created: 2026-07-29 16:59:45
Objective: 独立审阅P7日常医学监查运行台账、批次输入绑定、独立AI门禁与最终医学确认设计，返回冲突点和风险点
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3-256k`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/medical_monitoring_goal_p7_20260729/TASK_CONTEXT.md`
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`
- `docs/medical_monitoring_manual/医学监查子系统说明书_优化版.md`
- `records/active_slices/medical_monitoring_goal_p6_20260729/P6_LOOP2_IMPLEMENTATION_AND_REAL_PROJECT_ACCEPTANCE.md`
- `services/api/app/monitoring_batch_repository.py`
- `services/api/app/monitoring_batch_service.py`
- `services/api/app/monitoring_batch_diff.py`
- `services/api/app/medical_monitoring_summary.py`
- `services/api/app/medical_monitoring_router.py`
- `services/api/app/medical_risk_repository.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/ai_role_runtime_settings.py`
- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`
- 当前 SQLite 状态、API 响应和测试均是实现事实；文档中的完成表述不能覆盖运行证据。

## Scope

- In scope：识别 P7 批次运行台账、输入身份、幂等/CAS/重启恢复、diff、规则与独立 AI
  编排、风险快照、医学确认基线和前端进度之间的冲突、遗漏和最小可靠连接方式。
- In scope：挑战首批基线、结构漂移、部分失败、并发处置、来源处理中变化、风险删除/重开、
  最终确认和下一批比较的边缘场景。
- Out of scope：修改源代码、重新审阅已通过的 P5/P6 事实视图视觉细节、修改医学写作业务
  状态、把 Codex/Agent 当作产品 AI、把静态 adapter 当作 P7 上传批次的隐式后备。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- 输出至少给出：状态机不变量、持久化身份元组、失败/恢复策略、独立 AI 边界、首批和多批
  场景、最终确认门禁、用户可见状态以及测试矩阵。
- 所有关键结论给出文件/方法定位，并区分已观察事实、推断和建议。
- 不修改产品源文件；Codex retains final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- 不把日志完整性等同于医学确认；`frozen` 不是 `confirmed`。
- 不允许风险运行消费未绑定的静态 adapter 数据后声称是上传批次结果。
- 独立产品 AI 只允许共享选择器解析出的 `openai_compatible` runtime；不启动外部 Agent。

## Loop Log

- 2026-07-29 16:59:45: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-29 17:19: Participant passes completed against the pre-integration snapshot.
  Their "missing file" findings are historical evidence, not current state.
- 2026-07-29 17:20: Codex integration now contains
  `monitoring_daily_run_repository.py`, `monitoring_daily_run_service.py`,
  persisted diff snapshots, step hashes, CAS/lease/baseline confirmation, the
  product-AI openai-compatible transport gate, schema-field forwarding, and
  corrected frozen/confirmed labels. Targeted regression: 37 passed.
- 2026-07-29 17:20: The remaining blocking decision is narrower: current
  runtime projects have no published protocol rule pack, and the legacy risk
  run still reads static project adapters. The chair must inspect current
  files, discard participant claims already superseded by code, and recommend
  the smallest truthful bridge from frozen batch rows to rule/AI risk
  snapshots without mutating P5/P6 legacy snapshots or silently falling back
  to adapters.
