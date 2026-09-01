# Conference Context: safety_pv_dual_project_parity_20260713

Created: 2026-07-13 06:36:34
Objective: 基于MY009与RUX真实来源补齐安全信号与PV协同双项目全链路、来源版本、五动作、handoff与桌面验收
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

- `services/api/app/safety_pv_manifest.py`
- `services/api/app/safety_pv_review_workbench.py`
- `services/api/app/main.py` safety source requirements and API routes
- `packages/contracts/workbench_contracts/models.py` safety contracts
- `tests/test_safety_pv_manifest.py`
- `tests/test_safety_pv_review_workbench.py`
- `frontend/src/App.jsx` Safety/PV panel and state orchestration
- `frontend/tests/safety_pv_manifest_qc.mjs`
- `frontend/tests/tfl_safety_source_admission_qc.mjs`
- `logs/subsystems/safety_pv_log.md`
- `records/research/safety_pv_dual_project_20260713/EXTERNAL_AND_LOCAL_BASELINE.md`
- User authorized read-only access to original material under `/Users/smkzw/Documents/康哲项目资料` and `/Users/smkzw/Documents/朗来项目资料`; original files must never be modified, moved or deleted.

## Scope

- In scope: bind RUX listing + PV plan + 2.7.4 as one package; project-agnostic single/double-header parsing; MY009/RUX candidates; all five actions; source-admission and source-drift invalidation; durable audit; handoff; desktop project switching and every-button E2E.
- Out of scope: final seriousness/expectedness/causality/reportability decisions, PV database writes, E2B generation/transmission, regulatory clocks, automatic medical approval, post-marketing disproportionality statistics.

## Success Criteria

- RUX manifest contains real listing domains and at least AE, lab, ECG, non-investigational CM plus PV-plan/2.7.4 alignment candidates; no project-name parsing branch.
- RUX source admission requires the actual listing, PV plan and 2.7.4. MY009 keeps its actual 20260410 listing, S1 package and DSUR source.
- CM/non-investigational medication is never conflated with investigational product or dose adjustment.
- Each project can execute mark reviewed, request PV confirmation, return, close-no-action and reset with valid transitions and immutable source-bound records.
- Source replacement invalidates old reviewed/candidate status and removes stale handoff candidates.
- Browser automation uses both real projects and exercises every action, project switch, refresh, handoff and no-leak/no-overflow checks on desktop.
- Focused, full regression, production build and original-resolution Chrome screenshots pass.

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

## Loop Log

- 2026-07-13 06:36:34: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-13: Local inspection confirmed RUX dual header and field aliases; external official product research recorded in the bounded baseline.
- 2026-07-13: Participant rounds reviewed the pre-implementation state. After their outputs completed, Codex began the accepted TDD slice for RUX listing/header/alias/source registration. The chair must distinguish participant-time evidence from the newer shared-workspace state and must not label temporal differences as hallucinations.
- 2026-07-13: User materially replaced this objective with a two-part Safety/PV redesign. The chair run was interrupted before completion; this conference is `superseded_by_user_redesign` and must not pass its review gate.
