# Conference Context: workbench_resume_review_20260708

Created: 2026-07-08 08:02:21
Objective: Review AI Medical Manager Workbench resume-state changes, source registry/eligibility/dashboard public API boundaries, and overview inbox visibility before further commercialization build
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- Authoritative local task record:
  - `logs/SOFT_PAUSE_20260708_0640_CST.md`
  - `logs/system_build_log.md`
  - `logs/subsystems/project_dashboard_log.md`
  - `logs/subsystems/module_scope_log.md`
- Source/API boundary files:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/main.py`
  - `services/api/app/source_intake.py`
  - `services/api/app/enrollment_adapter.py`
  - `services/api/app/workbench_inbox.py`
  - `services/api/app/eligibility.py`
  - `services/api/app/demo_repository.py`
- Frontend/QC files:
  - `frontend/AGENTS.md`
  - `frontend/src/App.jsx`
  - `frontend/tests/overview_ai_gateway_qc.mjs`
- Tests:
  - `tests/test_source_registry.py`
  - `tests/test_workbench_inbox.py`
  - `tests/test_eligibility_adapter.py`
  - `tests/test_contracts.py`
- Rendered/browser evidence:
  - `records/visual_qc_20260708/overview_source_eligibility_after_hermes/overview_ai_gateway_qc.json`
  - `records/visual_qc_20260708/overview_after_deepseek_review/overview_ai_gateway_qc.json`

## Scope

- In scope:
  - Review and verify source registry, eligibility, health, and overview inbox public API boundaries.
  - Review and verify the limited overview inbox diversity recovery.
  - Confirm visible module scope and wording still follow user constraints.
  - Apply only low-risk consensus changes accepted by Codex after Hermes review.
  - Preserve enough records for context compression or handoff.
- Out of scope:
  - Building first/fourth/fifth non-medical clinical-development links.
  - Reading or modifying original real-project folders outside backup/copy-safe project workspace.
  - Final clinical/regulatory conclusions, visual acceptance by Hermes, or any Hermes production writes.
  - Starting the next build loop before the current recovery review is closed.

## Success Criteria

- Hermes sub-venue participant outputs and chair review are complete and bounded.
- DeepSeek supplier `deepseek-v4-pro` main-venue review is complete.
- Consensus code changes are applied only after Codex review.
- Focused backend tests, full backend regression, frontend build, live API V1/V2 checks, and browser QC pass.
- Logs and soft-pause notes identify changed files, verification evidence, remaining risks, and next restart point.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-08 08:02:21: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08: This context was retrospectively completed after DeepSeek Pro identified that the original guard template still had placeholder source/scope/success sections during participant dispatch. Participant and main-venue outputs preserve that process gap as a lesson learned.
