You are continuing the same `worker_01` session for the second and final R2 Batch A acceptance repair.

Hard boundaries:
- Work only inside the current workbench workspace root.
- Modify only Batch A files under `poc/medical_monitoring_ai_native_r2/`.
- Preserve both earlier reports as immutable history.
- Runner-managed output path: `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_01_followup_02.md`. Do not write this report file yourself; return the report in your final response.
- Do not edit R1, product, medical-writing, real-project, shared-runtime or 8911 surfaces.

Read these files only:
- `context/medical_monitoring_r2_kernel_execution_20260810_execution_context.md`
- `plans/codex_execution_medical_monitoring_r2_kernel_execution_20260810.md`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/schema_registry.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/domain.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/identity.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/artifacts.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/acceptance.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/__init__.py`
- `poc/medical_monitoring_ai_native_r2/tests/`
- `poc/medical_monitoring_ai_native_r2/README.md`

The first repair closed the seven original reproductions, but Codex source review found the following remaining Batch A foundation gaps:

1. `SourceRevision.content_digest` and `ListingSnapshot.content_digest` accept any non-empty string while the API/report claim a real SHA-256. Validate exactly a canonical 64-character hexadecimal digest (normalize or fail consistently) and add empty/short/non-hex regressions.
2. `RecordIdentity` and `RiskIdentity` auto-derive deterministic IDs only when the caller passes an empty ID; a direct constructor still accepts an arbitrary non-empty public ID. Enforce that a supplied public ID exactly matches the deterministic digest-derived ID. Canonicalize lineage/order where semantics are set-like so repeated factories cannot drift due only to parent ordering. Add direct-constructor mismatch and parent-order regressions.
3. The acceptance chain still allows `structurally_valid`, `mapping_reviewed`, and `snapshot_accepted` to be reached with empty evidence. Extend the frozen evidence contract and enforce step-specific affirmative gates:
   - `structurally_valid`: structural validation complete;
   - `mapping_reviewed`: critical mapping review complete/clean and identity review complete/clean;
   - `snapshot_accepted`: accepted scope is explicit; if actor is `system_policy`, deterministic/high-confidence mapping evidence is mandatory;
   - `baseline_eligible`: current source coverage plus the prior gates remain affirmative and no critical gaps/ambiguity exist.
   Every blocked attempt must append a decision record without changing the accepted state. Use a semantically correct blocked-decision/error name rather than labeling all pre-baseline failures as baseline eligibility if practical. Add positive and negative tests for every step and actor route.
4. `CanonicalFact` is facts-only now, but it does not bind the stable record identity or the accepted mapping that produced it, and its arbitrary `fact_id` remains outside a deterministic identity contract. Add required `record_identity_digest`, `identity_algorithm_digest`, and `mapping_result_id` (or equivalently explicit immutable fields that bind all three). Derive or validate a deterministic public fact ID from project/source/snapshot/type/record/mapping/location/payload. Add cross-project, missing-provenance, repeat-construction and mismatch regressions.
5. While touching adjacent validation, ensure `MappingDefinition.version` is required. `RuleActivation` represents an approved activation, so record a required `activated_by` and validate its frozen scope/version/source/knowledge-pack bindings; do not implement R3 natural-language parsing.

Keep compatibility changes explicit in package exports/README so worker_02 consumes the corrected interfaces. Do not implement Batch B/C.

Run focused tests for all five items, the entire Batch A suite and all current R2 tests. Return exact changed paths, test counts, before/after evidence, interface changes and residual limitations. Do not claim Batch A acceptance; Codex owns the gate.
