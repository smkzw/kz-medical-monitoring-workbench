# Conference Context: mm_r7_slice09e_contract_review_20260831

Created: 2026-08-31 09:36:42 CST
Objective: 独立审阅R7阶段复盘与Slice-09E本地分发数据处置合同，判断09E是否必要、范围是否最小、是否可进入实施，并输出P0-P4缺陷与明确结论。
Task type: `stage_review_plan`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.


## Preferred Browser Advisory Chair

- Role: `chatgpt-web-pro-advisory` via `codex-with-chatgpt`.
- Assignment: preferred stage-level retrospective and phase-planning adviser.
- UI selection: `Pro` / `GPT-5.6 Sol`; the visible UI state must be positively verified.
- Boundary: read-only C2C advisory chair, not a runner subprocess or executable participant. Reuse the same session, perform 20-30 second foreground DOM checks, and persist `c2c session` / `c2c record` state. A browser timeout is pending, not failure; there is no automatic callback.
- Codex remains the formal packet chair and final authority. If the advisory response is unavailable or invalid, continue the declared executable panel.


## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cms-router/minimax-m3:xhigh -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice09e_contract_review_20260831`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（R7 十项步骤）
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（本地应用、备份迁移与 R8 边界）
- `context/medical_monitoring_r7_phase_review_after_slice07c4_and_slice08_plan_20260829.md`
- `context/medical_monitoring_r7_slice_03_product_mount_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice09d_implementation_acceptance_record_20260831.md`
- `context/medical_monitoring_r7_slice09_overall_and_r7_phase_review_20260831.md`
- `reviews/medical_monitoring_r7_slice09e_local_distribution_contract_v0_1_20260831.md`
- Do not add production paths unless the user explicitly authorized reading them for this task.

## Scope

- In scope: R7 requirement-to-evidence reconciliation; whether Slice-09E is necessary; whether its contract is the smallest sufficient closeout; missing invariants, verification cases and user-facing data-disposition semantics.
- Out of scope: implementation edits; real projects/models/browser; service startup; security design/testing; medical-writing subsystem; R8 real-source execution.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Return P0-P4 findings with exact file/section anchors and one of `ACCEPT_CONTRACT` / `REVISE_CONTRACT` / `REJECT_SLICE_ROUTE`.

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

- 2026-08-31 09:36:42 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
