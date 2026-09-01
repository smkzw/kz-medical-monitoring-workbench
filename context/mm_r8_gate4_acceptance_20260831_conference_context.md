# Conference Context: mm_r8_gate4_acceptance_20260831

Created: 2026-08-31 13:35:11 CST
Objective: 独立审阅医学监查子系统R8 G4合成通知seam与System Design 15.4十三项程序，核查合同符合性、失败关闭、确定性、反过拟合、发布边界及P0-P4；不得写代码、启动服务/浏览器/模型或读取真实项目
Task type: `code_open_audit`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.


## Preferred Browser Advisory Chair

- Role: `chatgpt-web-pro-advisory` via `codex-with-chatgpt`.
- Assignment: preferred advisory chair for code review.
- UI selection: `Pro` / `GPT-5.6 Sol`; the visible UI state must be positively verified.
- Boundary: read-only C2C advisory chair, not a runner subprocess or executable participant. Reuse the same session, perform 20-30 second foreground DOM checks, and persist `c2c session` / `c2c record` state. A browser timeout is pending, not failure; there is no automatic callback.
- Codex remains the formal packet chair and final authority. If the advisory response is unavailable or invalid, continue the declared executable panel.


## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cms-router/minimax-m3:xhigh -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r8_gate4_synthetic_15_4_20260831`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor/default`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r8_gate4_synthetic_15_4_implementation_contract_v0_1_20260831.md`
- `reviews/medical_monitoring_r8_gate3_notification_decision_contract_v0_3_20260831.md`
- `reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md` §6-§8
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §15.4
- `deploy/medical_monitoring_local/synthetic_notification.py`
- `deploy/medical_monitoring_local/synthetic_15_4.py`
- `deploy/medical_monitoring_local/manage.py`
- `deploy/medical_monitoring_local/distribution.py`
- `deploy/medical_monitoring_local/release_sources.json`
- `deploy/medical_monitoring_local/README.md`
- `tests/test_medical_monitoring_r8_gate4_notification.py`
- `tests/test_medical_monitoring_r8_gate4_15_4.py`
- `tests/test_medical_monitoring_r8_gate4_distribution.py`
- Only the R7 source modules directly referenced by the G4 implementation may be opened to
  verify reuse rather than copied state machines.
- Do not read worker reports, worker stdout, real-project directories, model outputs, browser
  artifacts or medical-writing source. The current code and contracts are the review object.

## Scope

- In scope: contract fidelity; notification terminal authority/frozen gates; full identity and
  revision idempotency; channel failure isolation; persistent in-app degradation; navigation-only
  behavior; all 13 §15.4 items; actual temporary confirm/cancel semantics; canonical replay and
  tamper rejection; temporary-root/path traversal gates; deterministic output; anti-overfit;
  release inventory; Chinese user copy; focused and adjacent test sufficiency; P0-P4 findings.
- Out of scope: edits, real projects, real notifications, real model/harness calls, browser/UI,
  network, ports/services, medical-writing code, product safety/security design, G5/G6 acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Return an explicit `ACCEPT`, `ACCEPT_WITH_NONBLOCKING_FINDINGS`, or `REVISE` disposition;
  list every finding with P0-P4, file/line evidence, consequence, and smallest remediation.
- G4 may pass only when P0/P1 are closed and no claim exceeds synthetic/offline evidence.

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

- 2026-08-31 13:35:11 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
