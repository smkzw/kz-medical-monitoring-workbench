# Conference Context: mm_r7_slice07a_progress_ui_contract_20260828

Created: 2026-08-28 18:36:00
Objective: 独立审阅 R7 Slice-07A 医学监查真实进度与恢复界面合同：从懒惰、视觉敏感、数据敏感、风险敏感、中文原生且不熟悉计算机和AI的资深医学监察员视角，挑战信息层级、状态语义、真实进度、离页后台、停止/继续、错误恢复、无后端术语、可访问性和后续 ego(lite) 验收矩阵。不得实现代码，不得启动服务，不得运行真实项目；输出可执行的 P0-P4 修订意见。
Task type: `visual_report_structure`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair. The effective visual participant chain is `kimi-code/k3-256k:medium -> grok-build/grok-4.6:high -> cursor/cursor-grok-4.6:high -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> codex/gpt-5.6-luna:max`; it is filtered against the actual execution route nodes recorded below before dispatch.
- Guard validation alias for the declared Cursor fallback: `cursor-grok-4.6-high`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, code-review, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/google-antigravity `gemini-3.7-flash` (high) -> Pi/OpenCode Go `muse-spark-1.2-contributor` (high) -> Kimi Code `k3-256k` (medium) -> Codex subAgent `gpt-5.6-luna` (max). Participant 2 is Grok Build `grok-4.6` (medium) -> Pi/Cursor `cursor-grok-4.6` (medium) -> Pi/cms-router `minimax-m3` (high). Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice07a_progress_ui_contract_20260828`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice_07a_progress_ui_contract_v1_20260828.md`
- `context/medical_monitoring_r7_slice_06_review_and_slice07_plan_20260828.md`
- `frontend/AGENTS.md`
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py`
- `tests/test_medical_monitoring_r7_product_router.py`
- `context/medical_monitoring_subject_flow_dashboard_requirement_20260828.md`（仅用于确认后续 Slice-07B 边界）

## Scope

- In scope: 独立挑战 Slice-07A 合同中的用户信息层级、中文状态语义、真实进度、离页后台、停止/继续、错误恢复、可访问性、接口权威及 ego(lite) 验收矩阵；按 P0-P4 输出可直接落地的合同修订意见。
- Out of scope: 修改代码、启动服务或浏览器、运行真实项目、实现 Sankey/Patient Journey、触碰医学写作、设计或测试安全功能、展示凭据或内部运行标识。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 审阅结论必须逐项映射至合同条款或明确判定无需修改，并区分阻断实现的问题与后续增强。
- 不把模型自述、动画或前端推算当成真实进度；不把技术术语暴露给医学监察员。

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

- 2026-08-28 18:36:00: Conference initialized by `hermes_workflow_guard.py init-conference`.
