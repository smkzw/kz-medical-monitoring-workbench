You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- This is an authorized shared-workspace edit round. Edit only the in-scope
  field-mapping prompt/service/quality files, dedicated tests, and task records.
- Never read or modify runtime SQLite databases and never start port 8911.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/hermes_monitoring_mapping_contract_v14_20260730.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_mapping_contract_v14_20260730_context.md`
- `context/monitoring_p10_mgk10_v13_scientific_audit_20260730.md`
- `context/monitoring_p10_v13_ip_cm_coding_semantic_review_20260730.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_mapping_contract.py`
- `services/api/app/monitoring_mapping_semantic_quality.py`
- `services/api/app/monitoring_ai_field_profiler.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_mapping_semantic_quality.py`

Adjacent dependency rule: directly demonstrated adjacent field-mapping test
files may be read only when a failing focused test or imported helper proves
that dependency.

Task:
Implement the strict generalized field-mapping contract repair described in the
task context. Work from failing tests first. Do not hard-code any real project,
domain prefix, or source field. The implementation must:

1. Upgrade the field-mapping prompt contract so old outputs are naturally stale
   under the existing job lifecycle.
2. Preserve deterministic form/page-name field profiles as read-only domain
   context for the independent AI while keeping them outside the permitted
   output field list.
3. Introduce a machine-checkable treatment-object identity contract. A domain
   name such as EX is never sufficient evidence. IP/placebo/active-comparator
   mapping requires cited same-domain evidence such as treatment identity,
   randomized treatment, IMP/IP, or a protocol/CRF dosing identity. When
   identity cannot be established, conservatively retain the source value under
   a neutral treatment-administration role with unresolved identity, bounded
   confidence, explicit missing-evidence uncertainty and a concrete user action.
4. Separate planned, prescribed, administered, dispensed, returned,
   duplicate/derived and unresolved dose semantics. If multiple same-domain
   dose-like fields have indistinguishable evidence or the CRF label is absent,
   do not silently choose planned or actual.
5. Use form/page context, scale-item siblings, labels and value shape together
   to prevent numeric disease-scale scores/totals from becoming procedure or
   record numbers. Source totals remain source-collected unless a separately
   validated deterministic formula exists.
6. Add an auditable capability limitation when the listing lacks distinct
   source-backed fields for dose adjustment, interruption, restart,
   discontinuation and other IP changes. Missing fields mean capability
   unavailable, never “no changes occurred.”
7. Add synthetic, non-oncology, project-neutral tests for background therapy,
   true IP, placebo/active comparator, topical/inhaled products, disease scales
   and ambiguous dose pairs. Preserve CM as non-IP and keep all IP action
   families separate.
8. Run focused and adjacent regression tests, Ruff `E4/E7/E9/F`, and
   `py_compile`. Produce concise context/run/review/metrics records. Do not edit
   `monitoring_ai_router.py`, `tests/test_monitoring_ai_api.py`, protocol
   preparation, rule publication, frontend, medical writing, or real databases.

Output schema:
1. `# Hermes Execution Handoff: monitoring_mapping_contract_v14_20260730`
2. `## Boundary Check`
3. `## Files Changed`
4. `## Contract Behavior`
5. `## Tests And Verification`
6. `## Residual Risk`
7. `## Codex Recheck Targets`

Quality gates:
- No project-specific production logic.
- No runtime database access and no 8911 startup.
- Do not merely document the defect; implement and verify it.
- Do not claim final acceptance; return exact test evidence and residual risk.
