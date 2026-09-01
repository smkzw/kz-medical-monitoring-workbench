# Task Context: mw_truthful_pipeline_progress_20260729

Created: 2026-07-29 03:10:06
Objective: Implement truthful persisted weighted progress for medical-writing competitor search, triage, document preparation, translation, and corpus construction, with detailed current-substep labels and no elapsed-time fake progress.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md` and workspace `AGENTS.md`
- `context/mw_ai_roles_and_progress_contract_20260728.md`
- `context/mw_final_5x3_release_r11_20260729_context.md`
- frozen r11 A1 slot under
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/`
- `services/api/app/medical_writing_research_pipeline.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- existing backend/frontend research-pipeline contract tests

Frozen r11 evidence showed preparation advancing from 14/99 to 66/99 while
the parent remained fixed at 50%. Translation similarly remained fixed at 68%
while critical anchors became ready. These fixed anchors are not truthful
progress.

## Scope

- In scope:
  - persisted, backward-compatible pipeline progress projection;
  - weighted parent progress derived from real child counters for triage,
    preparation, translation, and round-1 corpus analysis;
  - concise current-substep label, child completed/total, and child percent;
  - frontend display of persisted parent percent plus current substep;
  - focused backend/frontend tests and build.
- Out of scope:
  - AI role/provider settings, `App.jsx`, shared oMLX gate semantics;
  - candidate drawer/panel lifecycle;
  - document-type classification/admission;
  - immutable r11 evidence/databases and release matrices;
  - elapsed-time interpolation, simulated timers, fabricated item counts, or
    invented ETA.

## Success Criteria

- Parent progress moves monotonically within observed stage ranges:
  triage 22-35, preparation 50-58, translation 68-85.
- Child progress survives status reload because it is persisted in
  `ResearchPipelineState`, not held only in React state.
- Preparation persists both real percent and current NCT/document label.
- Translation persists actual completed/total item counters and
  critical-anchor readiness.
- UI shows a specific human-readable step; technical IDs/logs stay hidden.
- Existing waiting, failed, cancel, resume, retry, and terminal semantics do
  not regress.
- Focused/adjacent pytest and frontend production build pass.

## Risk Boundaries

- Product write scope is limited to:
  - `services/api/app/medical_writing_research_pipeline.py`;
  - `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`;
  - focused tests under `tests/`.
- Do not touch AI role settings, `main.py`, `App.jsx`, candidate drawer/panel,
  document classification, r11 evidence, runtime databases, matrices, or dist.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 03:10:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29 03:18: Scope frozen from r11 evidence. The repair must use
  persisted observed counters and explicit stage weights; time-based smoothing
  or fake progress is forbidden.
- 2026-07-29 03:31: Delegated implementation returned with persisted child
  projection for triage, preparation, translation, and round-1 analysis.
  Codex review rejected global monotonicity across stage transitions because
  `failed=100` could leak into a retry and display fresh work as complete.
- 2026-07-29 03:36: Codex constrained monotonicity to the current active child
  stage, reset progress to the declared anchor on a real stage transition,
  preserved child evidence on failed/cancelled views, and cleared stale child
  labels when entering a different active phase. Added deterministic failed
  retry and same-phase waiting tests.
- 2026-07-29 03:38: Focused progress/waiting suite passed `12`; broader
  AI/OCR/translation/document/progress/frontend suite passed `321`. Frontend
  production build passed. No elapsed-time smoothing, invented counters, or
  fake ETA was introduced.
- 2026-07-29 03:42: Accepted for source freeze. Live r12 must still prove that
  real preparation and translation counters produce incremental parent and
  child progress after reload, and that failed retry no longer shows 100%.
