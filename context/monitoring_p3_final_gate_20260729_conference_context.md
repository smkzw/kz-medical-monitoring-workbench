# Conference Context: monitoring_p3_final_gate_20260729

Created: 2026-07-29 06:41:35
Objective: 只读对抗审阅 P3 严格规则生命周期最终阻断修复：核对 gold case 不可变来源绑定、exact rule revision、影子案例集冻结与确认/发布复验、canonical field lineage、legacy lifecycle v0 生产隔离；只报告可复现 P0/P1 或明确通过，不修改文件
Task type: `high_risk_contradiction_review`
Risk: `critical`
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

- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_protocol_rule_service.py`
- `services/api/app/monitoring_rule_lifecycle_service.py`
- `services/api/app/monitoring_rule_templates.py`
- `tests/test_monitoring_rule_lifecycle.py`
- `tests/test_monitoring_real_listing_shadow_cases.py`
- 必要的 `tests/test_monitoring_protocol_rule*.py`
- `records/active_slices/medical_monitoring_goal_p3_20260729/P3_FINAL_REVIEW_LOOP_3.md`
- 用户本轮七项 P3 验收要求为最高业务合同。

## Scope

- In scope: 只读核对 gold case 不可变绑定、exact revision、案例集冻结与三次复验、
  canonical field lineage、legacy 生产隔离及对应反例测试。
- Out of scope: 修改任何文件；`main`、router、前端、医学写作、入排及 P4 功能。

## Success Criteria

- 每个结论带具体文件、行号、可复现路径和严重度。
- 只报告仍可触发的 P0/P1；低优先级建议列为残余风险，不扩大本轮范围。
- 若未发现阻断，明确说明已核对的攻击面和未覆盖边界。
- 不修改任何源代码、测试或数据；Codex 保留最终验收权。

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

## Loop Log

- 2026-07-29 06:41:35: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-29 06:43:00: 当前处于 00:00-08:30 禁用 aishuo 时段；初始化器生成的
  `general_aishuo_cms` 不执行，替换为 CodeBuddy CLI / hy3。原始与有效路由均记录于此。
- 2026-07-29 06:52:00: 两名参与者均未发现既有七项合同内 P0/P1。主会场要求主持者
  额外裁决：`run_shadow_validation()` 是否可能把 `evaluation_state=indeterminate`
  且 `matched=False` 的阴性案例误判为通过；严格发布 gold case 应只接受确定性
  `true/false`。同时核对参与者关于 AE-03 缺少显式排除断言的说法，因为真实测试
  `tests/test_monitoring_real_listing_shadow_cases.py:1964-1966` 已有该断言。
