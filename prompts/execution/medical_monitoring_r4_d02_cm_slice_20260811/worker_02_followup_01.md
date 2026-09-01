You are continuing the same `worker_02` execution session for task `medical_monitoring_r4_d02_cm_slice_20260811`. Codex reviewed the current `cm.py` and tests against the frozen D02 v1.1 contract. The first pass is not accepted despite green tests. Repair all contract gaps below in one bounded pass.

## Hard boundaries

- Work only inside the runner-provided current workspace root (`.`).
- Modify only `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py` and `poc/medical_monitoring_ai_native_r4/tests/test_cm_slice.py`.
- Shared R4 files, R1/R2/R3, product, frontend/backend, medical-writing, real projects, services, providers, dictionaries, port 8911, task records, prompts, runs, logs, reviews, plans, context, and metrics are read-only or out of scope.
- Runner-managed output file: `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_02_round2.md`. Return the complete report in your final response; do not write the report path with tools.

## Read these source files

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`
- `context/medical_monitoring_r4_d02_cm_slice_20260811_execution_context.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_slice.py`
- Shared R4 contracts/lifecycle may be read but not modified.

## Required corrections

1. **Implement a real `not_applicable` result.** A rule unit whose current explicitly known study phase is outside that rule's `applicable_phases` must be `not_applicable`, with no candidate/Query. A missing or unconfirmed phase remains `not_evaluable`; zero rows/file missing must never become not-applicable. Replace the current test that only proves the engine never emits this fifth disposition with positive executable coverage of both paths.

2. **Definitive identity non-match.** A confirmed ingredient-exact binding that differs from an ingredient-exact rule target is a deterministic `negative` when the identity binding is complete; it does not need an outside time window. Category/product-type absence must remain fail-closed unless the binding explicitly proves that classification dimension complete. Do not turn a mere different superclass or missing membership into negative. Repair the weak test that currently accepts not-evaluable for a confirmed exact non-match.

3. **Indication linkage must fail closed on coverage and role.** `evidence_records=()` cannot by itself prove a complete search with no matching AE/MH/diagnosis. Add an explicit accepted linkage-coverage input to `evaluate_cm_unit`/`evaluate_cm_slice` (a compact boolean or equivalent immutable proof is acceptable) whose default is incomplete/fail-closed. A positive or definitive negative indication conclusion requires complete relevant-source coverage. Missing/unconfirmed treatment role is `not_evaluable`, not boundary and not positive. Prophylaxis/rescue can be negative only when the role is confirmed.

4. **Subject and temporal ownership.** `_assess_indication` must never use another participant's record as counterevidence. Filter by exact `subject_ref`; use relevant event time when supplied, and fail closed when a same-concept record cannot be temporally interpreted rather than silently treating it as matching. Add tests for cross-subject same concept and temporally unrelated records.

5. **Implement both indication positive subtypes.** `treatment_without_event_record` requires explicit evidence that the purpose is treatment of a study-period new/worsened event plus complete linkage coverage. Other confirmed, mappable, role-confirmed but unexplained indications use `medication_indication_unexplained`. Add the smallest explicit episode field/token needed to distinguish these cases; do not infer new/worsened from the word `treatment` alone. Keep subtype 2 precedence only when its stronger facts are present.

6. **No hard-coded non-rule medium.** When no versioned `D02PriorityPolicy` is supplied, a non-rule positive/boundary may use `unknown`; it must not silently default to `medium`. Not-evaluable remains a coverage gap and must never be presented as an unknown risk.

7. **Restricted-condition tri-state.** Missing role or missing stable-treatment evidence is `not_evaluable`; a confirmed unmet allowed condition is positive; a confirmed met condition is negative. Stable treatment can be accepted only when duration/stability and dose/frequency-unchanged evidence are explicitly confirmed, not merely because `treatment_role_confirmed=True`. Rescue/prophylaxis requires confirmed role. Unknown allowed-condition tokens fail closed instead of being ignored. Add deterministic tests for missing, confirmed-met, and confirmed-unmet cases.

8. **Query provenance.** Every generated Query must include the CM source locator and medication-identity evidence locator in `source_locator_ids`; include the indication locator when distinct. Rule id/clause locator must remain instantiated in the Chinese text. Deduplicate deterministically. Strengthen tests from `len >= 1` to exact required provenance membership.

9. **Episode L2 source count.** `CMEpisodeRollup.source_record_count` must count unique CM source records, not sum the same row once per child unit. Add a compound/multi-rule test proving one CM row counts once while child unit IDs and simultaneous flags remain intact.

10. **User language.** Replace `未知风险族` and any similar user-facing/internal wording. An unreachable evaluator branch should say a native Chinese coverage-gap phrase such as `未识别的用药核查类型，当前无法评价`; add a scan/assertion forbidding `正式事实`, `候选信号`, `只读xx`, and `未知风险` in user-visible result strings.

Keep the engine standard-library only and do not broaden into projection/fixtures/root exports. Run and report:

1. `python3 -m pytest -q -p no:cacheprovider tests/test_cm_slice.py`
2. `python3 -m pytest -q -p no:cacheprovider tests`
3. `python3 -m ruff check src/mm_r4/cm.py tests/test_cm_slice.py`
4. compile/import checks and no-listener check for 8911.

Return exact artifacts, commands, results, residual uncertainty, and the next step. Do not claim acceptance; Codex owns Gate 2 acceptance.
