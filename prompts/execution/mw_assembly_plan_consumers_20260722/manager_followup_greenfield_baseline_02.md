# Targeted greenfield baseline repair

Continue in the SAME manager session. Codex reproduced the combined manager + greenfield + table suite: 30 passed, 3 subtests, 3 failures. Your report's claim that all three are simply missing-plan fixtures is inaccurate. Fix these exact failures without weakening production fail-closed behavior:

1. `StudyDefinitionGreenfieldBindingTests::test_template_bound_request_accepts_all_canonical_dynamic_fact_projections`
   - Production bug: `_validate_greenfield_request_against_study_definition()` already receives `resolved_sections` but recomputes template seeds through the global plan-gated service with an empty project id.
   - Refactor it to validate against the passed authoritative `resolved_sections` (or pass a canonical project id through the real call path if recomputation is truly required). Do not silently bypass the plan gate at production entrypoints.

2. `GreenfieldMedicalWritingRuntimeFlowTests::test_greenfield_reuses_working_copy_approval_and_docx_export`
   - This is not a plan fixture failure. The test still calls retired writing ApprovalGate APIs and asserts `待医学批准` / `medically_approved`.
   - Migrate it to current author semantics: saved author content is an author decision; unresolved project/design decisions must block current-version freeze/final readiness as appropriate; after resolving required decisions, freeze the current revision and verify immutable freeze/history/readiness behavior. Remove obsolete writing-approval wording/assertions while preserving the DOCX and unresolved-decision coverage.

3. `GreenfieldMedicalWritingApiTests::test_greenfield_structured_table_round_trip_restart_and_export_boundaries`
   - Create/refresh/confirm a project ProtocolAssemblyPlan through the actual API/service fixture before the managed DOCX export. Assert the plan id/revision/hash pin or fail-closed transition where observable. Do not bypass the exporter helper.

Allowed writes for this follow-up:
- `services/api/app/main.py` only for the confirmed validation defect;
- `tests/test_medical_writing_greenfield_runtime.py` and narrowly shared test helpers;
- manager integration tests only if needed.

Run at minimum:
- `tests/test_manager_plan_consumption_integration.py`
- `tests/test_medical_writing_greenfield_runtime.py`
- `tests/test_medical_writing_table_api.py`
- author-freeze, protocol-plan, source-preserving export and Worker 01-03 suites.

Return exact changes, commands/pass counts and any residual failure. End with `MANAGER_GREENFIELD_BASELINE_COMPLETE` only when all three reproduced failures are green. Do not write the runner report directly.
