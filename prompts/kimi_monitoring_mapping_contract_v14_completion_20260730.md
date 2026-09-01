You are the fallback implementation worker in a Codex-controlled workflow.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- This is an authorized shared-workspace edit round.
- Never access runtime SQLite databases and never start port 8911.
- Do not edit `services/api/app/monitoring_ai_router.py`,
  `tests/test_monitoring_ai_api.py`, protocol preparation, rule publication,
  frontend, medical writing, or runtime provider selectors.
- Edit only field-mapping prompt/service/semantic-quality code, dedicated tests,
  and the task records named below.
- Runner-managed output path:
  `runs/kimi_monitoring_mapping_contract_v14_completion_20260730.md`.
  Do not write that report path through tools; return the report in the final
  response for the runner to persist.

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

Task:
The primary worker failed to establish a usable session after leaving a partial
implementation. Treat the current files as untrusted partial work. Preserve
useful pieces, but complete the strict generalized contract and tests.

Known partial-work gaps that must be addressed:

1. `read_only_domain_context` currently exposes only deterministic field names
   and recommended roles. That does not expose decisive form/page labels such as
   "background therapy". Preserve bounded top/representative values and counts
   for only form/page/study-treatment identity context fields. Do not expose
   identifiers and do not allow these fields in output mappings.
2. The provider output model currently has no machine-checkable
   `object_identity`, identity evidence-field binding, or dose-semantic state.
   Prompt prose alone is insufficient. Add a backward-compatible persisted
   contract for relevant mappings and deterministic validation or conservative
   normalization.
3. A domain name such as EX, EC, dosing, administration or treatment is never
   sufficient to establish IP. IP/placebo/active-comparator identity needs
   same-domain source evidence. Background, rescue and concomitant evidence must
   not become IP. Unknown identity must become a neutral
   `treatment_administration`/source role, `object_identity=unresolved`, bounded
   confidence, explicit missing-evidence `uncertainty`, concrete `user_action`,
   and an auditable system quality-gate action.
4. Planned, prescribed, actual-administered, dispensed, returned,
   duplicate/derived and unresolved dose semantics must be machine-readable.
   Same-domain dose-like fields with indistinguishable profiles or absent CRF
   labels cannot silently receive different specific meanings. Unknown meaning
   must remain neutral/unresolved and source-collected.
5. Scale protection must use actual read-only form/page context plus sibling
   scale-item evidence, not only role strings or domain-name markers. A numeric
   total/score misclassified as a procedure/record number must be rejected or
   conservatively normalized before persistence.
6. The semantic quality report must expose an `ip_change_lifecycle` capability
   blocker when distinct, source-backed dose adjustment, interruption, restart,
   discontinuation and other change families cannot be reconstructed. It must
   never infer "no change occurred" from absence.
7. Production code must remain project neutral. Real project names, batch IDs,
   and source fields may appear only in audit records, never in decision logic.
8. Add multi-style synthetic tests: explicit IP identity, placebo and active
   comparator; non-IP background/rescue/concomitant therapy; topical and inhaled
   products; ambiguous dose pairs; questionnaire/disease-scale item and total
   fields. Assert both safe acceptance and unsafe-output normalization/rejection.

Run:
- Focused tests for service and semantic quality.
- Adjacent mapping draft/activation/candidate-audit tests if touched contracts
  propagate there.
- Ruff `E4,E7,E9,F` and `py_compile` on touched Python.

Update:
- `context/monitoring_mapping_contract_v14_20260730_context.md`
- `reviews/codex_monitoring_mapping_contract_v14_20260730_review.md`
- `metrics/monitoring_mapping_contract_v14_20260730_metrics.md`

Do not claim final acceptance. Return changed files, exact tests, unresolved
risks, and specific Codex recheck targets.
