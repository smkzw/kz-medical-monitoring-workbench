# Conference Context: safety_pv_dual_project_fullchain_20260714

Created: 2026-07-14 11:51:31
Objective: 补齐RUX与MY009双项目Safety/PV五类医学复核、统一SQLite幂等/CAS/审计、来源换版失效、医学监查交接和桌面端完整交互
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/safety_pv_dual_project_fullchain_20260714/TASK_RECORD.md`
- `services/api/app/safety_pv_manifest.py`
- `services/api/app/safety_pv_review_workbench.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx` and `frontend/src/styles.css`
- `tests/test_safety_pv_manifest.py`, `tests/test_safety_pv_review_workbench.py`, `tests/test_workbench_inbox.py`, and `tests/test_frontend_safety_projection_contract.py`
- Real source facts already registered by the production manifest: MY009 2026-04-10/2026-04-08 listing, safety evaluation report, AE TFL and DSUR collection document; RUX-03-002 listing, safety management plan and CTD 2.7.4 clinical safety summary. Models must not open user document roots directly in this conference.

## Scope

- In scope: explicit five-action state machine, source-version invalidation, SQLite immutable records/state, idempotency and optimistic concurrency, unified audit, monitoring-to-Safety/PV projection and handoff, project inbox behavior, and desktop interaction/test design for both projects.
- Out of scope: formal PV seriousness/expectedness/causality/reportability decisions, regulatory clocks, E2B, PV database writes, creation of a second risk ledger/timeline/profile, modification of clinical source files, and final visual or clinical acceptance.

## Success Criteria

- Recommendations must point to current code facts and the narrowest compatible implementation.
- Same monitoring risk identity and source revision remain authoritative in the Safety/PV projection.
- Each action has valid predecessors, substantive-comment policy, source binding policy, idempotent replay behavior, expected revision and audit semantics.
- RUX and MY009 both have concrete API and browser test cases, including project switching and source drift.
- Source content itself is primary in the review UI; locators remain secondary traceability.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- CM means non-investigational concomitant medication; study-drug dose adjustment, interruption, discontinuation and other investigational-product changes remain separate.
- The system may produce content pending medical approval but must not upgrade it to a final PV conclusion.

## Loop Log

- 2026-07-14 11:51:31: Conference initialized by `hermes_workflow_guard.py init-conference`.
