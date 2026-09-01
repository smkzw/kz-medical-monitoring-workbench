# Conference Context: mm_r7_slice09a_contract_20260830

Created: 2026-08-30 10:14:53 CST
Objective: 独立挑战并冻结 R7 Slice-09A 项目备份、恢复、导出与导入合同；核查最小范围、包闭包、一致快照、原子恢复、故障矩阵、中文用户语义与相邻回归，不实施产品代码。
Task type: `complex_delivery_conference`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cms-router/minimax-m3:xhigh -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice09a_contract_20260830`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_1_20260830.md`：待挑战的完整合同草案。
- `context/medical_monitoring_r7_slice08_overall_review_and_slice09_plan_20260830.md`：Slice-08 接受边界与 Slice-09 分解。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`：R0–R8 当前正式实施计划。
- `services/api/app/medical_monitoring_r7_product_router.py`：项目工作区、公开 DTO 与产品路由现状。
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/{run_entry.py,runtime_progress.py,launch_registry.py,run_setup.py}`：R7 权威数据库、运行、发布、连续性与规则存储现状。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`：R1 SQLite、工件、审计与恢复权威存储现状。
- 当前文件系统为最终真相；只读核查，不读取五个真实项目，不启动服务或模型。

## Scope

- In scope: challenge package closure and format, SQLite/artifact consistent snapshot, import preflight, atomic restore/rollback, replay/conflict semantics, failure matrix, identity reconciliation, Chinese product DTO/progress, adjacent regression and YAGNI.
- Out of scope: product code edits, tests/service/model execution, real project data, medical-writing changes, visual UI reopening, mobile, security feature design, schema migration, log rotation, capacity benchmarking.

## Success Criteria

- Return a clear `ACCEPT_CONTRACT_V0_1`, `ACCEPT_WITH_REQUIRED_CORRECTIONS`, or `REJECT` recommendation.
- Enumerate every P0–P4 contract defect; propose exact replacement clauses for every required correction.
- Resolve or explicitly bound the six questions in Section 14 of the contract.
- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No product source is modified; Codex retains final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; explicit user routes also proceed when the catalog is stale or incomplete, while a genuinely missing CLI or native transport boundary may block. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-08-30 10:14:53 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
