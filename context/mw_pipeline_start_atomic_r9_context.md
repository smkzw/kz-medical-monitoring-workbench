# Task Context: mw_pipeline_start_atomic_r9

Created: 2026-07-28 22:12:30
Objective: Repair the competitor-search to research-pipeline startup remount race proven by release-r9, add focused tests, and preserve all clinical/corpus gates
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/mw_final_5x3_release_r9_20260728_context.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r9-20260728/slots/A1/lazy_medical_writer/DEFECTS.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r9-20260728/slots/A1/lazy_medical_writer/BROWSER_ACTION_TRACE.json`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r9-20260728/slots/A1/lazy_medical_writer/pipeline_lineage.json`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r9-20260728/slots/A1/lazy_medical_writer/service_logs/api.log`
- Frozen r9 runtime databases under the same slot evidence root; read-only.
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/main.py`
- Existing focused tests adjacent to those implementation surfaces.

## Scope

- In scope:
  - make the successful competitor-search -> research-pipeline start transition
    survive frontend journey state application, parent callbacks and remount;
  - preserve a successful search snapshot if pipeline start fails;
  - expose a truthful retryable failure rather than silently claiming that the
    pipeline started;
  - ensure the one-click basket confirmation can advance the real parent
    pipeline and create its preparation/translation work;
  - add focused frontend and/or API tests reproducing the release-r9 race.
- Out of scope:
  - changing r9 evidence or databases;
  - relaxing document validation, structure review, translation scope, corpus
    admission, PICOS or independent-AI gates;
  - generating a preparation/translation batch directly in presentation code;
  - broad refactors, visual redesign, or unrelated AI-role settings.

## Success Criteria

- A successful competitor-search response is followed by exactly one
  research-pipeline start request before any callback can invalidate the active
  operation.
- A remount/navigation callback cannot suppress that start request.
- Start failure remains visible and retryable while the valid search snapshot
  is retained.
- Focused tests fail on the r9 behavior and pass after the repair.
- Existing research-pipeline, translation-batch and authoring-journey tests
  remain green.

## Risk Boundaries

- Edits are authorized only inside this workbench.
- Preserve current user changes and do not modify frozen r9 evidence.
- Prefer the smallest coherent frontend/API change that makes orchestration
  reliable; do not fabricate downstream state.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-28 22:12:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-28 22:13: Root cause established from frozen evidence: competitor
  search returned 200, but the intended pipeline-start POST never reached the
  API; journey application/callback occurs before the start call.
- 2026-07-28 22:27: Hermes/aishuo/cms-model completed the bounded two-file
  repair and reported 111 frontend-contract tests, 50 adjacent pipeline tests,
  52 durable-job tests and JSX compilation passing.
- 2026-07-28 22:32: Cursor CLI/auto manager returned `ACCEPT WITH REQUIRED
  FOLLOW-UP`. It accepted the reordering but required a function-scoped
  failure-retention test and identified stale UI writes if the active project
  changes while the non-aborted start request is completing.
- 2026-07-28 22:36: Codex added the post-start project/generation guard and
  strengthened all new assertions to the `runPublicSearch` function body.
  The server-side start remains allowed to complete; only stale frontend
  response application is suppressed.
- 2026-07-28 22:37: Codex verification passed:
  - 4 focused `pipeline_start` contracts;
  - 147 affected frontend/pipeline/translation regressions;
  - 52 durable-job state tests;
  - JSX esbuild bundle.
  Current implementation SHA-256:
  `95156b6798d940fe1cd7b83444c7c3c4a76ac88ddba9b7e45276331fe84c5bea`.
  Current contract-test SHA-256:
  `79d066660db17d11c11c6fdfdb5171cc629c25e731ef3bb5dd8fb92a59f212e1`.

## Acceptance Status

Deterministic repair acceptance is complete. The frozen release-r9 remains
`BLOCKED / FAIL`. Product acceptance requires a clean release-r10 headed
browser run proving:

1. exactly one parent pipeline start reaches the API after competitor search;
2. the durable parent pipeline exists before basket confirmation;
3. the confirmed basket advances into real preparation/translation work;
4. translation latest/preview no longer return 404 for the bound snapshot.
