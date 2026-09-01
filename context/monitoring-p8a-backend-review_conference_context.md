# Conference Context: monitoring-p8a-backend-review

Created: 2026-07-29 23:00:18
Objective: 独立审阅 P8-A 后端权威风险分类与 Checklist 查询实现，寻找分类边界、兼容降级、稳定分页、API 关闭失败及测试遗漏；只读，不修改文件
Task type: `high_risk_contradiction_review`
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

- `context/monitoring_p8a_backend_context.md`
- `reviews/monitoring_p8_risk_workspace_gap.md`
- `context/monitoring-p8a-backend_context.md`
- `services/api/app/medical_monitoring_risk_taxonomy.py`
- `services/api/app/medical_risk_repository.py`
- `services/api/app/medical_monitoring_summary.py`
- `services/api/app/medical_monitoring_router.py`
- `services/api/app/monitoring_rule_risk_bridge.py`
- `services/api/app/monitoring_ai_risk_bridge.py`
- `services/api/app/rux_monitoring_service.py`
- `services/api/app/my009_monitoring_service.py`
- Monitoring tests changed for P8-A and adjacent monitoring contract tests.
- Test evidence already observed by Codex: focused `87 passed`, repository
  `17 passed`, API `12 passed`, and 55-file monitoring regression `709 passed`.
- Do not read the real runtime database or treat current frontend/runtime state
  as part of this backend-only acceptance.

## Scope

- In scope: read-only contradiction review of taxonomy closure/versioning,
  classification inputs, legacy degradation/lineage, Safety/PV independence,
  strict CM versus EX/EC/DA/IP boundaries, seven-column query validation and
  stable snapshot-pinned pagination, real-project adapter compatibility, and
  material missing tests.
- Out of scope: editing any file; frontend/App/CSS; medical writing; shared AI;
  P7B/P7C rule lifecycle; shared contracts; browser or visual acceptance; API
  restart; real runtime database access.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- Findings are ordered by severity and cite exact file/line evidence.
- The review explicitly tests whether title/rationale/display text can affect
  classification and whether old coarse codes can acquire finer meaning.
- The review checks deterministic tie behavior, page stability across new
  snapshots, unknown query rejection, and project-scoped snapshot lookup.
- The review distinguishes a material defect from a later frontend integration
  boundary and from pre-existing unrelated lint/deprecation warnings.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.

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
- Read-only review: no source, test, runtime, database, or generated artifact
  mutation is authorized.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-29 23:00:18: Conference initialized by `hermes_workflow_guard.py init-conference`.
