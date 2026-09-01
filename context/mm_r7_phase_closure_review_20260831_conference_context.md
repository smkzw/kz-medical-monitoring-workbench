# Conference Context: mm_r7_phase_closure_review_20260831

Created: 2026-08-31 10:43:53 CST
Objective: 独立审阅医学监查 R7 十项要求、System Design 15.1/15.4、Slice-01至09E的受限验收与当前源码边界；判断能否仅以 synthetic/offline engineering baseline 收口并进入 R8 合同冻结，还是必须先补本地通知或真实一键应用纵切；不得把真实项目、医学质量、真实安装或生产能力伪造成已完成。
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

- Linked execution task: `mm_r7_slice09e_implementation_20260831`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor/default`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（重点 §§15.1、15.4）
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（重点 R7 十项与完成证据）
- `context/medical_monitoring_r7_slice09_overall_and_r7_phase_review_20260831.md`
- `context/medical_monitoring_r7_slice_01_execution_profile_run_binding_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice_02_product_api_run_entry_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice_03_product_mount_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice_04_durable_progress_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice_05_background_recovery_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice_06_harness_live_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice07a_progress_ui_acceptance_record_20260828.md`
- `context/medical_monitoring_r7_slice07b_subject_flow_acceptance_record_20260829.md`
- `context/medical_monitoring_r7_slice07c4_visual_acceptance_record_20260829.md`
- `context/medical_monitoring_r7_slice08d_implementation_acceptance_record_20260830.md`
- `context/medical_monitoring_r7_slice09a_implementation_acceptance_record_20260830.md` through `09e_implementation_acceptance_record_20260831.md`
- Current source evidence for disputed boundaries: `frontend/src/App.jsx`, `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProgressPanel.jsx`, `deploy/medical_monitoring_local/README.md`, `deploy/medical_monitoring_local/manage.py`, `deploy/medical_monitoring_local/distribution.py`.

## Scope

- In scope: requirement-to-evidence reconciliation; severity of local-notification and one-click-app gaps; distinction between synthetic/offline engineering baseline and real user/product completion; exact R8 entry gate.
- Out of scope: editing code; running services/browser/models/real projects; judging medical accuracy; accepting production/commercial/regulatory readiness; modifying medical writing.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Every R7 plan item must be labeled closed, limited, deferred-to-R8 by design, or blocking; no ambiguous “mostly done”.
- Reviewer must decide whether a new R7 bounded slice is required. If yes, specify the smallest observable contract; if no, specify the narrow acceptance wording and R8 carry-forward gates.

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

- 2026-08-31 10:43:53 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
