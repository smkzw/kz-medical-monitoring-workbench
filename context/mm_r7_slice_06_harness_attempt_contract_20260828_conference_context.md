# Conference Context: mm_r7_slice_06_harness_attempt_contract_20260828

Created: 2026-08-28 11:36:26
Objective: 独立审阅并挑战 R7 Slice-06 harness capability attempt、有限重试、恢复与诚实 session/cancel 语义合同；只读源码与合同，不修改文件，不调用模型服务或真实项目，不启动产品服务。输出必须逐项回答四个待会商问题，列出 P0-P4 缺陷及可执行修订建议，并明确 ACCEPT 或 REVISE。
Task type: `long_horizon_code`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair. The effective visual participant chain is ``; it is filtered against the actual execution route nodes recorded below before dispatch.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, code-review, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/google-antigravity `gemini-3.7-flash` (high) -> Pi/OpenCode Go `muse-spark-1.2-contributor` (high) -> Kimi Code `k3-256k` (medium) -> Codex subAgent `gpt-5.6-luna` (max). Participant 2 is Grok Build `grok-4.6` (medium) -> Pi/Cursor `cursor-grok-4.6` (medium) -> Pi/cms-router `minimax-m3` (high). Codex remains the final authority.
- The cataloged Cursor CLI `cursor-cli` / `cursor` route was not selected for this packet; it is recorded here
  for panel validation only and is not retroactively claimed as a participant.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice_06_harness_attempt_contract_20260828`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r7_slice_06_harness_attempt_recovery_contract_draft_20260828.md`
- `context/medical_monitoring_r7_slice_05_review_and_slice06_plan_20260828.md`
- `context/medical_monitoring_r7_slice_05_background_recovery_contract_20260828.md`
- `context/medical_monitoring_r7_slice_05_background_recovery_contract_errata_20260828.md`
- `context/medical_monitoring_r6_runtime_slice_07_agent_harness_acceptance_record_20260828.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/background_recovery.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/run_binding.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`

## Scope

- In scope: contract consistency with current R1/R6/R7 code; ownership and lease composition; preflight ordering;
  retry classification and limit; honest logical continuation versus transport session semantics; unsupported cancel;
  deterministic/offline and later synthetic live-smoke acceptance matrix; native Chinese audience projection.
- Out of scope: file edits by participants; service/model/real-project execution; frontend; security features;
  medical-writing subsystem; overall R7/R8 acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Both participants cite concrete source behavior, answer all four draft questions, identify P0-P4 defects or state
  none with evidence, and return an explicit `ACCEPT` or `REVISE` recommendation.

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

- 2026-08-28 11:36:26: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-28: Pi round 1 and Grok round 1 both returned REVISE without fallback.
- 2026-08-28: v0.2 closed shared lease/node/preflight/controller/identity findings; Pi same-session accepted.
- 2026-08-28: Grok same-session retained classifier and resumable-ledger P0s; v0.3 closed both.
- 2026-08-28: Grok same-session final delta returned `ACCEPT_CONTRACT_V0_3`; Codex froze v1.0.
