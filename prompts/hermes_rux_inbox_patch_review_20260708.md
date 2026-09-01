You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. This policy file is the only allowed read outside the current workspace root. In your output, state honestly whether you read the full file.

Hard boundaries:
- Work only inside the current workspace root, except for the explicitly allowed `/Users/smkzw/.hermes/SOUL.md`.
- Do not read original clinical project folders.
- Do not edit files.
- Do not browse web, run tests, open browsers, inspect images, or perform visual/PPT/browser acceptance.
- Write exactly one output file: `runs/hermes_rux_inbox_patch_review_20260708.md`.

Read these files only:
- `context/rux_inbox_patch_review_20260708_context.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/rux_monitoring_service.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/main.py`
- `tests/test_rux_monitoring_service.py`
- `tests/test_workbench_inbox.py`
- `research/rux_inbox_external_research_20260708.md`
- `reviews/codex_conference_rux_p0_backend_review_20260708_review.md`
- `metrics/rux_p0_backend_review_20260708_conference_metrics.md`
- `KNOWN_ISSUES.md`

Task:
Perform a focused post-implementation code review of the RUX-03-002 workbench inbox patch. Prioritize defects, source-boundary risks, clinical-workflow semantics, regressions, and missing tests. Do not praise the patch generically. If you identify blocking or important issues, include the precise file/function and a minimal fix recommendation. If an issue is a known non-blocking limitation, classify it as follow-up.

Output schema:
1. `# Hermes Code Review: rux_inbox_patch_review_20260708`
2. `## Boundary Check`
3. `## Findings`
4. `## Test Coverage Assessment`
5. `## Commercialization / Clinical Workflow Risk`
6. `## Required Fixes Before Codex Proceeds`
7. `## Follow-Up Work`
8. `## Final Recommendation`

Quality gates:
- Findings first, ordered by severity.
- Separate evidence from inference and recommendation.
- Do not make final clinical/regulatory/visual/current-web claims.
- Do not claim test execution; use only Codex-reported verification from the context.
- Do not approve full commercial readiness; review only this P0 backend patch.
