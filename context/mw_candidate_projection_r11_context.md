# Task Context: mw_candidate_projection_r11

Created: 2026-07-29 02:51:48
Objective: Repair the confirmed competitor basket projection so reopening the medical-writing competitor drawer reliably reloads the immutable snapshot and exposes retained candidates, with regression evidence and a fresh isolated E2E round.
Task type: `html_ppt_visual_browser`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max-preview` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/mw_final_5x3_release_r11_20260729_context.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/BLOCKED.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/DEFECTS.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/COMPLETION_STATUS.json`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/screenshots/original_resolution/018_candidate_list_after_confirm.png`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r11-20260729/slots/A1/lazy_medical_writer/service_logs/api.log`
- `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_frontend_medical_writing_contract.py`
- `tests/test_frontend_medical_writing_pipeline_waiting_contract.py`

## Scope

- In scope:
  - prove the browser/API lifecycle that produced the empty candidate
    projection after a confirmed basket;
  - implement the smallest coherent frontend repair so every visible drawer
    opening refreshes the workspace for the current immutable snapshot;
  - distinguish loading from a genuinely empty snapshot;
  - add focused deterministic regression coverage;
  - run affected frontend contract tests and the frontend build.
- Out of scope:
  - changing the immutable r11 runtime databases or evidence;
  - bypassing triage, document validation, corpus admission, or AI gates;
  - treating the separate 59-not-admitted/3-failed preparation outcome as
    fixed;
  - redesigning unrelated medical-writing UI.

## Success Criteria

- A persisted drawer receives an explicit refresh signal on every closed-to-open
  transition, even when project and snapshot IDs are unchanged.
- The panel issues
  `/medical-writing/references/workspace?snapshot_id=<current snapshot>` for
  that open transition and rejects stale project/snapshot responses.
- While that request is unresolved, the UI shows a loading state rather than
  `0项 / 尚未检索公开竞品研究`.
- A true loaded snapshot with zero candidates still shows the genuine empty
  state.
- Focused tests and `npm run build` pass.
- The patch stays confined to the drawer/panel lifecycle and its focused tests.

## Risk Boundaries

- Writable product paths for this repair are explicitly limited to:
  - `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
  - `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
  - focused test files under `tests/`.
- Do not modify backend source, r11 evidence, frozen runtime databases, matrix
  receipts, or generated distribution files.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 02:51:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29 02:55: Root-cause boundary frozen. On the post-confirmation
  re-entry, the API log contains authoring-journey and latest-triage recovery
  requests but no writing-reference workspace request. The immutable snapshot
  itself still contains 665 candidates. The durable drawer therefore lacks an
  open-transition refresh contract; empty local workspace was rendered as a
  genuine zero-candidate result.
- 2026-07-29 03:03: Pi/Alibaba `qwen3.8-max-preview` xhigh completed one
  execution pass without fallback. The bounded repair added a closed-to-open
  refresh signal, retained project/snapshot stale-response guards, and separated
  unresolved loading from a genuine loaded-empty snapshot.
- 2026-07-29 03:06: Codex source acceptance passed. The focused plus adjacent
  frontend contracts passed 121/121 and the Vite production build succeeded.
  Live browser acceptance is deliberately deferred to a fresh r12 environment;
  r11 remains immutable and blocked.
