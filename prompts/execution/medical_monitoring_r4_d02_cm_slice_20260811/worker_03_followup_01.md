You are continuing the same `worker_03` execution session for task `medical_monitoring_r4_d02_cm_slice_20260811`. Codex independently reviewed the first projection pass. Gate 3 is not accepted. Repair only the listed projection defects.

## Hard boundaries

- Work only inside the runner-provided current workspace root (`.`).
- Modify only `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_projection.py` and `poc/medical_monitoring_ai_native_r4/tests/test_cm_projection.py`.
- Shared R4 files, `cm.py`, R1/R2/R3, root exports, product/frontend/backend, medical-writing, real projects, services, providers, dictionaries, port 8911, task records, prompts, runs, logs, reviews, plans, context, and metrics are read-only or out of scope.
- Runner-managed output file: `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_03_round2.md`. Return the complete report in the final response; do not write that file with tools.

## Read these source files

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`
- `context/medical_monitoring_r4_d02_cm_slice_20260811_execution_context.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_projection.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_projection.py`

## Required corrections

1. **Compute the real rule-overlap anchor.** For prohibited/restricted markers with a supplied rule, `anchor_start` and `anchor_end` must be the actual intersection of the CM interval and the rule window when full-day endpoints are deterministically comparable. Do not merely label the full CM interval as `interval_rule_overlap`. For partial/ambiguous endpoints, preserve a fail-closed non-fabricated anchor consistent with the engine disposition. Add a test where CM is wider than the rule window and assert exact intersection coordinates.
2. **Guarantee medication-identity drill-back.** Whenever `episode` is available, every emitted marker must include both the CM source locator and `episode.identity_binding.evidence_locator` in `source_locator_ids`; include the distinct indication locator when present. Add exact-membership tests for prohibited and indication markers, not only identity fields.
3. **Make the bidirectional join truly episode + unit bound.** A marker may link only to an event with the same `episode_id` **and** whose `unit_ids` contains the marker `unit_id`. Add an adversarial test: same episode id but mismatched unit id must not join in either direction. Reject or leave unlinked; never connect by episode alone.
4. **Never return an internal risk-family code as an audience label.** Unknown or missing family must fall back to natural Chinese such as `用药信息待核实`, not `risk_family`. Add a test with an unknown synthetic family and scan audience labels for internal/backend terms already prohibited by the product contract.
5. **Make Ruff clean.** Remove the six unused imports reported by `python3 -m ruff check src/mm_r4/cm_projection.py tests/test_cm_projection.py`. Do not use blanket noqa or disable rules.
6. Preserve all accepted projection contracts: exact minimum payloads, typed Chinese labels, CM track, no fake AE/MH event, simultaneous positive/boundary/not_evaluable markers, stable ids, view-only rollups, source/rule/Query/cross-domain joins, deterministic serialization.

Run focused projection tests, CM engine tests, full R4, Ruff via `python3 -m ruff`, compile/import, adjacent R2/R3, shared hash checks, and port 8911 no-listener check. Return exact counts, hashes, scope confirmation, and residual uncertainty. Do not claim Gate 3 acceptance; Codex owns acceptance.
