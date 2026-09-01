You are continuing the SAME Pi execution session for `medical_monitoring_r4_aemh_slice_20260810`, role `worker_02`, requested effort `high`. This is the final narrow recovery pass for worker_02. Codex has independently reviewed the current round-2 source and rejects only the precise residual contract gaps below. Do not reopen broad design or change scope.

Runner-managed report path: `runs/execution/medical_monitoring_r4_aemh_slice_20260810/worker_02_round3.md`.
Never write or edit that report path through tools. Return the complete seven-heading execution report in your final response; the runner persists it.

## Hard boundaries

- Modify only worker_02-owned R4 files: `src/mm_r4/aemh.py`, `src/mm_r4/projection.py`, `tests/test_aemh_slice.py`.
- Use the current worker_01 common contract as-is. Do not edit R1-R3, worker_01 files, product/runtime, medical writing, or real projects.
- No lifecycle establish/close/transition. No service start, dependency installation, security work, or network/provider calls beyond this already-running session. Port 8911 stays stopped.
- Runtime modules must not mutate `sys.path`.

## Residual findings that must be corrected exactly

1. **Partial date across the protocol boundary must have one outcome.** The current `test_partial_date_crossing_boundary` accepts `BOUNDARY` or `POSITIVE`, and the implementation loses `boundary_cls.classification == "boundary"` when no reported AE/MH matches. Preserve that boundary classification through disposition determination. The exact test must assert only `L1Disposition.BOUNDARY`, retain the supporting source locator and uncertainty, and prove the result validates through `to_unit_evaluation`. Do not turn a partially dated event into a clean positive. A boundary candidate/query may remain if all common-contract joins are valid, but its unit disposition must be `boundary`.

2. **Replace permissive NCS tests with medical-semantic proofs.** Add exact tests showing: (a) isolated explicit NCS, with no symptom, action/treatment, seriousness, high priority or repeat worsening, yields `NEGATIVE`, no candidate and source-linked counterevidence; (b) NCS plus a medical action (or a separate associated symptom/seriousness clue) with no matching reported AE/MH remains an exact `POSITIVE` clue and creates the one candidate; (c) a source-linked confirmed alternative diagnosis, with no reported match that could mask this branch, yields exact `NEGATIVE`, no candidate and counterevidence. Do not use multi-outcome assertions or mere no-crash assertions. Represent confirmation explicitly, e.g. an immutable boolean `alternative_diagnosis_confirmed`; a non-empty tentative diagnosis alone must not suppress a clue. Validate its type.

3. **Do not silently coerce AI provenance.** `SemanticRecord.ai_assertion` currently uses `bool(value)`, so the string `"false"` becomes true. Require an actual boolean and add a rejection test.

4. **Role availability must be internally coherent.** Validate `available_roles` and `empty_covered_roles` as recognized D01 semantic roles; reject overlap; require every role actually present in `records` to appear in `available_roles`. Keep explicit empty-but-covered required roles valid. Add direct tests for all three invariants.

5. **Query text must have exactly one three-part prefix.** `_query_basis_text` currently returns text beginning `依据：`, and `project_query_drafts` prefixes `依据：` again. Make `query_to_text` render exactly one `依据：`, one `发现：`, and one `行动项：`; add exact prefix-count assertions while retaining the boundary/strategy IDs and minimal source-locator joins.

6. **Every Patient Journey event must be bound to the EvaluationUnit.** Add exact `unit_id` to each raw journey marker and `JourneyEvent`, validate it is non-empty and equals the source `AEMHUnitResult.unit_id`, include it in canonical payloads, and test every projected event. Preserve distinct AE/MH/CM/IP/symptom/exam categories and locator-scoped risk markers.

7. Remove or replace any remaining `assert ... in (NEGATIVE, BOUNDARY, POSITIVE)` or similar permissive clinical outcome assertions in worker_02 tests. Each scenario must assert the single intended result.

Run the full isolated R4 test suite, focused R2 risk/identity tests, focused R3 normalization/date tests, Ruff on the worker_02 files, compile/import checks, frozen R2/R3 file digests, and port 8911 check. Do not claim acceptance yourself. In the report state exact test counts, changed file hashes, no out-of-scope writes, and any genuine residual uncertainty. Codex remains final authority.
