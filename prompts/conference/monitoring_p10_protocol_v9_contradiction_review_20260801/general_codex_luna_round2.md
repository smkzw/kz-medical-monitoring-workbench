Continue the existing native Luna session for one delta-only read-only review.
Do not restart the prior broad v9 review.

Hard boundaries:
- Work only inside the current workspace.
- Do not modify any file.
- Do not start tests, services, providers, ports, runtime databases, browsers,
  real projects or candidate workflows.
- Do not read medical-writing or real-project files.
- Runner-managed output path:
  `runs/conference/monitoring_p10_protocol_v9_contradiction_review_20260801/general_codex_luna_round2.md`.
  Return the complete report; do not write the path.

Read these files only:
- `AGENTS.md`
- `context/monitoring_p10_protocol_v9_cutover_direct_tests_20260801_context.md`
- `runs/pi_monitoring_p10_protocol_v9_cutover_direct_tests_20260801.md`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`

Task:
Independently review the P2 closure and report delta-only findings with exact
file/line or test locators.

Challenge all of the following:

1. Whether `superseded_workflow_contract`, `superseded_prompt_contract`, and
   `superseded_job_contract` are correctly and safely permanent non-retry states
   for every task type, rather than only protocol v8/v9.
2. Whether ordinary same-revision `stale_claimed` retry and completed-candidate
   restoration remain valid and are actually exercised after the fix.
3. Whether the v8→v9 test really proves completed/failed audit preservation,
   same-revision queued and running v8 retirement, frozen attempts, no
   retry/reuse/claim, late completion CAS loss with zero candidates, and
   distinct v9 selection/completion.
4. Whether artificial business-key suffixes or manually constructed states
   weaken the proof compared with real startup/service behavior.
5. Whether changing the retry error message or fail-loud behavior creates an
   untested downstream regression.
6. Whether any P0-P4 issue remains before runtime preflight. Do not infer canary
   success from offline tests.

Parent-recorded verification, not independently rerun:
- compile pass;
- focused shared tests `429 passed`;
- full monitoring excluding one known unrelated collection file
  `1400 passed, 4285 deselected`;
- adjacent medical-writing contracts `200 passed`.

Output schema:
1. `# Luna Delta Review: monitoring_p10_protocol_v9_cutover_direct_tests_20260801`
2. `## Boundary Check`
3. `## Findings`
4. `## Evidence And No-Issue Scope`
5. `## Residual Risk`
6. `## Gate Decision And Next Action`

If no defect remains, explicitly state the P0-P4 no-issue scope and what is still
unproven. Do not invent a finding.
