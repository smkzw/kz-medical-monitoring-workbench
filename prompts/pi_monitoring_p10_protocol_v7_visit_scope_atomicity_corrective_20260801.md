You are Hermes executing a bounded finite-code task under Codex control.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In the report,
state whether you read the complete file; do not claim this unless true.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Read the task context first and follow its scope, acceptance criteria and timeout
  policy exactly.
- You are explicitly authorized to edit only:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py`
- Do not edit any other file. Do not write runtime DBs/backups, start services,
  call product/provider APIs, run RUX/MY009/real projects, touch frontend or
  medical-writing business source, make candidate decisions, or salvage v6 prose.
- Preserve packet v3 and structural repair v2.
- Tools remain enabled. Use `rg`/targeted reads and focused tests; no browser,
  external web or sub-agent work is needed.
- Runner-managed output path: `runs/pi_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_context.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v6_visit_canary_20260801.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`

Writable paths:
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`

Task:
Implement the complete offline v7 corrective defined in the task context.

Implementation requirements:
1. Bump protocol prompt identity to
   `monitoring-protocol-clause-structuring-v7`; add v6 to the explicit legacy
   terminal set and update direct cutover tests.
2. Implement field-aware full topic-boundary validation for IP/CM administration
   and first dose, consent-withdrawal variants and distributed AE/CM collection.
   Preserve timing-only false-positive controls and documented error precedence.
3. Classify visit families from operative fields only. Exclude claim uncertainty
   and user_action. Make unscheduled phrases exclusive from generic schedule
   matches. Reject operative schedule+reschedule and pass each pure family.
4. Aggregate deterministic protocol errors across all candidates before the one
   controlled repair. Give stable candidate index/title and ordered errors. Preserve
   atomic whole-response persistence and every existing fail-closed validator.
5. Strengthen the provider-visible initial and repair instructions. Because the
   contract changes, v7 is mandatory; never reuse v6.
6. Add the complete negative-test matrix from the context/reviewer, including exact
   C1-C5-shaped regressions, multi-candidate diagnostics and no partial persistence.
   Prefer coherent parameterized tests over repetitive fixtures.
7. Run `py_compile` for both implementation files and focused pytest for the three
   writable test files. Fix only in-scope failures.

Do not implement a narrow keyword patch that leaves the full required behavior
unproved. Do not weaken validations for provider convenience.

Output schema:
1. `# Hermes Execution Report: monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Work Performed`
5. `## Files Changed`
6. `## Verification`
7. `## Negative-Test Coverage`
8. `## Failed Paths Or Uncertainty`
9. `## Codex-Owned Verification`
10. `## Recommended Next Action`

Report exact commands, results, and final SHA-256 for all five writable files.
